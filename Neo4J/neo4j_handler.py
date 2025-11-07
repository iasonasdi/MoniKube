#!/usr/bin/env python3
"""
Neo4J Database Handler for MoniKube
Handles storage of Kubernetes monitoring data in Neo4J graph database.
"""

import json
import socket
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
import logging

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError, TransientError
except ImportError:
    print("Neo4J driver not installed. Install with: pip install neo4j")
    GraphDatabase = None

from DataCollection.kubernetes_monitor import (
    KubernetesMonitor, 
    ContainerInfo, 
    PodInfo, 
    ServiceInfo, 
    NodeInfo, 
    ClusterMetrics
)


class Neo4JHandler:
    """
    Neo4J database handler for storing Kubernetes monitoring data.
    Creates a comprehensive graph representation of cluster infrastructure.
    """
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """
        Initialize Neo4J connection.
        
        Args:
            uri: Neo4J database URI (e.g., "bolt://localhost:7687")
            username: Database username
            password: Database password
            database: Database name (default: "neo4j")
        """
        if GraphDatabase is None:
            raise ImportError("Neo4J driver not available. Install with: pip install neo4j")
        
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        self.logger = self._setup_logging()
        self.vm_identifier = self._get_vm_identifier()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _get_vm_identifier(self) -> Dict[str, Any]:
        """Get VM identifier information"""
        try:
            # Get hostname
            hostname = socket.gethostname()
            
            # Get IP addresses
            ip_addresses = []
            try:
                # Get primary IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                primary_ip = s.getsockname()[0]
                s.close()
                ip_addresses.append(primary_ip)
            except:
                pass
            
            # Get all IP addresses
            try:
                import netifaces
                for interface in netifaces.interfaces():
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            ip = addr['addr']
                            if ip not in ip_addresses and not ip.startswith('127.'):
                                ip_addresses.append(ip)
            except ImportError:
                pass
            
            return {
                'hostname': hostname,
                'ip_addresses': ip_addresses,
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Could not get VM identifier: {e}")
            return {
                'hostname': 'unknown',
                'ip_addresses': [],
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'timestamp': datetime.now().isoformat()
            }
    
    def connect(self) -> bool:
        """Connect to Neo4J database"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password),
                database=self.database
            )
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            self.logger.info(f"Successfully connected to Neo4J at {self.uri}")
            return True
            
        except ServiceUnavailable as e:
            self.logger.error(f"Neo4J service unavailable: {e}")
            return False
        except AuthError as e:
            self.logger.error(f"Neo4J authentication failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4J: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Neo4J database"""
        if self.driver:
            self.driver.close()
            self.logger.info("Disconnected from Neo4J")
    
    def create_schema(self):
        """Create Neo4J schema for Kubernetes monitoring data"""
        schema_queries = [
            # Create indexes for performance
            "CREATE INDEX vm_id_index IF NOT EXISTS FOR (v:VM) ON (v.id)",
            "CREATE INDEX cluster_id_index IF NOT EXISTS FOR (c:Cluster) ON (c.id)",
            "CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Node) ON (n.id)",
            "CREATE INDEX pod_id_index IF NOT EXISTS FOR (p:Pod) ON (p.id)",
            "CREATE INDEX service_id_index IF NOT EXISTS FOR (s:Service) ON (s.id)",
            "CREATE INDEX container_id_index IF NOT EXISTS FOR (ct:Container) ON (ct.id)",
            "CREATE INDEX resource_usage_cluster_index IF NOT EXISTS FOR (ru:ResourceUsage) ON (ru.cluster_id)",
            
            # Create constraints for uniqueness
            "CREATE CONSTRAINT vm_id_unique IF NOT EXISTS FOR (v:VM) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (c:Cluster) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:Node) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT pod_id_unique IF NOT EXISTS FOR (p:Pod) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT service_id_unique IF NOT EXISTS FOR (s:Service) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT container_id_unique IF NOT EXISTS FOR (ct:Container) REQUIRE ct.id IS UNIQUE",
            "CREATE CONSTRAINT resource_usage_cluster_unique IF NOT EXISTS FOR (ru:ResourceUsage) REQUIRE ru.cluster_id IS UNIQUE"
        ]
        
        try:
            with self.driver.session() as session:
                for query in schema_queries:
                    session.run(query)
            self.logger.info("Neo4J schema created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create schema: {e}")
    
    def store_monitoring_data(self, monitor: KubernetesMonitor, context: str = "default") -> bool:
        """
        Store comprehensive monitoring data in Neo4J.
        
        Args:
            monitor: KubernetesMonitor instance
            context: Kubernetes context name
            
        Returns:
            bool: Success status
        """
        try:
            # Get resource usage data (if metrics-server is available)
            resource_usage = monitor.get_resource_usage()
            
            # Parse metrics for usage data
            node_metrics_dict = self._parse_node_metrics(resource_usage.get('node_metrics', {}))
            pod_metrics_dict = self._parse_pod_metrics(resource_usage.get('pod_metrics', {}))
            
            # Get available contexts
            available_contexts = monitor.get_available_contexts()
            
            with self.driver.session() as session:
                # Start transaction
                with session.begin_transaction() as tx:
                    # Store VM information
                    vm_id = self._store_vm_info(tx)
                    
                    # Store cluster information (including available contexts)
                    cluster_id = self._store_cluster_info(tx, monitor, context, vm_id, available_contexts)
                    
                    # Store nodes (with actual usage data if available)
                    node_ids = self._store_nodes(tx, monitor, cluster_id, node_metrics_dict)
                    
                    # Store pods
                    pod_ids = self._store_pods(tx, monitor, cluster_id, node_ids)
                    
                    # Store services
                    service_ids = self._store_services(tx, monitor, cluster_id)
                    
                    # Store containers (with actual usage data if available)
                    self._store_containers(tx, monitor, pod_ids, pod_metrics_dict)
                    
                    # Store cluster metrics
                    self._store_cluster_metrics(tx, monitor, cluster_id)
                    
                    # Store resource usage data
                    self._store_resource_usage(tx, monitor, cluster_id, resource_usage)
                    
                    # Create relationships
                    self._create_relationships(tx, monitor, cluster_id, node_ids, pod_ids, service_ids)
                    
                    self.logger.info(f"Successfully stored monitoring data for context: {context}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to store monitoring data: {e}")
            return False
    
    def _store_vm_info(self, tx) -> str:
        """Store VM information and return VM ID"""
        vm_id = f"vm_{self.vm_identifier['hostname']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        query = """
        MERGE (v:VM {id: $vm_id})
        SET v.hostname = $hostname,
            v.ip_addresses = $ip_addresses,
            v.platform = $platform,
            v.python_version = $python_version,
            v.timestamp = $timestamp,
            v.last_updated = datetime()
        RETURN v.id as vm_id
        """
        
        result = tx.run(query, 
                       vm_id=vm_id,
                       hostname=self.vm_identifier['hostname'],
                       ip_addresses=self.vm_identifier['ip_addresses'],
                       platform=self.vm_identifier['platform'],
                       python_version=self.vm_identifier['python_version'],
                       timestamp=self.vm_identifier['timestamp'])
        
        return result.single()['vm_id']
    
    def _parse_node_metrics(self, node_metrics: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Parse node metrics from kubectl top nodes output"""
        metrics_dict = {}
        try:
            if isinstance(node_metrics, dict) and 'items' in node_metrics:
                for item in node_metrics.get('items', []):
                    metadata = item.get('metadata', {})
                    name = metadata.get('name', '')
                    usage = item.get('usage', {})
                    
                    # Parse CPU (convert to float percentage)
                    cpu_str = usage.get('cpu', '0')
                    cpu_value = self._parse_cpu_to_float(cpu_str)
                    
                    # Parse Memory (convert to float in MiB)
                    memory_str = usage.get('memory', '0')
                    memory_value = self._parse_memory_to_mib(memory_str)
                    
                    metrics_dict[name] = {
                        'cpu_usage': cpu_value,
                        'memory_usage': memory_value
                    }
        except Exception as e:
            self.logger.warning(f"Failed to parse node metrics: {e}")
        return metrics_dict
    
    def _parse_pod_metrics(self, pod_metrics: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Parse pod metrics from kubectl top pods output"""
        metrics_dict = {}
        try:
            if isinstance(pod_metrics, dict) and 'items' in pod_metrics:
                for item in pod_metrics.get('items', []):
                    metadata = item.get('metadata', {})
                    namespace = metadata.get('namespace', '')
                    name = metadata.get('name', '')
                    pod_key = f"{namespace}/{name}"
                    
                    containers = item.get('containers', [])
                    container_metrics = {}
                    
                    for container in containers:
                        container_name = container.get('name', '')
                        usage = container.get('usage', {})
                        
                        # Parse CPU (convert to float percentage)
                        cpu_str = usage.get('cpu', '0')
                        cpu_value = self._parse_cpu_to_float(cpu_str)
                        
                        # Parse Memory (convert to float in MiB)
                        memory_str = usage.get('memory', '0')
                        memory_value = self._parse_memory_to_mib(memory_str)
                        
                        container_metrics[container_name] = {
                            'cpu_usage': cpu_value,
                            'memory_usage': memory_value
                        }
                    
                    metrics_dict[pod_key] = container_metrics
        except Exception as e:
            self.logger.warning(f"Failed to parse pod metrics: {e}")
        return metrics_dict
    
    def _parse_cpu_to_float(self, cpu_str: str) -> float:
        """Parse CPU string to float (millicores or cores)"""
        if not cpu_str or cpu_str == '0':
            return 0.0
        
        try:
            cpu_str = cpu_str.strip()
            if cpu_str.endswith('m'):
                # Millicores
                return float(cpu_str[:-1]) / 1000.0
            elif cpu_str.endswith('n'):
                # Nanocores
                return float(cpu_str[:-1]) / 1000000000.0
            else:
                # Cores
                return float(cpu_str)
        except:
            return 0.0
    
    def _parse_memory_to_mib(self, memory_str: str) -> float:
        """Parse memory string to float (MiB)"""
        if not memory_str or memory_str == '0':
            return 0.0
        
        try:
            memory_str = memory_str.strip().upper()
            
            # Handle different units
            if memory_str.endswith('KI'):
                return float(memory_str[:-2]) / 1024.0
            elif memory_str.endswith('MI'):
                return float(memory_str[:-2])
            elif memory_str.endswith('GI'):
                return float(memory_str[:-2]) * 1024.0
            elif memory_str.endswith('TI'):
                return float(memory_str[:-2]) * 1024.0 * 1024.0
            elif memory_str.endswith('K'):
                return float(memory_str[:-1]) / 1024.0
            elif memory_str.endswith('M'):
                return float(memory_str[:-1])
            elif memory_str.endswith('G'):
                return float(memory_str[:-1]) * 1024.0
            elif memory_str.endswith('T'):
                return float(memory_str[:-1]) * 1024.0 * 1024.0
            else:
                # Assume bytes
                return float(memory_str) / (1024.0 * 1024.0)
        except:
            return 0.0
    
    def _store_cluster_info(self, tx, monitor: KubernetesMonitor, context: str, vm_id: str, available_contexts: List[str]) -> str:
        """Store cluster information and return cluster ID"""
        cluster_id = f"cluster_{context}_{vm_id}"
        
        # Get cluster info
        cluster_info = monitor.get_cluster_info()
        
        query = """
        MERGE (c:Cluster {id: $cluster_id})
        SET c.context = $context,
            c.vm_id = $vm_id,
            c.cluster_info = $cluster_info,
            c.available_contexts = $available_contexts,
            c.timestamp = datetime(),
            c.last_updated = datetime()
        RETURN c.id as cluster_id
        """
        
        result = tx.run(query,
                       cluster_id=cluster_id,
                       context=context,
                       vm_id=vm_id,
                       cluster_info=json.dumps(cluster_info),
                       available_contexts=available_contexts)
        
        return result.single()['cluster_id']
    
    def _store_nodes(self, tx, monitor: KubernetesMonitor, cluster_id: str, node_metrics_dict: Dict[str, Dict[str, Any]] = None) -> List[str]:
        """Store node information and return list of node IDs"""
        nodes = monitor.get_nodes()
        node_ids = []
        node_metrics_dict = node_metrics_dict or {}
        
        for node in nodes:
            node_id = f"node_{node.name}_{cluster_id}"
            node_ids.append(node_id)
            
            # Get actual usage from metrics if available
            node_metrics = node_metrics_dict.get(node.name, {})
            cpu_usage = node_metrics.get('cpu_usage', node.cpu_usage)
            memory_usage = node_metrics.get('memory_usage', node.memory_usage)
            
            query = """
            MERGE (n:Node {id: $node_id})
            SET n.name = $name,
                n.status = $status,
                n.roles = $roles,
                n.cpu_capacity = $cpu_capacity,
                n.memory_capacity = $memory_capacity,
                n.cpu_allocatable = $cpu_allocatable,
                n.memory_allocatable = $memory_allocatable,
                n.cpu_usage = $cpu_usage,
                n.memory_usage = $memory_usage,
                n.cluster_id = $cluster_id,
                n.timestamp = datetime(),
                n.last_updated = datetime()
            RETURN n.id as node_id
            """
            
            tx.run(query,
                   node_id=node_id,
                   name=node.name,
                   status=node.status,
                   roles=node.roles,
                   cpu_capacity=node.cpu_capacity,
                   memory_capacity=node.memory_capacity,
                   cpu_allocatable=node.cpu_allocatable,
                   memory_allocatable=node.memory_allocatable,
                   cpu_usage=cpu_usage,
                   memory_usage=memory_usage,
                   cluster_id=cluster_id)
        
        return node_ids
    
    def _store_pods(self, tx, monitor: KubernetesMonitor, cluster_id: str, node_ids: List[str]) -> List[str]:
        """Store pod information and return list of pod IDs"""
        pods = monitor.get_pods()
        pod_ids = []
        
        for pod in pods:
            pod_id = f"pod_{pod.name}_{pod.namespace}_{cluster_id}"
            pod_ids.append(pod_id)
            
            query = """
            MERGE (p:Pod {id: $pod_id})
            SET p.name = $name,
                p.namespace = $namespace,
                p.status = $status,
                p.node = $node,
                p.cpu_requests = $cpu_requests,
                p.memory_requests = $memory_requests,
                p.cpu_limits = $cpu_limits,
                p.memory_limits = $memory_limits,
                p.cluster_id = $cluster_id,
                p.timestamp = datetime(),
                p.last_updated = datetime()
            RETURN p.id as pod_id
            """
            
            tx.run(query,
                   pod_id=pod_id,
                   name=pod.name,
                   namespace=pod.namespace,
                   status=pod.status,
                   node=pod.node,
                   cpu_requests=pod.cpu_requests,
                   memory_requests=pod.memory_requests,
                   cpu_limits=pod.cpu_limits,
                   memory_limits=pod.memory_limits,
                   cluster_id=cluster_id)
        
        return pod_ids
    
    def _store_services(self, tx, monitor: KubernetesMonitor, cluster_id: str) -> List[str]:
        """Store service information and return list of service IDs"""
        services = monitor.get_services()
        service_ids = []
        
        for service in services:
            service_id = f"service_{service.name}_{service.namespace}_{cluster_id}"
            service_ids.append(service_id)
            
            query = """
            MERGE (s:Service {id: $service_id})
            SET s.name = $name,
                s.namespace = $namespace,
                s.type = $type,
                s.cluster_ip = $cluster_ip,
                s.external_ip = $external_ip,
                s.ports = $ports,
                s.selector = $selector,
                s.cluster_id = $cluster_id,
                s.timestamp = datetime(),
                s.last_updated = datetime()
            RETURN s.id as service_id
            """
            
            tx.run(query,
                   service_id=service_id,
                   name=service.name,
                   namespace=service.namespace,
                   type=service.type,
                   cluster_ip=service.cluster_ip,
                   external_ip=service.external_ip,
                   ports=json.dumps(service.ports),
                   selector=json.dumps(service.selector),
                   cluster_id=cluster_id)
        
        return service_ids
    
    def _store_containers(self, tx, monitor: KubernetesMonitor, pod_ids: List[str], pod_metrics_dict: Dict[str, Dict[str, Any]] = None):
        """Store container information"""
        pods = monitor.get_pods()
        pod_metrics_dict = pod_metrics_dict or {}
        
        for i, pod in enumerate(pods):
            pod_id = pod_ids[i] if i < len(pod_ids) else f"pod_{pod.name}_{pod.namespace}"
            pod_key = f"{pod.namespace}/{pod.name}"
            container_metrics = pod_metrics_dict.get(pod_key, {})
            
            for container in pod.containers:
                container_id = f"container_{container.name}_{pod_id}"
                
                # Get actual usage from metrics if available
                container_metric = container_metrics.get(container.name, {})
                cpu_usage = container_metric.get('cpu_usage', container.cpu_usage)
                memory_usage = container_metric.get('memory_usage', container.memory_usage)
                
                query = """
                MERGE (ct:Container {id: $container_id})
                SET ct.name = $name,
                    ct.image = $image,
                    ct.status = $status,
                    ct.cpu_usage = $cpu_usage,
                    ct.memory_usage = $memory_usage,
                    ct.memory_limit = $memory_limit,
                    ct.cpu_limit = $cpu_limit,
                    ct.pod_id = $pod_id,
                    ct.timestamp = datetime(),
                    ct.last_updated = datetime()
                RETURN ct.id as container_id
                """
                
                tx.run(query,
                       container_id=container_id,
                       name=container.name,
                       image=container.image,
                       status=container.status,
                       cpu_usage=cpu_usage,
                       memory_usage=memory_usage,
                       memory_limit=container.memory_limit,
                       cpu_limit=container.cpu_limit,
                       pod_id=pod_id)
    
    def _store_cluster_metrics(self, tx, monitor: KubernetesMonitor, cluster_id: str):
        """Store cluster metrics"""
        metrics = monitor.get_cluster_metrics()
        
        query = """
        MERGE (cm:ClusterMetrics {cluster_id: $cluster_id})
        SET cm.total_pods = $total_pods,
            cm.running_pods = $running_pods,
            cm.pending_pods = $pending_pods,
            cm.failed_pods = $failed_pods,
            cm.total_services = $total_services,
            cm.total_nodes = $total_nodes,
            cm.ready_nodes = $ready_nodes,
            cm.total_cpu_usage = $total_cpu_usage,
            cm.total_memory_usage = $total_memory_usage,
            cm.timestamp = datetime(),
            cm.last_updated = datetime()
        RETURN cm.cluster_id as cluster_id
        """
        
        tx.run(query,
               cluster_id=cluster_id,
               total_pods=metrics.total_pods,
               running_pods=metrics.running_pods,
               pending_pods=metrics.pending_pods,
               failed_pods=metrics.failed_pods,
               total_services=metrics.total_services,
               total_nodes=metrics.total_nodes,
               ready_nodes=metrics.ready_nodes,
               total_cpu_usage=metrics.total_cpu_usage,
               total_memory_usage=metrics.total_memory_usage)
    
    def _store_resource_usage(self, tx, monitor: KubernetesMonitor, cluster_id: str, resource_usage: Dict[str, Any]):
        """Store resource usage data from metrics-server"""
        if not resource_usage:
            return
        
        query = """
        MERGE (ru:ResourceUsage {cluster_id: $cluster_id})
        SET ru.pod_metrics = $pod_metrics,
            ru.node_metrics = $node_metrics,
            ru.timestamp = $timestamp,
            ru.last_updated = datetime()
        RETURN ru.cluster_id as cluster_id
        """
        
        timestamp = resource_usage.get('timestamp', datetime.now().isoformat())
        pod_metrics = json.dumps(resource_usage.get('pod_metrics', {}))
        node_metrics = json.dumps(resource_usage.get('node_metrics', {}))
        
        tx.run(query,
               cluster_id=cluster_id,
               pod_metrics=pod_metrics,
               node_metrics=node_metrics,
               timestamp=timestamp)
    
    def _create_relationships(self, tx, monitor: KubernetesMonitor, cluster_id: str, node_ids: List[str], 
                           pod_ids: List[str], service_ids: List[str]):
        """Create relationships between entities"""
        
        # VM -> Cluster relationship
        tx.run("""
        MATCH (v:VM), (c:Cluster {id: $cluster_id})
        WHERE v.id = c.vm_id
        MERGE (v)-[:HOSTS]->(c)
        """, cluster_id=cluster_id)
        
        # Cluster -> Nodes relationships
        for node_id in node_ids:
            tx.run("""
            MATCH (c:Cluster {id: $cluster_id}), (n:Node {id: $node_id})
            MERGE (c)-[:CONTAINS]->(n)
            """, cluster_id=cluster_id, node_id=node_id)
        
        # Cluster -> Pods relationships
        for pod_id in pod_ids:
            tx.run("""
            MATCH (c:Cluster {id: $cluster_id}), (p:Pod {id: $pod_id})
            MERGE (c)-[:CONTAINS]->(p)
            """, cluster_id=cluster_id, pod_id=pod_id)
        
        # Cluster -> Services relationships
        for service_id in service_ids:
            tx.run("""
            MATCH (c:Cluster {id: $cluster_id}), (s:Service {id: $service_id})
            MERGE (c)-[:CONTAINS]->(s)
            """, cluster_id=cluster_id, service_id=service_id)
        
        # Cluster -> ResourceUsage relationship
        tx.run("""
        MATCH (c:Cluster {id: $cluster_id}), (ru:ResourceUsage {cluster_id: $cluster_id})
        MERGE (c)-[:HAS_RESOURCE_USAGE]->(ru)
        """, cluster_id=cluster_id)
        
        # Node -> Pods relationships (based on pod.node field)
        pods = monitor.get_pods()
        for i, pod in enumerate(pods):
            if i < len(pod_ids):
                pod_id = pod_ids[i]
                # Find the node that hosts this pod
                for node_id in node_ids:
                    if pod.node in node_id:
                        tx.run("""
                        MATCH (n:Node {id: $node_id}), (p:Pod {id: $pod_id})
                        MERGE (n)-[:HOSTS]->(p)
                        """, node_id=node_id, pod_id=pod_id)
        
        # Pod -> Container relationships
        for i, pod in enumerate(pods):
            if i < len(pod_ids):
                pod_id = pod_ids[i]
                for container in pod.containers:
                    container_id = f"container_{container.name}_{pod_id}"
                    tx.run("""
                    MATCH (p:Pod {id: $pod_id}), (ct:Container {id: $container_id})
                    MERGE (p)-[:CONTAINS]->(ct)
                    """, pod_id=pod_id, container_id=container_id)
    
    def query_data(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a custom Cypher query"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            return []
    
    def get_vm_summary(self) -> Dict[str, Any]:
        """Get summary of all VMs in the database"""
        query = """
        MATCH (v:VM)
        RETURN v.id as vm_id, v.hostname, v.ip_addresses, v.platform, v.timestamp
        ORDER BY v.timestamp DESC
        """
        return self.query_data(query)
    
    def get_cluster_summary(self, vm_id: str = None) -> Dict[str, Any]:
        """Get summary of clusters for a specific VM or all VMs"""
        if vm_id:
            query = """
            MATCH (v:VM {id: $vm_id})-[:HOSTS]->(c:Cluster)
            RETURN c.id as cluster_id, c.context, c.timestamp
            ORDER BY c.timestamp DESC
            """
            return self.query_data(query, {'vm_id': vm_id})
        else:
            query = """
            MATCH (c:Cluster)
            RETURN c.id as cluster_id, c.context, c.vm_id, c.timestamp
            ORDER BY c.timestamp DESC
            """
            return self.query_data(query)
    
    def get_infrastructure_graph(self, vm_id: str = None) -> Dict[str, Any]:
        """Get complete infrastructure graph for visualization"""
        if vm_id:
            query = """
            MATCH (v:VM {id: $vm_id})-[:HOSTS]->(c:Cluster)
            OPTIONAL MATCH (c)-[:CONTAINS]->(n:Node)
            OPTIONAL MATCH (c)-[:CONTAINS]->(p:Pod)
            OPTIONAL MATCH (c)-[:CONTAINS]->(s:Service)
            OPTIONAL MATCH (n)-[:HOSTS]->(p)
            OPTIONAL MATCH (p)-[:CONTAINS]->(ct:Container)
            RETURN v, c, n, p, s, ct
            """
            return self.query_data(query, {'vm_id': vm_id})
        else:
            query = """
            MATCH (v:VM)-[:HOSTS]->(c:Cluster)
            OPTIONAL MATCH (c)-[:CONTAINS]->(n:Node)
            OPTIONAL MATCH (c)-[:CONTAINS]->(p:Pod)
            OPTIONAL MATCH (c)-[:CONTAINS]->(s:Service)
            OPTIONAL MATCH (n)-[:HOSTS]->(p)
            OPTIONAL MATCH (p)-[:CONTAINS]->(ct:Container)
            RETURN v, c, n, p, s, ct
            """
            return self.query_data(query)
    
    def cleanup_old_data(self, days: int = 7):
        """Clean up data older than specified days"""
        query = """
        MATCH (n)
        WHERE n.timestamp < datetime() - duration({days: $days})
        DELETE n
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, {'days': days})
                self.logger.info(f"Cleaned up data older than {days} days")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")


def main():
    """Example usage of Neo4JHandler"""
    # Example configuration
    handler = Neo4JHandler(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password",
        database="neo4j"
    )
    
    if handler.connect():
        # Create schema
        handler.create_schema()
        
        # Example: Store monitoring data
        monitor = KubernetesMonitor()
        handler.store_monitoring_data(monitor, "default")
        
        # Example queries
        print("VM Summary:")
        print(handler.get_vm_summary())
        
        print("\nCluster Summary:")
        print(handler.get_cluster_summary())
        
        handler.disconnect()
    else:
        print("Failed to connect to Neo4J")


if __name__ == "__main__":
    main()
