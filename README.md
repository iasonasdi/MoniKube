# MoniKube

`Last Updated: 2/12/2025`

A comprehensive Kubernetes distributed monitoring tool that monitors all clusters deployed on compute nodes (VMs or physical machines) and collects data, stats, and system metrics.

## 🚀 Features

- **Multi-Cluster Monitoring**: Automatically discover and monitor multiple Kubernetes clusters
- **Docker Container Monitoring**: Monitor Docker containers running on the host with security-focused data collection
- **Real-time Monitoring**: Continuous monitoring with customizable intervals
- **Comprehensive Data Collection**: 
  - Cluster information and versions
  - Node status, roles, and resource capacity
  - Pod status, containers, and resource usage
  - Service discovery and configuration
  - System metrics (CPU, RAM) when metrics-server is available
  - Docker container processes, network connections, and external IPs
- **Flexible Execution**: Run once, limited iterations, or continuously
- **Rich Console Output**: Visual status indicators and detailed reporting
- **Neo4J Integration**: Store all monitoring data in Neo4J graph database
- **Web Visualization**: Interactive graph visualization of infrastructure
- **JSON Reporting**: Export comprehensive reports for further analysis
- **Object-Oriented Design**: Easy to extend and customize

## 📋 Requirements

- Python 3.7+
- kubectl installed and configured
- Access to Kubernetes clusters
- Docker installed (for Docker container monitoring, optional)
- metrics-server (optional, for resource usage monitoring)
- Neo4J database (optional, for data storage and visualization)

## 🛠️ Installation

1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Quick Start

### Automated Setup (Recommended)

Use `main.sh` to automatically ensure the kind cluster exists before running monitoring:

```bash
# Run with automatic kind cluster setup
./main.sh -db -t 60 -n 1

# All main.py arguments work with main.sh
./main.sh -db -t 30 -n 5

# Disable Docker monitoring
./main.sh -db -t 30 -n 5 --no-docker
```

The script will:
- Check if kind cluster exists
- Create it if it doesn't exist
- Wait for cluster to be ready
- Then run main.py with your arguments

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

# Run with Docker monitoring disabled
python3 main.py -db -t 30 -n 5 --no-docker
```

### Command Line Options

- `-t, --time`: Time interval between monitoring cycles in seconds (default: 10)
- `-n, --iterations`: Number of monitoring cycles to run (0 = continuous, default: 0)
- `-db, --database`: Enable Neo4J database storage
- `--neo4j-uri URI`: Neo4J database URI (default: bolt://localhost:7687)
- `--neo4j-username USERNAME`: Neo4J username (default: neo4j)
- `--neo4j-password PASSWORD`: Neo4J password (default: password)
- `--neo4j-database DATABASE`: Neo4J database name (default: neo4j)
- `--no-docker`: Disable Docker container monitoring (enabled by default)

### Examples

```bash
# Continuous monitoring every 5 seconds
python main.py -t 5

# Run 5 monitoring cycles, every 30 seconds
python main.py -t 30 -n 5

# Single report
python main.py -n 1

# Run with Docker monitoring disabled
python main.py --no-docker

# Run with Neo4J and custom connection
python main.py -db --neo4j-uri bolt://neo4j-server:7687 --neo4j-username admin --neo4j-password secret

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

### 7. Docker Container Monitoring
**Note**: Docker monitoring is enabled by default. Use `--no-docker` to disable it.

For each running Docker container, the following security-focused data is collected:

**Container-Level Data:**
- **Container ID**: Full Docker container ID
- **Container Name**: Container name
- **Image**: Docker image name and tag
- **Status**: Container status

**Process Information:**
- **Top Processes**: Top 20 processes by CPU usage
  - Process ID (PID)
  - User running the process
  - CPU usage percentage
  - Memory usage percentage and KB
  - Command line
  - Start time

**Network Security:**
- **Network Connections**: All active network connections
  - Protocol (TCP/UDP)
  - Local address and port
  - Remote address and port
  - Connection state
  - Associated process (if available)
- **External IPs**: List of all external IP addresses the container communicates with
  - Automatically filters out private IP ranges (10.x.x.x, 172.16.x.x, 192.168.x.x)
  - Tracks external communication for security analysis
- **Open Ports**: All listening ports in the container
  - Protocol
  - Bind address
  - Port number
  - Port state

**User Information:**
- **Container Users**: List of all user accounts in the container
  - Extracted from `/etc/passwd`
  - Currently logged in users

**Security Benefits:**
- Identify suspicious network connections
- Track external communication patterns
- Monitor process activity
- Detect unauthorized access
- Analyze container security posture

### Data Collection Methods

**Kubernetes Data:**
All Kubernetes data is collected through `kubectl` commands executed with JSON output format:
- `kubectl get nodes -o json`
- `kubectl get pods -o json`
- `kubectl get services -o json`
- `kubectl top pods -o json` (requires metrics-server)
- `kubectl top nodes -o json` (requires metrics-server)
- `kubectl cluster-info`
- `kubectl version`

**Docker Data:**
Docker container data is collected through Docker commands executed inside containers:
- `docker ps` - List all running containers
- `docker exec <container> ps aux` - Get process information
- `docker exec <container> ss -tunap` - Get network connections
- `docker exec <container> netstat -tunap` - Fallback for network connections
- `docker exec <container> ss -tuln` - Get open ports
- `docker exec <container> cat /etc/passwd` - Get user accounts
- `docker exec <container> who` - Get logged in users

The collected data is parsed and structured into Python dataclasses for easy programmatic access and JSON export.

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

The monitoring system uses structured dataclasses to represent all collected data. Here's a comprehensive overview:

| Data Structure | Source | Description | Key Properties |
|----------------|--------|-------------|----------------|
| **Kubernetes Monitoring** |
| `ContainerInfo` | Kubernetes Pods | Container within a Kubernetes pod | `name`, `image`, `status`, `cpu_usage`, `memory_usage`, `cpu_limit`, `memory_limit` |
| `PodInfo` | Kubernetes API | Kubernetes pod information | `name`, `namespace`, `status`, `node`, `containers[]`, `cpu_requests`, `memory_requests`, `cpu_limits`, `memory_limits` |
| `ServiceInfo` | Kubernetes API | Kubernetes service configuration | `name`, `namespace`, `type`, `cluster_ip`, `external_ip`, `ports[]`, `selector{}` |
| `NodeInfo` | Kubernetes API | Kubernetes node information | `name`, `status`, `roles[]`, `cpu_capacity`, `memory_capacity`, `cpu_allocatable`, `memory_allocatable`, `cpu_usage`, `memory_usage` |
| `ClusterMetrics` | Aggregated | Overall cluster statistics | `total_pods`, `running_pods`, `pending_pods`, `failed_pods`, `total_services`, `total_nodes`, `ready_nodes`, `total_cpu_usage`, `total_memory_usage` |
| **Docker Container Monitoring** |
| `ProcessInfo` | Docker Container | Process running inside container | `pid`, `user`, `cpu_percent`, `memory_percent`, `memory_kb`, `command`, `start_time` |
| `NetworkConnection` | Docker Container | Network connection from container | `protocol`, `local_address`, `local_port`, `remote_address`, `remote_port`, `state`, `process_name`, `pid` |
| `ContainerSecurityInfo` | Docker Container | Complete security profile | `container_id`, `container_name`, `image`, `status`, `processes[]`, `network_connections[]`, `external_ips{}`, `open_ports[]`, `users{}`, `timestamp` |

**Data Relationships:**
- **Kubernetes**: `Cluster` → `Node` → `Pod` → `Container`
- **Docker**: `ComputeNode` → `DockerContainer` → `Process`, `NetworkConnection`, `OpenPort`, `ContainerUser`
- **Network**: `NetworkConnection` → `ExternalIP`
- **Process**: `Process` → `NetworkConnection` (when process info available)

## 🔍 Monitoring Output

The tool provides rich console output with:
- 🖥️ **Node Status**: Visual indicators for node health
- 🚀 **Pod Status**: Color-coded pod status summary
- 🌐 **Service Types**: Service breakdown by type
- 🐳 **Docker Containers**: Container summary with process and network information
- 📊 **Detailed Metrics**: Total counts and status breakdown
- ⏱️ **Timing Information**: Cycle numbers and timestamps
- 🔒 **Security Data**: External IPs, open ports, and process information for Docker containers

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
3. **Docker**: Must be installed and running (for Docker container monitoring)
4. **metrics-server** (optional): For resource usage monitoring
5. **Neo4J** (optional): For data storage and visualization

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

5. **"Docker command not found"**
   - Install Docker and ensure it's running
   - Ensure your user has permission to run `docker ps` and `docker exec`
   - Use `--no-docker` to disable Docker monitoring if not needed

6. **"Failed to execute command in container"**
   - Some containers may not have required tools (ps, ss, netstat)
   - This is normal and the tool will gracefully handle missing commands

### Debug Mode
Enable debug logging to see detailed command execution:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Enhancements

- **Alerting**: Configurable alerts for cluster issues and security events
- **Historical Data**: Store and analyze trends over time
- **Multi-tenant Support**: Monitor multiple clusters simultaneously
- **Container Image Scanning**: Security vulnerability scanning for container images
- **Network Flow Analysis**: Deep packet inspection and flow analysis
- **Anomaly Detection**: Machine learning-based anomaly detection for security threats

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

---

**MoniKube** - Your comprehensive Kubernetes monitoring solution! 🚀
