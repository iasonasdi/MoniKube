#!/usr/bin/env python3
"""
Example usage of the KubernetesMonitor class.
This script demonstrates various ways to use the monitoring capabilities.
"""

from kubernetes_monitor import KubernetesMonitor
import json
import time


def example_basic_monitoring():
    """Basic monitoring example"""
    print("=== Basic Kubernetes Monitoring Example ===")
    
    # Initialize the monitor
    monitor = KubernetesMonitor()
    
    # Get available contexts
    contexts = monitor.get_available_contexts()
    print(f"Available Kubernetes contexts: {contexts}")
    
    if not contexts:
        print("No Kubernetes contexts found. Make sure kubectl is configured.")
        return
    
    # Print cluster summary
    monitor.print_summary()
    
    # Get detailed information
    print("\n=== Node Information ===")
    nodes = monitor.get_nodes()
    for node in nodes:
        print(f"Node: {node.name}")
        print(f"  Status: {node.status}")
        print(f"  Roles: {', '.join(node.roles)}")
        print(f"  CPU Capacity: {node.cpu_capacity}")
        print(f"  Memory Capacity: {node.memory_capacity}")
        print()


def example_namespace_monitoring():
    """Example of monitoring specific namespace"""
    print("\n=== Namespace-specific Monitoring ===")
    
    monitor = KubernetesMonitor()
    
    # Monitor specific namespace
    namespace = "default"
    print(f"Monitoring namespace: {namespace}")
    
    # Get pods in namespace
    pods = monitor.get_pods(namespace)
    print(f"Found {len(pods)} pods in namespace '{namespace}':")
    
    for pod in pods:
        print(f"  Pod: {pod.name}")
        print(f"    Status: {pod.status}")
        print(f"    Node: {pod.node}")
        print(f"    Containers: {len(pod.containers)}")
        for container in pod.containers:
            print(f"      - {container.name} ({container.image})")
        print()


def example_service_monitoring():
    """Example of monitoring services"""
    print("\n=== Service Monitoring ===")
    
    monitor = KubernetesMonitor()
    
    # Get all services
    services = monitor.get_services()
    print(f"Found {len(services)} services:")
    
    for service in services:
        print(f"  Service: {service.name}")
        print(f"    Namespace: {service.namespace}")
        print(f"    Type: {service.type}")
        print(f"    Cluster IP: {service.cluster_ip}")
        if service.external_ip:
            print(f"    External IP: {service.external_ip}")
        print(f"    Ports: {len(service.ports)}")
        for port in service.ports:
            print(f"      - {port['port']}:{port['target_port']} ({port['protocol']})")
        print()


def example_comprehensive_report():
    """Example of generating comprehensive reports"""
    print("\n=== Comprehensive Report Generation ===")
    
    monitor = KubernetesMonitor()
    
    # Generate comprehensive report
    print("Generating comprehensive cluster report...")
    report = monitor.get_comprehensive_report()
    
    # Save to file
    filename = f"kubernetes_report_{int(time.time())}.json"
    monitor.save_report_to_file(report, filename)
    print(f"Report saved to: {filename}")
    
    # Print some key metrics from the report
    metrics = report.get('cluster_metrics', {})
    print(f"\nCluster Metrics:")
    print(f"  Total Pods: {metrics.get('total_pods', 0)}")
    print(f"  Running Pods: {metrics.get('running_pods', 0)}")
    print(f"  Total Nodes: {metrics.get('total_nodes', 0)}")
    print(f"  Ready Nodes: {metrics.get('ready_nodes', 0)}")
    print(f"  Total Services: {metrics.get('total_services', 0)}")


def example_custom_context():
    """Example of using specific kubeconfig and context"""
    print("\n=== Custom Context Example ===")
    
    # Example with custom kubeconfig path and context
    # monitor = KubernetesMonitor(
    #     kubeconfig_path="/path/to/your/kubeconfig",
    #     context="your-context-name"
    # )
    
    # For this example, we'll use the default configuration
    monitor = KubernetesMonitor()
    
    # Get cluster info
    cluster_info = monitor.get_cluster_info()
    print("Cluster Information:")
    print(json.dumps(cluster_info, indent=2))


def example_resource_monitoring():
    """Example of resource usage monitoring"""
    print("\n=== Resource Usage Monitoring ===")
    
    monitor = KubernetesMonitor()
    
    # Get resource usage (requires metrics-server)
    resource_usage = monitor.get_resource_usage()
    
    if resource_usage:
        print("Resource usage data available:")
        print(json.dumps(resource_usage, indent=2))
    else:
        print("Resource usage data not available.")
        print("Note: This requires metrics-server to be installed in the cluster.")


def example_continuous_monitoring():
    """Example of continuous monitoring"""
    print("\n=== Continuous Monitoring Example ===")
    
    monitor = KubernetesMonitor()
    
    print("Starting continuous monitoring (press Ctrl+C to stop)...")
    try:
        for i in range(5):  # Monitor for 5 iterations
            print(f"\n--- Monitoring Cycle {i+1} ---")
            
            # Get current metrics
            metrics = monitor.get_cluster_metrics()
            
            print(f"Pods: {metrics.running_pods}/{metrics.total_pods} running")
            print(f"Nodes: {metrics.ready_nodes}/{metrics.total_nodes} ready")
            
            # Wait before next cycle
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")


def main():
    """Run all examples"""
    print("Kubernetes Monitor - Example Usage")
    print("=" * 50)
    
    try:
        # Run examples
        example_basic_monitoring()
        example_namespace_monitoring()
        example_service_monitoring()
        example_comprehensive_report()
        example_custom_context()
        example_resource_monitoring()
        
        # Uncomment to run continuous monitoring
        # example_continuous_monitoring()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure kubectl is installed and configured properly.")


if __name__ == "__main__":
    main()
