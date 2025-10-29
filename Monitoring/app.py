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
                    color = get_node_color(labels[0] if labels else 'Node')
                    cleaned_props = convert_datetime_types(props)
                    
                    node_map[node_id] = {
                        'id': node_id,
                        'label': props.get('name', node_id.split('_')[-1]),
                        'group': labels[0] if labels else 'Node',
                        'color': color,
                        'title': get_node_tooltip(props, labels[0] if labels else 'Node'),
                        'properties': cleaned_props,
                        'type': labels[0] if labels else 'Node'
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


def get_node_color(label):
    """Get color for node based on label"""
    color_map = {
        'VM': '#FF6B6B',
        'Cluster': '#4ECDC4',
        'Node': '#45B7D1',
        'Pod': '#96CEB4',
        'Service': '#FECA57',
        'Container': '#FF9FF3',
        'ClusterMetrics': '#A8E6CF'
    }
    return color_map.get(label, '#BDC3C7')


def get_edge_color(rel_type):
    """Get color for edge based on relationship type"""
    color_map = {
        'HOSTS': '#FF6B6B',
        'CONTAINS': '#4ECDC4',
        'RELATES_TO': '#95A5A6'
    }
    return color_map.get(rel_type, '#95A5A6')


def get_node_tooltip(props, node_type):
    """Generate tooltip text for node"""
    lines = [f"📋 {node_type}"]
    lines.append("─" * 30)
    
    # Add key properties to tooltip
    if 'name' in props:
        lines.append(f"📌 Name: {props['name']}")
    if 'status' in props:
        emoji = "✅" if props['status'] == "Ready" else "❌"
        lines.append(f"{emoji} Status: {props['status']}")
    if 'context' in props:
        lines.append(f"🌐 Context: {props['context']}")
    if 'namespace' in props:
        lines.append(f"📦 Namespace: {props['namespace']}")
    if 'hostname' in props:
        lines.append(f"💻 Host: {props['hostname']}")
    
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

