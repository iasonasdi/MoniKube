#!/usr/bin/env python3
"""
Flask Backend API for Neo4j Visualization
Provides REST API endpoints to query Neo4j database and retrieve graph data
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime as py_datetime
from neo4j.time import DateTime as NeoDateTime

# Add parent directory to path to import neo4j_handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from neo4j_handler import Neo4JHandler

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

# Global handler
handler = None


def convert_datetime_types(obj):
    """Recursively convert Neo4j DateTime objects to strings for JSON serialization"""
    if isinstance(obj, NeoDateTime):
        return str(obj)
    elif isinstance(obj, py_datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetime_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_types(item) for item in obj]
    else:
        return obj


def init_handler():
    """Initialize Neo4j handler"""
    global handler
    # Default Neo4j connection parameters
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
    neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    handler = Neo4JHandler(
        uri=neo4j_uri,
        username=neo4j_username,
        password=neo4j_password,
        database=neo4j_database
    )
    
    return handler.connect()


@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    global handler
    if handler and handler.driver:
        try:
            with handler.driver.session() as session:
                session.run("RETURN 1")
            return jsonify({'status': 'healthy', 'neo4j': 'connected'})
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    return jsonify({'status': 'unhealthy', 'neo4j': 'not connected'}), 500


@app.route('/api/graph')
def get_graph():
    """Get the complete graph data for visualization"""
    global handler
    try:
        # Use a better query that returns all nodes and relationships
        query = """
        MATCH (n)
        RETURN n, labels(n) as labels, properties(n) as props
        """
        
        query_relations = """
        MATCH (n)-[r]->(m)
        RETURN n, m, r, type(r) as rel_type
        """
        
        with handler.driver.session() as session:
            # First pass: get all nodes
            result = session.run(query)
            node_map = {}
            
            for record in result:
                labels = list(record['labels'])
                props = dict(record['props'])
                node_id = props.get('id')
                
                if not node_id:
                    continue
                
                if node_id not in node_map:
                    node_type = labels[0] if labels else 'Node'
                    color = get_node_color(node_type)
                    cleaned_props = convert_datetime_types(props)
                    
                    # Generate enhanced label with key information
                    enhanced_label = get_node_label(cleaned_props, node_type)
                    
                    node_map[node_id] = {
                        'id': node_id,
                        'label': enhanced_label,
                        'group': node_type,
                        'color': color,
                        'title': get_node_tooltip(cleaned_props, node_type),
                        'properties': cleaned_props,
                        'type': node_type
                    }
            
            # Second pass: get all relationships
            edge_map = {}
            result_relations = session.run(query_relations)
            
            for record in result_relations:
                source_node = record['n']
                target_node = record['m']
                rel_type = record['rel_type']
                
                # Get properties for both nodes
                if hasattr(source_node, 'items'):
                    source_props = dict(source_node.items())
                else:
                    source_props = {}
                    
                if hasattr(target_node, 'items'):
                    target_props = dict(target_node.items())
                else:
                    target_props = {}
                
                source_id = source_props.get('id')
                target_id = target_props.get('id')
                
                # Make sure both nodes exist in our node_map
                if source_id and target_id and source_id in node_map and target_id in node_map:
                    edge_key = f"{source_id}_{target_id}_{rel_type}"
                    if edge_key not in edge_map:
                        edge_map[edge_key] = {
                            'from': source_id,
                            'to': target_id,
                            'label': rel_type,
                            'arrows': 'to',
                            'color': get_edge_color(rel_type)
                        }
            
            nodes = list(node_map.values())
            edges = list(edge_map.values())
        
        return jsonify({'nodes': nodes, 'edges': edges})
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/node/<node_id>')
def get_node_details(node_id):
    """Get detailed information about a specific node"""
    global handler
    try:
        # Escape node_id for safety
        query = """
        MATCH (n {id: $node_id})
        RETURN n
        """
        
        result = handler.query_data(query, {'node_id': node_id})
        
        if result and result[0].get('n'):
            node = result[0]['n']
            labels = list(node.labels) if hasattr(node, 'labels') else ['Node']
            props = dict(node.items()) if hasattr(node, 'items') else {}
            
            return jsonify({
                'id': node_id,
                'labels': labels,
                'properties': props,
                'type': labels[0]
            })
        
        return jsonify({'error': 'Node not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nodes')
def get_nodes():
    """Get all nodes grouped by type"""
    global handler
    try:
        query = """
        MATCH (n)
        RETURN labels(n) as labels, count(*) as count
        """
        
        result = handler.query_data(query)
        
        return jsonify({
            'summary': [
                {'type': labels[0] if labels else 'Unknown', 'count': record['count']}
                for record in result
                if record['labels']
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/query')
def execute_query():
    """Execute a custom Cypher query"""
    global handler
    try:
        # For security, this endpoint should be restricted in production
        query = request.args.get('query', '')
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        result = handler.query_data(query)
        return jsonify({'result': result})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/resource-usage')
def get_resource_usage():
    """Get resource usage information for nodes and pods"""
    global handler
    try:
        query = """
        MATCH (ru:ResourceUsage)
        RETURN ru.cluster_id, ru.timestamp, ru.pod_metrics, ru.node_metrics
        ORDER BY ru.timestamp DESC
        LIMIT 10
        """
        result = handler.query_data(query)
        return jsonify({'resource_usage': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nodes-high-cpu')
def get_nodes_high_cpu():
    """Get nodes with high CPU usage"""
    global handler
    try:
        threshold = float(request.args.get('threshold', 0.5))
        query = """
        MATCH (n:Node)
        WHERE n.cpu_usage > $threshold
        RETURN n.id, n.name, n.cpu_usage, n.memory_usage, n.status, n.cluster_id
        ORDER BY n.cpu_usage DESC
        """
        result = handler.query_data(query, {'threshold': threshold})
        return jsonify({'nodes': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/containers-high-cpu')
def get_containers_high_cpu():
    """Get containers with high CPU usage"""
    global handler
    try:
        threshold = float(request.args.get('threshold', 0.5))
        query = """
        MATCH (ct:Container)
        WHERE ct.cpu_usage > $threshold
        RETURN ct.id, ct.name, ct.image, ct.cpu_usage, ct.memory_usage, ct.pod_id
        ORDER BY ct.cpu_usage DESC
        """
        result = handler.query_data(query, {'threshold': threshold})
        return jsonify({'containers': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cluster-summary')
def get_cluster_summary():
    """Get cluster summary with metrics"""
    global handler
    try:
        cluster_id = request.args.get('cluster_id', None)
        if cluster_id:
            query = """
            MATCH (c:Cluster {id: $cluster_id})
            OPTIONAL MATCH (c)-[:CONTAINS]->(n:Node)
            OPTIONAL MATCH (c)-[:CONTAINS]->(p:Pod)
            OPTIONAL MATCH (c)-[:CONTAINS]->(s:Service)
            OPTIONAL MATCH (cm:ClusterMetrics {cluster_id: $cluster_id})
            RETURN c, 
                   count(DISTINCT n) as node_count,
                   count(DISTINCT p) as pod_count,
                   count(DISTINCT s) as service_count,
                   cm
            """
            result = handler.query_data(query, {'cluster_id': cluster_id})
        else:
            query = """
            MATCH (c:Cluster)
            OPTIONAL MATCH (c)-[:CONTAINS]->(n:Node)
            OPTIONAL MATCH (c)-[:CONTAINS]->(p:Pod)
            OPTIONAL MATCH (c)-[:CONTAINS]->(s:Service)
            OPTIONAL MATCH (cm:ClusterMetrics)
            WHERE cm.cluster_id = c.id
            RETURN c.id as cluster_id, c.context, c.vm_id, c.timestamp,
                   count(DISTINCT n) as node_count,
                   count(DISTINCT p) as pod_count,
                   count(DISTINCT s) as service_count,
                   cm
            ORDER BY c.timestamp DESC
            """
            result = handler.query_data(query)
        
        return jsonify({'summary': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_node_color(label):
    """Get color for node based on label"""
    color_map = {
        'VM': '#FF6B6B',
        'Cluster': '#4ECDC4',
        'Node': '#45B7D1',
        'Pod': '#96CEB4',
        'Service': '#FECA57',
        'Container': '#FF9FF3',
        'ClusterMetrics': '#A8E6CF',
        'ResourceUsage': '#FFA07A'
    }
    return color_map.get(label, '#BDC3C7')


def get_edge_color(rel_type):
    """Get color for edge based on relationship type"""
    color_map = {
        'HOSTS': '#FF6B6B',
        'CONTAINS': '#4ECDC4',
        'HAS_RESOURCE_USAGE': '#FFA07A',
        'RELATES_TO': '#95A5A6'
    }
    return color_map.get(rel_type, '#95A5A6')


def format_memory(value):
    """Format memory value for display"""
    if isinstance(value, (int, float)):
        if value >= 1024:
            return f"{value/1024:.2f} GiB"
        else:
            return f"{value:.2f} MiB"
    return str(value)


def format_cpu(value):
    """Format CPU value for display"""
    if isinstance(value, (int, float)):
        if value >= 1:
            return f"{value:.2f} cores"
        else:
            return f"{value*1000:.0f} millicores"
    return str(value)


def get_node_label(props, node_type):
    """Generate enhanced label for node with key information"""
    name = props.get('name', 'Unknown')
    
    if node_type == 'VM':
        hostname = props.get('hostname', '')
        return f"{hostname}\nVM"
    
    elif node_type == 'Cluster':
        context = props.get('context', 'default')
        return f"{context}\nCluster"
    
    elif node_type == 'Node':
        status_emoji = "✅" if props.get('status') == 'Ready' else "❌"
        cpu_usage = props.get('cpu_usage', 0)
        if cpu_usage and cpu_usage > 0:
            return f"{name}\n{status_emoji} CPU: {format_cpu(cpu_usage)}"
        return f"{name}\n{status_emoji}"
    
    elif node_type == 'Pod':
        status = props.get('status', 'Unknown')
        namespace = props.get('namespace', 'default')
        return f"{name}\n{namespace}\n[{status}]"
    
    elif node_type == 'Service':
        svc_type = props.get('type', 'ClusterIP')
        cluster_ip = props.get('cluster_ip', 'N/A')
        return f"{name}\n{svc_type}\n{cluster_ip}"
    
    elif node_type == 'Container':
        image = props.get('image', '')
        if image:
            image_short = image.split('/')[-1][:20] if len(image) > 20 else image
            return f"{name}\n{image_short}"
        return name
    
    elif node_type == 'ClusterMetrics':
        total_pods = props.get('total_pods', 0)
        running_pods = props.get('running_pods', 0)
        return f"Metrics\nPods: {running_pods}/{total_pods}"
    
    return name


def get_node_tooltip(props, node_type):
    """Generate comprehensive tooltip text for node with all available information"""
    lines = [f"📋 {node_type}"]
    lines.append("═" * 40)
    
    # Common properties
    if 'name' in props:
        lines.append(f"📌 Name: {props['name']}")
    
    if 'id' in props:
        lines.append(f"🆔 ID: {props['id']}")
    
    # VM-specific information
    if node_type == 'VM':
        if 'hostname' in props:
            lines.append(f"💻 Hostname: {props['hostname']}")
        if 'ip_addresses' in props:
            ip_addresses = props['ip_addresses']
            if isinstance(ip_addresses, list) and ip_addresses:
                lines.append(f"🌐 IP Addresses:")
                for ip in ip_addresses:
                    lines.append(f"   • {ip}")
            elif ip_addresses:
                lines.append(f"🌐 IP: {ip_addresses}")
        if 'platform' in props:
            lines.append(f"💾 Platform: {props['platform']}")
        if 'python_version' in props:
            lines.append(f"🐍 Python: {props['python_version']}")
        if 'timestamp' in props:
            lines.append(f"🕐 First Seen: {props['timestamp']}")
    
    # Cluster-specific information
    elif node_type == 'Cluster':
        if 'context' in props:
            lines.append(f"🌐 Context: {props['context']}")
        if 'available_contexts' in props:
            contexts = props['available_contexts']
            if isinstance(contexts, list):
                lines.append(f"📋 Available Contexts ({len(contexts)}):")
                for ctx in contexts[:5]:  # Show first 5
                    lines.append(f"   • {ctx}")
                if len(contexts) > 5:
                    lines.append(f"   ... and {len(contexts) - 5} more")
        if 'cluster_info' in props:
            try:
                cluster_info = json.loads(props['cluster_info']) if isinstance(props['cluster_info'], str) else props['cluster_info']
                if isinstance(cluster_info, dict):
                    if 'version' in cluster_info:
                        lines.append(f"📦 Kubernetes Version: {cluster_info.get('version', {}).get('serverVersion', {}).get('gitVersion', 'N/A')}")
            except:
                pass
        if 'vm_id' in props:
            lines.append(f"🖥️  VM ID: {props['vm_id']}")
    
    # Node-specific information
    elif node_type == 'Node':
        if 'status' in props:
            status = props['status']
            emoji = "✅" if status == "Ready" else "❌" if status == "NotReady" else "⚠️"
            lines.append(f"{emoji} Status: {status}")
        if 'roles' in props:
            roles = props['roles']
            if isinstance(roles, list):
                lines.append(f"👤 Roles: {', '.join(roles)}")
            elif roles:
                lines.append(f"👤 Role: {roles}")
        if 'cpu_capacity' in props:
            lines.append(f"⚡ CPU Capacity: {props['cpu_capacity']}")
        if 'memory_capacity' in props:
            lines.append(f"💾 Memory Capacity: {props['memory_capacity']}")
        if 'cpu_allocatable' in props:
            lines.append(f"⚡ CPU Allocatable: {props['cpu_allocatable']}")
        if 'memory_allocatable' in props:
            lines.append(f"💾 Memory Allocatable: {props['memory_allocatable']}")
        if 'cpu_usage' in props:
            cpu_usage = props['cpu_usage']
            if cpu_usage and cpu_usage > 0:
                lines.append(f"📊 CPU Usage: {format_cpu(cpu_usage)}")
        if 'memory_usage' in props:
            memory_usage = props['memory_usage']
            if memory_usage and memory_usage > 0:
                lines.append(f"📊 Memory Usage: {format_memory(memory_usage)}")
        if 'cluster_id' in props:
            lines.append(f"🏢 Cluster ID: {props['cluster_id']}")
    
    # Pod-specific information
    elif node_type == 'Pod':
        if 'namespace' in props:
            lines.append(f"📦 Namespace: {props['namespace']}")
        if 'status' in props:
            status = props['status']
            status_emoji = {
                'Running': '✅',
                'Pending': '⏳',
                'Failed': '❌',
                'Succeeded': '✓',
                'Unknown': '❓'
            }.get(status, '❓')
            lines.append(f"{status_emoji} Status: {status}")
        if 'node' in props:
            lines.append(f"🖥️  Node: {props['node']}")
        if 'cpu_requests' in props:
            lines.append(f"⚡ CPU Requests: {props['cpu_requests']}")
        if 'memory_requests' in props:
            lines.append(f"💾 Memory Requests: {props['memory_requests']}")
        if 'cpu_limits' in props:
            lines.append(f"⚡ CPU Limits: {props['cpu_limits']}")
        if 'memory_limits' in props:
            lines.append(f"💾 Memory Limits: {props['memory_limits']}")
        if 'cluster_id' in props:
            lines.append(f"🏢 Cluster ID: {props['cluster_id']}")
    
    # Service-specific information
    elif node_type == 'Service':
        if 'namespace' in props:
            lines.append(f"📦 Namespace: {props['namespace']}")
        if 'type' in props:
            lines.append(f"🔧 Type: {props['type']}")
        if 'cluster_ip' in props:
            lines.append(f"🌐 Cluster IP: {props['cluster_ip']}")
        if 'external_ip' in props:
            ext_ip = props['external_ip']
            if ext_ip:
                lines.append(f"🌍 External IP: {ext_ip}")
        if 'ports' in props:
            try:
                ports = json.loads(props['ports']) if isinstance(props['ports'], str) else props['ports']
                if isinstance(ports, list) and ports:
                    lines.append(f"🔌 Ports ({len(ports)}):")
                    for port in ports[:5]:  # Show first 5 ports
                        port_num = port.get('port', 'N/A')
                        target_port = port.get('target_port', 'N/A')
                        protocol = port.get('protocol', 'TCP')
                        lines.append(f"   • {port_num} → {target_port} ({protocol})")
                    if len(ports) > 5:
                        lines.append(f"   ... and {len(ports) - 5} more")
            except:
                if props['ports']:
                    lines.append(f"🔌 Ports: {props['ports']}")
        if 'selector' in props:
            try:
                selector = json.loads(props['selector']) if isinstance(props['selector'], str) else props['selector']
                if isinstance(selector, dict) and selector:
                    lines.append(f"🏷️  Selectors:")
                    for key, value in list(selector.items())[:3]:  # Show first 3
                        lines.append(f"   • {key}: {value}")
                    if len(selector) > 3:
                        lines.append(f"   ... and {len(selector) - 3} more")
            except:
                if props['selector']:
                    lines.append(f"🏷️  Selector: {props['selector']}")
        if 'cluster_id' in props:
            lines.append(f"🏢 Cluster ID: {props['cluster_id']}")
    
    # Container-specific information
    elif node_type == 'Container':
        if 'image' in props:
            lines.append(f"🐳 Image: {props['image']}")
        if 'status' in props:
            lines.append(f"📊 Status: {props['status']}")
        if 'cpu_usage' in props:
            cpu_usage = props['cpu_usage']
            if cpu_usage and cpu_usage > 0:
                lines.append(f"⚡ CPU Usage: {format_cpu(cpu_usage)}")
        if 'memory_usage' in props:
            memory_usage = props['memory_usage']
            if memory_usage and memory_usage > 0:
                lines.append(f"💾 Memory Usage: {format_memory(memory_usage)}")
        if 'cpu_limit' in props:
            lines.append(f"⚡ CPU Limit: {props['cpu_limit']}")
        if 'memory_limit' in props:
            lines.append(f"💾 Memory Limit: {props['memory_limit']}")
        if 'pod_id' in props:
            lines.append(f"📦 Pod ID: {props['pod_id']}")
    
    # ClusterMetrics-specific information
    elif node_type == 'ClusterMetrics':
        lines.append(f"📊 Cluster Metrics:")
        if 'total_pods' in props:
            lines.append(f"   • Total Pods: {props['total_pods']}")
        if 'running_pods' in props:
            lines.append(f"   • Running Pods: {props['running_pods']}")
        if 'pending_pods' in props:
            lines.append(f"   • Pending Pods: {props['pending_pods']}")
        if 'failed_pods' in props:
            lines.append(f"   • Failed Pods: {props['failed_pods']}")
        if 'total_services' in props:
            lines.append(f"   • Total Services: {props['total_services']}")
        if 'total_nodes' in props:
            lines.append(f"   • Total Nodes: {props['total_nodes']}")
        if 'ready_nodes' in props:
            lines.append(f"   • Ready Nodes: {props['ready_nodes']}")
        if 'total_cpu_usage' in props:
            cpu_usage = props['total_cpu_usage']
            if cpu_usage and cpu_usage > 0:
                lines.append(f"   • Total CPU Usage: {format_cpu(cpu_usage)}")
        if 'total_memory_usage' in props:
            memory_usage = props['total_memory_usage']
            if memory_usage and memory_usage > 0:
                lines.append(f"   • Total Memory Usage: {format_memory(memory_usage)}")
        if 'cluster_id' in props:
            lines.append(f"🏢 Cluster ID: {props['cluster_id']}")
    
    # ResourceUsage-specific information
    elif node_type == 'ResourceUsage':
        lines.append(f"📊 Resource Usage Metrics:")
        if 'timestamp' in props:
            lines.append(f"🕐 Timestamp: {props['timestamp']}")
        if 'pod_metrics' in props:
            lines.append(f"📦 Pod Metrics: Available")
        if 'node_metrics' in props:
            lines.append(f"🖥️  Node Metrics: Available")
        if 'cluster_id' in props:
            lines.append(f"🏢 Cluster ID: {props['cluster_id']}")
    
    # Timestamp information (common to all)
    if 'timestamp' in props and node_type != 'VM' and node_type != 'ResourceUsage':
        lines.append(f"🕐 Collected: {props['timestamp']}")
    if 'last_updated' in props:
        lines.append(f"🔄 Last Updated: {props['last_updated']}")
    
    return "\n".join(lines)


if __name__ == '__main__':
    print("Initializing Neo4j connection...")
    if init_handler():
        print("Connected to Neo4j successfully!")
        print("Starting Flask server on http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("Failed to connect to Neo4j. Please check your connection settings.")
        print("Set environment variables: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE")

