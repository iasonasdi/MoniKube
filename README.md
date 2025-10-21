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
```

### Command Line Options

- `-t, --time`: Time interval between monitoring cycles in seconds (default: 10)
- `-n, --iterations`: Number of monitoring cycles to run (0 = continuous, default: 0)

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

### Cluster Information
- Available contexts and cluster versions
- Basic cluster connectivity and status

### Nodes
- Node status (Ready/NotReady)
- Node roles (master, worker, etc.)
- CPU and memory capacity
- Resource allocation

### Pods
- Pod status (Running, Pending, Failed, etc.)
- Container information (name, image, status)
- Resource requests and limits
- Node assignment

### Services
- Service types (ClusterIP, NodePort, LoadBalancer)
- Cluster and external IPs
- Port configurations
- Service selectors

### System Metrics (with metrics-server)
- CPU usage per pod and node
- Memory usage per pod and node
- Resource utilization trends

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
