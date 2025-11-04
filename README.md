# MoniKube

A comprehensive Kubernetes distributed monitoring tool that monitors all clusters deployed on a VM and collects data, stats, and system metrics.

## 🚀 Features

- **Multi-Cluster Monitoring**: Automatically discover and monitor multiple Kubernetes clusters
- **Real-time Monitoring**: Continuous monitoring with customizable intervals
- **Comprehensive Data Collection**: 
  - Cluster information and versions
  - Node status, roles, and resource capacity
  - Pod status, containers, and resource usage
  - Service discovery and configuration
  - System metrics (CPU, RAM) when metrics-server is available
- **Flexible Execution**: Run once, limited iterations, or continuously
- **Rich Console Output**: Visual status indicators and detailed reporting
- **JSON Reporting**: Export comprehensive reports for further analysis
- **Object-Oriented Design**: Easy to extend and customize

## 📋 Requirements

- Python 3.7+
- kubectl installed and configured
- Access to Kubernetes clusters
- metrics-server (optional, for resource usage monitoring)

## 🛠️ Installation

1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Quick Start

### Basic Usage

```bash
# Run continuously (default: every 10 seconds)
python main.py

# Run every 5 seconds
python main.py -t 5

# Run 10 times, every 30 seconds
python main.py -t 30 -n 10

# Run once (single report)
python main.py -t 60 -n 1

# Run with Neo4J storing
python3 main.py -db -t 30 -n 5
```

### Command Line Options

- `-t, --time`: Time interval between monitoring cycles in seconds (default: 10)
- `-n, --iterations`: Number of monitoring cycles to run (0 = continuous, default: 0)
- `-db, --neo4j-uri bolt://neo4j-server:7687 --neo4j-username admin --neo4j-password secret`: Store data in the Neo4J database

### Examples

```bash
# Continuous monitoring every 5 seconds
python main.py -t 5

# Run 5 monitoring cycles, every 30 seconds
python main.py -t 30 -n 5

# Single report
python main.py -n 1

# Show help
python main.py --help
```

## 📊 What It Monitors

The tool collects comprehensive information about your Kubernetes clusters through `kubectl` commands. All data is collected in JSON format and parsed into structured dataclasses. Here's what information is collected:

### 1. Cluster-Level Information
- **Cluster Info**: Basic cluster connectivity and status from `kubectl cluster-info`
- **Version Information**: Kubernetes version details from `kubectl version`
- **Available Contexts**: List of all configured Kubernetes contexts
- **Timestamps**: Each collection includes timestamp information for tracking

### 2. Node Information
For each node in the cluster, the following data is collected:
- **Node Name**: Unique identifier for the node
- **Status**: Node health status (Ready/NotReady/Unknown) extracted from node conditions
- **Roles**: Node roles (master, worker, control-plane, etc.) extracted from labels
- **Resource Capacity**:
  - CPU capacity (total CPU available on the node)
  - Memory capacity (total memory available on the node)
- **Resource Allocatable**:
  - CPU allocatable (CPU available for pods after system reservations)
  - Memory allocatable (Memory available for pods after system reservations)
- **Resource Usage** (requires metrics-server):
  - Real-time CPU usage percentage
  - Real-time memory usage percentage

### 3. Pod Information
For each pod in the cluster, the following data is collected:

**Pod-Level Data:**
- **Pod Name**: Unique identifier for the pod
- **Namespace**: The namespace where the pod is deployed
- **Status**: Pod phase (Running, Pending, Failed, Succeeded, Unknown)
- **Node Assignment**: Which node the pod is scheduled on
- **Resource Requests** (aggregated across all containers):
  - Total CPU requests (in millicores)
  - Total memory requests (in MiB)
- **Resource Limits** (aggregated across all containers):
  - Total CPU limits (in millicores)
  - Total memory limits (in MiB)

**Container-Level Data** (for each container within the pod):
- **Container Name**: Name of the container
- **Image**: Container image name and tag
- **Status**: Container state (extracted from running state, including startedAt timestamp)
- **Resource Limits**:
  - CPU limit (if configured)
  - Memory limit (if configured)
- **Resource Usage** (requires metrics-server):
  - Real-time CPU usage
  - Real-time memory usage

### 4. Service Information
For each service in the cluster, the following data is collected:
- **Service Name**: Unique identifier for the service
- **Namespace**: The namespace where the service is deployed
- **Service Type**: Type of service (ClusterIP, NodePort, LoadBalancer, ExternalName)
- **IP Addresses**:
  - Cluster IP (internal cluster IP address)
  - External IP (if applicable, for LoadBalancer services)
- **Port Configuration**: For each port exposed by the service:
  - Port name (if named)
  - Port number
  - Target port (port on the pods)
  - Protocol (TCP, UDP, etc.)
- **Selectors**: Label selectors used to match pods

### 5. Resource Usage Metrics
**Note**: This requires metrics-server to be installed in your cluster. Without it, usage metrics will be `0.0`.

- **Pod Metrics**: Real-time CPU and memory usage for all pods via `kubectl top pods`
- **Node Metrics**: Real-time CPU and memory usage for all nodes via `kubectl top nodes`
- **Timestamp**: When the metrics were collected

### 6. Aggregated Cluster Metrics
The tool also calculates and provides aggregated statistics:
- **Pod Counts**:
  - Total pods in the cluster
  - Running pods count
  - Pending pods count
  - Failed pods count
- **Service Count**: Total number of services
- **Node Counts**:
  - Total nodes in the cluster
  - Ready nodes count (nodes in Ready state)
- **Resource Usage** (requires metrics-server):
  - Total CPU usage across the cluster
  - Total memory usage across the cluster

### Data Collection Methods
All data is collected through `kubectl` commands executed with JSON output format:
- `kubectl get nodes -o json`
- `kubectl get pods -o json`
- `kubectl get services -o json`
- `kubectl top pods -o json` (requires metrics-server)
- `kubectl top nodes -o json` (requires metrics-server)
- `kubectl cluster-info`
- `kubectl version`

The collected data is parsed and structured into Python dataclasses (`NodeInfo`, `PodInfo`, `ServiceInfo`, `ContainerInfo`, `ClusterMetrics`) for easy programmatic access and JSON export.

## 🔧 Advanced Usage

### Programmatic Usage

```python
from kubernetes_monitor import KubernetesMonitor

# Initialize monitor
monitor = KubernetesMonitor()

# Get cluster summary
monitor.print_summary()

# Get detailed information
nodes = monitor.get_nodes()
pods = monitor.get_pods()
services = monitor.get_services()

# Generate comprehensive report
report = monitor.get_comprehensive_report()
monitor.save_report_to_file(report, 'cluster_report.json')
```

### Custom Context and Kubeconfig

```python
# Use specific kubeconfig and context
monitor = KubernetesMonitor(
    kubeconfig_path="/path/to/kubeconfig",
    context="production-cluster"
)
```

### Namespace-specific Monitoring

```python
# Monitor specific namespace
pods = monitor.get_pods("production")
services = monitor.get_services("kube-system")
```

## 📁 Project Structure

```
MoniKube/
├── main.py                    # Main entry point with CLI
├── kubernetes_monitor.py      # Core monitoring class
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🏗️ Architecture

### KubernetesMonitor Class
The core monitoring class that handles:
- Cluster discovery and connection
- Data collection from kubectl commands
- Resource parsing and structuring
- Error handling and logging

### MonitoringController Class
The main controller that handles:
- Command line argument parsing
- Timing and iteration control
- Graceful shutdown handling
- Enhanced console output

### Data Structures
- `ContainerInfo`: Container details
- `PodInfo`: Pod information
- `ServiceInfo`: Service details
- `NodeInfo`: Node information
- `ClusterMetrics`: Overall cluster statistics

## 🔍 Monitoring Output

The tool provides rich console output with:
- 🖥️ **Node Status**: Visual indicators for node health
- 🚀 **Pod Status**: Color-coded pod status summary
- 🌐 **Service Types**: Service breakdown by type
- 📊 **Detailed Metrics**: Total counts and status breakdown
- ⏱️ **Timing Information**: Cycle numbers and timestamps

## 🚨 Error Handling

- Validates command line arguments
- Checks kubectl availability and configuration
- Handles network connectivity issues
- Graceful shutdown on Ctrl+C
- Comprehensive error logging

## 🔧 Configuration

### Prerequisites
1. **kubectl**: Must be installed and configured
2. **Kubernetes Access**: Proper RBAC permissions
3. **metrics-server** (optional): For resource usage monitoring

### Installing metrics-server
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

## 🐛 Troubleshooting

### Common Issues

1. **"No Kubernetes contexts found"**
   - Run: `kubectl config get-contexts`
   - Ensure kubectl is properly configured

2. **"kubectl not found"**
   - Install kubectl and ensure it's in PATH

3. **"Resource usage not available"**
   - Install metrics-server in your cluster

4. **"Permission denied"**
   - Check RBAC permissions for your user/service account

### Debug Mode
Enable debug logging to see detailed command execution:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Enhancements

- **Neo4J Integration**: Send collected metrics to a central Neo4J database
- **Alerting**: Configurable alerts for cluster issues
- **Web Dashboard**: Real-time web interface
- **Historical Data**: Store and analyze trends over time
- **Multi-tenant Support**: Monitor multiple clusters simultaneously

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

---

**MoniKube** - Your comprehensive Kubernetes monitoring solution! 🚀
