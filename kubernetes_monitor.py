#!/usr/bin/env python3
"""
Kubernetes Cluster Monitor
A comprehensive monitoring solution for Kubernetes clusters, pods, services, and resources.
"""

import subprocess
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml


@dataclass
class ContainerInfo:
    """Container information structure"""
    name: str
    image: str
    status: str
    cpu_usage: float
    memory_usage: float
    memory_limit: Optional[str]
    cpu_limit: Optional[str]


@dataclass
class PodInfo:
    """Pod information structure"""
    name: str
    namespace: str
    status: str
    node: str
    containers: List[ContainerInfo]
    cpu_requests: str
    memory_requests: str
    cpu_limits: str
    memory_limits: str


@dataclass
class ServiceInfo:
    """Service information structure"""
    name: str
    namespace: str
    type: str
    cluster_ip: str
    external_ip: Optional[str]
    ports: List[Dict[str, Any]]
    selector: Dict[str, str]


@dataclass
class NodeInfo:
    """Node information structure"""
    name: str
    status: str
    roles: List[str]
    cpu_capacity: str
    memory_capacity: str
    cpu_allocatable: str
    memory_allocatable: str
    cpu_usage: float
    memory_usage: float


@dataclass
class ClusterMetrics:
    """Cluster metrics structure"""
    total_pods: int
    running_pods: int
    pending_pods: int
    failed_pods: int
    total_services: int
    total_nodes: int
    ready_nodes: int
    total_cpu_usage: float
    total_memory_usage: float


class KubernetesMonitor:
    """
    A comprehensive Kubernetes monitoring class that provides detailed information
    about clusters, pods, services, and resource usage.
    """
    
    def __init__(self, kubeconfig_path: Optional[str] = None, context: Optional[str] = None):
        """
        Initialize the Kubernetes monitor.
        
        Args:
            kubeconfig_path: Path to kubeconfig file (optional)
            context: Kubernetes context to use (optional)
        """
        self.kubeconfig_path = kubeconfig_path
        self.context = context
        self.logger = self._setup_logging()
        self.clusters = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _run_kubectl_command(self, command: List[str], namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute kubectl command and return JSON output.
        
        Args:
            command: kubectl command as list
            namespace: Optional namespace to target
            
        Returns:
            Dictionary containing command output
        """
        try:
            cmd = ['kubectl'] + command
            
            if self.kubeconfig_path:
                cmd.extend(['--kubeconfig', self.kubeconfig_path])
            
            if self.context:
                cmd.extend(['--context', self.context])
            
            if namespace:
                cmd.extend(['-n', namespace])
            
            cmd.append('-o')
            cmd.append('json')
            
            self.logger.debug(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            return json.loads(result.stdout)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Kubectl command failed: {e.stderr}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON output: {e}")
            return {}
        except subprocess.TimeoutExpired:
            self.logger.error("Kubectl command timed out")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {}
    
    def get_available_contexts(self) -> List[str]:
        """Get list of available Kubernetes contexts"""
        try:
            cmd = ['kubectl', 'config', 'get-contexts', '-o', 'name']
            if self.kubeconfig_path:
                cmd.extend(['--kubeconfig', self.kubeconfig_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except Exception as e:
            self.logger.error(f"Failed to get contexts: {e}")
            return []
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get basic cluster information"""
        cluster_info = self._run_kubectl_command(['cluster-info'])
        version_info = self._run_kubectl_command(['version'])
        
        return {
            'cluster_info': cluster_info,
            'version': version_info,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_nodes(self) -> List[NodeInfo]:
        """Get information about all nodes in the cluster"""
        nodes_data = self._run_kubectl_command(['get', 'nodes'])
        nodes = []
        
        if 'items' in nodes_data:
            for node_data in nodes_data['items']:
                node_info = self._parse_node_info(node_data)
                nodes.append(node_info)
        
        return nodes
    
    def _parse_node_info(self, node_data: Dict[str, Any]) -> NodeInfo:
        """Parse node information from kubectl output"""
        metadata = node_data.get('metadata', {})
        status = node_data.get('status', {})
        
        # Get node roles
        roles = []
        labels = metadata.get('labels', {})
        for key, value in labels.items():
            if key.startswith('node-role.kubernetes.io/'):
                roles.append(key.split('/')[-1])
        
        # Get capacity and allocatable resources
        capacity = status.get('capacity', {})
        allocatable = status.get('allocatable', {})
        
        # Calculate usage (this would need metrics server for accurate data)
        cpu_usage = 0.0
        memory_usage = 0.0
        
        return NodeInfo(
            name=metadata.get('name', ''),
            status=self._get_node_status(status),
            roles=roles,
            cpu_capacity=capacity.get('cpu', '0'),
            memory_capacity=capacity.get('memory', '0'),
            cpu_allocatable=allocatable.get('cpu', '0'),
            memory_allocatable=allocatable.get('memory', '0'),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )
    
    def _get_node_status(self, status: Dict[str, Any]) -> str:
        """Extract node status from conditions"""
        conditions = status.get('conditions', [])
        for condition in conditions:
            if condition.get('type') == 'Ready':
                return 'Ready' if condition.get('status') == 'True' else 'NotReady'
        return 'Unknown'
    
    def get_pods(self, namespace: Optional[str] = None) -> List[PodInfo]:
        """Get information about all pods"""
        pods_data = self._run_kubectl_command(['get', 'pods'], namespace)
        pods = []
        
        if 'items' in pods_data:
            for pod_data in pods_data['items']:
                pod_info = self._parse_pod_info(pod_data)
                pods.append(pod_info)
        
        return pods
    
    def _parse_pod_info(self, pod_data: Dict[str, Any]) -> PodInfo:
        """Parse pod information from kubectl output"""
        metadata = pod_data.get('metadata', {})
        spec = pod_data.get('spec', {})
        status = pod_data.get('status', {})
        
        # Parse containers
        containers = []
        container_statuses = status.get('containerStatuses', [])
        
        for container_status in container_statuses:
            container_info = ContainerInfo(
                name=container_status.get('name', ''),
                image=container_status.get('image', ''),
                status=container_status.get('state', {}).get('running', {}).get('startedAt', 'Unknown'),
                cpu_usage=0.0,  # Would need metrics server
                memory_usage=0.0,  # Would need metrics server
                memory_limit=None,
                cpu_limit=None
            )
            containers.append(container_info)
        
        # Get resource requests and limits
        resource_requests = self._get_resource_requests(spec)
        
        return PodInfo(
            name=metadata.get('name', ''),
            namespace=metadata.get('namespace', ''),
            status=status.get('phase', 'Unknown'),
            node=spec.get('nodeName', ''),
            containers=containers,
            cpu_requests=resource_requests.get('cpu', '0'),
            memory_requests=resource_requests.get('memory', '0'),
            cpu_limits=resource_requests.get('cpu_limit', '0'),
            memory_limits=resource_requests.get('memory_limit', '0')
        )
    
    def _get_resource_requests(self, spec: Dict[str, Any]) -> Dict[str, str]:
        """Extract resource requests and limits from pod spec"""
        containers = spec.get('containers', [])
        total_cpu_requests = 0
        total_memory_requests = 0
        total_cpu_limits = 0
        total_memory_limits = 0
        
        for container in containers:
            resources = container.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})
            
            # Parse CPU (convert to millicores for calculation)
            cpu_request = self._parse_cpu_value(requests.get('cpu', '0'))
            cpu_limit = self._parse_cpu_value(limits.get('cpu', '0'))
            
            # Parse Memory (convert to bytes for calculation)
            memory_request = self._parse_memory_value(requests.get('memory', '0'))
            memory_limit = self._parse_memory_value(limits.get('memory', '0'))
            
            total_cpu_requests += cpu_request
            total_cpu_limits += cpu_limit
            total_memory_requests += memory_request
            total_memory_limits += memory_limit
        
        return {
            'cpu': f"{total_cpu_requests}m",
            'memory': f"{total_memory_requests}Mi",
            'cpu_limit': f"{total_cpu_limits}m",
            'memory_limit': f"{total_memory_limits}Mi"
        }
    
    def _parse_cpu_value(self, cpu_str: str) -> int:
        """Parse CPU value to millicores"""
        if not cpu_str or cpu_str == '0':
            return 0
        
        cpu_str = cpu_str.strip()
        if cpu_str.endswith('m'):
            return int(cpu_str[:-1])
        elif cpu_str.endswith('n'):
            return int(cpu_str[:-1]) // 1000000
        else:
            return int(float(cpu_str) * 1000)
    
    def _parse_memory_value(self, memory_str: str) -> int:
        """Parse memory value to MiB"""
        if not memory_str or memory_str == '0':
            return 0
        
        memory_str = memory_str.strip().upper()
        multipliers = {
            'KI': 1024,
            'MI': 1,
            'GI': 1/1024,
            'TI': 1/(1024*1024)
        }
        
        for suffix, multiplier in multipliers.items():
            if memory_str.endswith(suffix):
                return int(float(memory_str[:-len(suffix)]) * multiplier)
        
        # Assume bytes if no suffix
        return int(float(memory_str) / (1024 * 1024))
    
    def get_services(self, namespace: Optional[str] = None) -> List[ServiceInfo]:
        """Get information about all services"""
        services_data = self._run_kubectl_command(['get', 'services'], namespace)
        services = []
        
        if 'items' in services_data:
            for service_data in services_data['items']:
                service_info = self._parse_service_info(service_data)
                services.append(service_info)
        
        return services
    
    def _parse_service_info(self, service_data: Dict[str, Any]) -> ServiceInfo:
        """Parse service information from kubectl output"""
        metadata = service_data.get('metadata', {})
        spec = service_data.get('spec', {})
        status = service_data.get('status', {})
        
        # Parse ports
        ports = []
        for port in spec.get('ports', []):
            ports.append({
                'name': port.get('name', ''),
                'port': port.get('port', 0),
                'target_port': port.get('targetPort', 0),
                'protocol': port.get('protocol', 'TCP')
            })
        
        return ServiceInfo(
            name=metadata.get('name', ''),
            namespace=metadata.get('namespace', ''),
            type=spec.get('type', 'ClusterIP'),
            cluster_ip=spec.get('clusterIP', ''),
            external_ip=status.get('loadBalancer', {}).get('ingress', [{}])[0].get('ip'),
            ports=ports,
            selector=spec.get('selector', {})
        )
    
    def get_resource_usage(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get resource usage information.
        Note: This requires metrics-server to be installed in the cluster.
        """
        try:
            # Get pod metrics
            pod_metrics = self._run_kubectl_command(['top', 'pods'], namespace)
            node_metrics = self._run_kubectl_command(['top', 'nodes'])
            
            return {
                'pod_metrics': pod_metrics,
                'node_metrics': node_metrics,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Could not get resource usage (metrics-server may not be installed): {e}")
            return {}
    
    def get_cluster_metrics(self) -> ClusterMetrics:
        """Get overall cluster metrics"""
        pods = self.get_pods()
        services = self.get_services()
        nodes = self.get_nodes()
        
        # Count pod statuses
        pod_statuses = {}
        for pod in pods:
            status = pod.status
            pod_statuses[status] = pod_statuses.get(status, 0) + 1
        
        # Count node statuses
        ready_nodes = sum(1 for node in nodes if node.status == 'Ready')
        
        return ClusterMetrics(
            total_pods=len(pods),
            running_pods=pod_statuses.get('Running', 0),
            pending_pods=pod_statuses.get('Pending', 0),
            failed_pods=pod_statuses.get('Failed', 0),
            total_services=len(services),
            total_nodes=len(nodes),
            ready_nodes=ready_nodes,
            total_cpu_usage=0.0,  # Would need metrics server
            total_memory_usage=0.0  # Would need metrics server
        )
    
    def get_comprehensive_report(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get a comprehensive monitoring report"""
        self.logger.info("Generating comprehensive cluster report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'cluster_info': self.get_cluster_info(),
            'nodes': [asdict(node) for node in self.get_nodes()],
            'pods': [asdict(pod) for pod in self.get_pods(namespace)],
            'services': [asdict(service) for service in self.get_services(namespace)],
            'cluster_metrics': asdict(self.get_cluster_metrics()),
            'resource_usage': self.get_resource_usage(namespace)
        }
        
        return report
    
    def save_report_to_file(self, report: Dict[str, Any], filename: str) -> None:
        """Save report to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Report saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
    
    def print_summary(self, namespace: Optional[str] = None) -> None:
        """Print a summary of cluster status"""
        metrics = self.get_cluster_metrics()
        
        print("\n" + "="*50)
        print("KUBERNETES CLUSTER SUMMARY")
        print("="*50)
        print(f"Total Nodes: {metrics.total_nodes} (Ready: {metrics.ready_nodes})")
        print(f"Total Pods: {metrics.total_pods}")
        print(f"  - Running: {metrics.running_pods}")
        print(f"  - Pending: {metrics.pending_pods}")
        print(f"  - Failed: {metrics.failed_pods}")
        print(f"Total Services: {metrics.total_services}")
        print("="*50)


# def main():
#     """Example usage of the KubernetesMonitor class"""
#     # Initialize monitor
#     monitor = KubernetesMonitor()
    
#     # Print available contexts
#     contexts = monitor.get_available_contexts()
#     print(f"Available contexts: {contexts}")
    
#     # Generate comprehensive report
#     report = monitor.get_comprehensive_report()
    
#     # Print summary
#     monitor.print_summary()
    
#     # Save report to file
#     monitor.save_report_to_file(report, 'kubernetes_report.json')
    
#     # Example of monitoring specific namespace
#     if contexts:
#         print(f"\nMonitoring namespace 'default' in context '{contexts[0]}'")
#         namespace_report = monitor.get_comprehensive_report('default')
#         monitor.save_report_to_file(namespace_report, 'kubernetes_namespace_report.json')


# if __name__ == "__main__":
#     main()
