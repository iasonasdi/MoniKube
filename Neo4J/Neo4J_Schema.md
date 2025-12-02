# Neo4J Schema Documentation

This document describes the complete Neo4J graph database schema used by MoniKube for storing Kubernetes monitoring data.

## Overview

The schema represents a comprehensive graph model of Kubernetes infrastructure, tracking Compute Nodes (VMs or physical machines), clusters, nodes, pods, containers, services, and their relationships. It also stores resource usage metrics and cluster-level statistics.

### Schema Overview

| Component | Count | Description |
|-----------|-------|-------------|
| **Node Types** | 14 | ComputeNode, Cluster, Node, Pod, Container, Service, ClusterMetrics, ResourceUsage, DockerContainer, Process, NetworkConnection, ExternalIP, OpenPort, ContainerUser |
| **Relationships** | 9 | HOSTS, CONTAINS, HAS_RESOURCE_USAGE, RUNS_PROCESS, HAS_CONNECTION, CONNECTS_TO, HAS_OPEN_PORT, HAS_USER, PROCESS_USES |
| **Indexes** | 14 | Performance indexes on Kubernetes and Docker entities (including namespace index) |
| **Constraints** | 13 | Uniqueness constraints on all node IDs |

#### Relationship Quick Reference

| Relationship | Direction(s) | Meaning |
|--------------|--------------|---------|
| `HOSTS` | `ComputeNode → Cluster`, `Node → Pod`, `ComputeNode → DockerContainer` | Captures hosting relationships across infrastructure layers. |
| `CONTAINS` | `Cluster → Node/Pod/Service`, `Pod → Container` | Represents hierarchical membership inside the cluster. |
| `HAS_RESOURCE_USAGE` | `Cluster → ResourceUsage` | Links a cluster to the raw metrics snapshot. |
| `RUNS_PROCESS` | `DockerContainer → Process` | Shows which processes run inside each container. |
| `HAS_CONNECTION` | `DockerContainer → NetworkConnection` | Lists network connections initiated within a container. |
| `CONNECTS_TO` | `NetworkConnection → ExternalIP` | Identifies the public IP reached by a connection. |
| `HAS_OPEN_PORT` | `DockerContainer → OpenPort` | Enumerates open/exposed ports for a container. |
| `HAS_USER` | `DockerContainer → ContainerUser` | Maps containers to observed user accounts. |
| `PROCESS_USES` | `Process → NetworkConnection` | Connects a process to the network connections it owns. |

## Node Types

### 1. ComputeNode

Represents the compute node (VM or physical machine) where the monitoring tool runs.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `compute_node_{hostname}_{namespace}`
- `hostname` (String) - Hostname of the compute node
- `ip_addresses` (List[String]) - List of IP addresses assigned to the compute node
- `platform` (String) - Operating system platform information
- `python_version` (String) - Python version running on the compute node
- `node_type` (String) - Type of compute node: `VM` or `Physical`
- `virtualization_type` (String) - Virtualization type if VM: `VMware`, `KVM`, `VirtualBox`, `QEMU`, `Hyper-V`, `Xen`, `Physical`, or `Unknown`
- `namespace` (String, Indexed) - Namespace/organization the compute node belongs to
- `timestamp` (String) - ISO timestamp when compute node information was first collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`
- Index on `namespace`

---

### 2. Cluster

Represents a Kubernetes cluster.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `cluster_{context}_{compute_node_id}`
- `context` (String) - Kubernetes context name
- `compute_node_id` (String) - Reference to the Compute Node that hosts this cluster
- `namespace` (String) - Namespace/organization the cluster belongs to
- `cluster_info` (String/JSON) - JSON string containing cluster information from `kubectl cluster-info` and `kubectl version`
- `available_contexts` (List[String]) - List of all available Kubernetes contexts
- `timestamp` (DateTime) - Timestamp when cluster info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 3. Node

Represents a Kubernetes node (worker or master node).

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `node_{name}_{cluster_id}`
- `name` (String) - Node name
- `status` (String) - Node status (Ready/NotReady/Unknown)
- `roles` (List[String]) - List of node roles (e.g., master, worker, control-plane)
- `cpu_capacity` (String) - Total CPU capacity of the node
- `memory_capacity` (String) - Total memory capacity of the node
- `cpu_allocatable` (String) - CPU available for pods (after system reservations)
- `memory_allocatable` (String) - Memory available for pods (after system reservations)
- `cpu_usage` (Float) - Current CPU usage (from metrics-server if available)
- `memory_usage` (Float) - Current memory usage in MiB (from metrics-server if available)
- `cluster_id` (String) - Reference to the cluster this node belongs to
- `timestamp` (DateTime) - Timestamp when node info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 4. Pod

Represents a Kubernetes pod.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `pod_{name}_{namespace}_{cluster_id}`
- `name` (String) - Pod name
- `namespace` (String) - Kubernetes namespace
- `status` (String) - Pod status (Running, Pending, Failed, Succeeded, Unknown)
- `node` (String) - Node name where the pod is scheduled
- `cpu_requests` (String) - Total CPU requests across all containers (in millicores)
- `memory_requests` (String) - Total memory requests across all containers (in MiB)
- `cpu_limits` (String) - Total CPU limits across all containers (in millicores)
- `memory_limits` (String) - Total memory limits across all containers (in MiB)
- `cluster_id` (String) - Reference to the cluster this pod belongs to
- `timestamp` (DateTime) - Timestamp when pod info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 5. Container

Represents a container within a pod.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `container_{name}_{pod_id}`
- `name` (String) - Container name
- `image` (String) - Container image name and tag
- `status` (String) - Container status (extracted from running state, includes startedAt timestamp)
- `cpu_usage` (Float) - Current CPU usage (from metrics-server if available)
- `memory_usage` (Float) - Current memory usage in MiB (from metrics-server if available)
- `memory_limit` (String, Optional) - Memory limit if configured
- `cpu_limit` (String, Optional) - CPU limit if configured
- `pod_id` (String) - Reference to the pod this container belongs to
- `timestamp` (DateTime) - Timestamp when container info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 6. Service

Represents a Kubernetes service.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `service_{name}_{namespace}_{cluster_id}`
- `name` (String) - Service name
- `namespace` (String) - Kubernetes namespace
- `type` (String) - Service type (ClusterIP, NodePort, LoadBalancer, ExternalName)
- `cluster_ip` (String) - Cluster IP address
- `external_ip` (String, Optional) - External IP address (for LoadBalancer services)
- `ports` (String/JSON) - JSON string containing port configurations (name, port, target_port, protocol)
- `selector` (String/JSON) - JSON string containing label selectors used to match pods
- `cluster_id` (String) - Reference to the cluster this service belongs to
- `timestamp` (DateTime) - Timestamp when service info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 7. ClusterMetrics

Represents aggregated cluster-level metrics.

**Properties:**
- `cluster_id` (String, Unique) - Reference to the cluster (used as identifier)
- `total_pods` (Integer) - Total number of pods in the cluster
- `running_pods` (Integer) - Number of running pods
- `pending_pods` (Integer) - Number of pending pods
- `failed_pods` (Integer) - Number of failed pods
- `total_services` (Integer) - Total number of services
- `total_nodes` (Integer) - Total number of nodes
- `ready_nodes` (Integer) - Number of ready nodes
- `total_cpu_usage` (Float) - Total CPU usage across cluster (from metrics-server if available)
- `total_memory_usage` (Float) - Total memory usage across cluster (from metrics-server if available)
- `timestamp` (DateTime) - Timestamp when metrics were collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `cluster_id`

---

### 8. ResourceUsage
### 9. DockerContainer

Represents a Docker container discovered by the security monitoring component.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `docker_{container_id[:12]}_{compute_node_id}`
- `name` (String) - Container name
- `container_id` (String) - Full Docker container ID
- `image` (String) - Image name and tag
- `status` (String) - Container runtime status
- `compute_node_id` (String) - Reference to Compute Node hosting the container
- `namespace` (String) - Namespace/organization the container belongs to
- `timestamp` (DateTime) - Timestamp when container info was first collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 10. Process

Represents a process running inside a Docker container.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `process_{pid}_{docker_container_id}`
- `pid` (Integer) - Process ID
- `user` (String) - Username running the process
- `cpu_percent` (Float) - CPU usage percentage
- `memory_percent` (Float) - Memory usage percentage
- `memory_kb` (Float) - Memory consumption in KB
- `command` (String) - Command line (trimmed to 500 chars)
- `start_time` (String) - Process start time
- `container_id` (String) - Reference to parent Docker container
- `timestamp` (DateTime) - Timestamp when process info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 11. NetworkConnection

Represents a network connection made by a process inside a Docker container.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier built from protocol, endpoints, and container
- `protocol` (String) - Protocol (TCP/UDP/etc.)
- `local_address` (String) - Local IP address
- `local_port` (Integer) - Local port
- `remote_address` (String) - Remote IP address
- `remote_port` (Integer) - Remote port
- `state` (String) - Connection state
- `process_name` (String) - Name of owning process
- `pid` (Integer, Optional) - Process ID (if known)
- `container_id` (String) - Reference to parent Docker container
- `timestamp` (DateTime) - Timestamp when connection info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 12. ExternalIP

Represents an external IP that a container connects to.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `ip_{address}`
- `address` (String) - IP address
- `is_private` (Boolean) - Indicates if IP is private (defaults to false)
- `timestamp` (DateTime) - Timestamp when IP was first recorded
- `last_seen` (DateTime) - Last time the IP was observed

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 13. OpenPort

Represents an open port exposed by a Docker container.

**Properties:**
- `id` (String, Unique, Indexed) - `port_{protocol}_{port}_{docker_container_id}`
- `protocol` (String) - Protocol (TCP/UDP/etc.)
- `address` (String) - IP address bound to the port
- `port` (Integer) - Port number
- `state` (String) - Port state
- `container_id` (String) - Reference to parent Docker container
- `timestamp` (DateTime) - Timestamp when port info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 14. ContainerUser

Represents a user account observed inside a Docker container.

**Properties:**
- `id` (String, Unique, Indexed) - `user_{username}_{docker_container_id}`
- `username` (String) - Username inside the container
- `container_id` (String) - Reference to parent Docker container
- `timestamp` (DateTime) - Timestamp when user info was collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

Stores raw resource usage data from metrics-server.

**Properties:**
- `cluster_id` (String, Unique, Indexed) - Reference to the cluster (used as identifier)
- `pod_metrics` (String/JSON) - JSON string containing raw pod metrics from `kubectl top pods`
- `node_metrics` (String/JSON) - JSON string containing raw node metrics from `kubectl top nodes`
- `timestamp` (String) - ISO timestamp when metrics were collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `cluster_id`

**Indexes:**
- Index on `cluster_id`

---

## Relationships

### 1. HOSTS

**Directions:**
- `ComputeNode` → `Cluster`
- `Node` → `Pod`
- `ComputeNode` → `DockerContainer`

**Description:** Same relationship type reused to indicate hosting at different infrastructure layers.

**Properties:** None

**Example:**
```cypher
(cn:ComputeNode {id: "compute_node_hostname_default"})-[:HOSTS]->(cluster:Cluster {id: "cluster_default_compute_node_hostname_default"})
(node:Node {id: "node_node1_cluster_id"})-[:HOSTS]->(pod:Pod {id: "pod_app1_default_cluster_id"})
(cn:ComputeNode {id: "compute_node_hostname_default"})-[:HOSTS]->(dc:DockerContainer {id: "docker_cid_compute_node_hostname_default"})
```

---

### 2. CONTAINS

**Directions:**
- `Cluster` → `Node`
- `Cluster` → `Pod`
- `Cluster` → `Service`
- `Pod` → `Container`

**Description:** Indicates hierarchical containment within the Kubernetes cluster.

**Properties:** None

**Example:**
```cypher
(cluster:Cluster {id: "cluster_default_compute_node_id"})-[:CONTAINS]->(node:Node {id: "node_node1_cluster_id"})
(cluster)-[:CONTAINS]->(pod:Pod {id: "pod_app1_default_cluster_id"})
(cluster)-[:CONTAINS]->(service:Service {id: "service_svc1_default_cluster_id"})
(pod:Pod {id: "pod_app1_default_cluster_id"})-[:CONTAINS]->(container:Container {id: "container_app_container_pod_app1_default_cluster_id"})
```

---

### 3. HAS_RESOURCE_USAGE

**Direction:** `Cluster` → `ResourceUsage`

**Description:** Links a cluster to its raw metrics-server snapshot.

**Properties:** None

**Example:**
```cypher
(cluster:Cluster {id: "cluster_default_compute_node_id"})-[:HAS_RESOURCE_USAGE]->(ru:ResourceUsage {cluster_id: "cluster_default_compute_node_id"})
```

---

### 4. RUNS_PROCESS

**Direction:** `DockerContainer` → `Process`

**Description:** Associates each Docker container with the processes observed inside it.

**Properties:** None

**Example:**
```cypher
(dc:DockerContainer {id: "docker_cid_compute_node"})-[:RUNS_PROCESS]->(pr:Process {id: "process_123_docker_cid_compute_node"})
```

---

### 5. HAS_CONNECTION

**Direction:** `DockerContainer` → `NetworkConnection`

**Description:** Captures network connections initiated within a container.

**Properties:** None

**Example:**
```cypher
(dc:DockerContainer {id: "docker_cid_compute_node"})-[:HAS_CONNECTION]->(nc:NetworkConnection {id: "conn_tcp_10.0.0.1_80_8.8.8.8_443_docker_cid_compute_node"})
```

---

### 6. CONNECTS_TO

**Direction:** `NetworkConnection` → `ExternalIP`

**Description:** Records which external IPs are contacted by a given connection (only for public IPs).

**Properties:** None

**Example:**
```cypher
(nc:NetworkConnection {id: "conn_tcp..."})-[:CONNECTS_TO]->(eip:ExternalIP {id: "ip_8.8.8.8"})
```

---

### 7. HAS_OPEN_PORT

**Direction:** `DockerContainer` → `OpenPort`

**Description:** Lists ports exposed by a container.

**Properties:** None

**Example:**
```cypher
(dc:DockerContainer {id: "docker_cid_compute_node"})-[:HAS_OPEN_PORT]->(op:OpenPort {id: "port_tcp_443_docker_cid_compute_node"})
```

---

### 8. HAS_USER

**Direction:** `DockerContainer` → `ContainerUser`

**Description:** Maps containers to user accounts discovered within them.

**Properties:** None

**Example:**
```cypher
(dc:DockerContainer {id: "docker_cid_compute_node"})-[:HAS_USER]->(cu:ContainerUser {id: "user_root_docker_cid_compute_node"})
```

---

### 9. PROCESS_USES

**Direction:** `Process` → `NetworkConnection`

**Description:** Connects a process to the network connections it owns (when PID mapping is available).

**Properties:** None

**Example:**
```cypher
(pr:Process {id: "process_123_docker_cid_compute_node"})-[:PROCESS_USES]->(nc:NetworkConnection {id: "conn_tcp..."})
```

---

## Schema Structure Diagram

```
ComputeNode
 ├─[:HOSTS]→ Cluster
 │            ├─[:CONTAINS]→ Node
 │            │   └─[:HOSTS]→ Pod
 │            │       └─[:CONTAINS]→ Container
 │            ├─[:CONTAINS]→ Pod
 │            ├─[:CONTAINS]→ Service
 │            └─[:HAS_RESOURCE_USAGE]→ ResourceUsage
 │
 │ ClusterMetrics (linked via shared cluster_id property, no explicit relationship)
 │
 └─[:HOSTS]→ DockerContainer
              ├─[:RUNS_PROCESS]→ Process
              │                   └─[:PROCESS_USES]→ NetworkConnection
              │                                         └─[:CONNECTS_TO]→ ExternalIP
              ├─[:HAS_CONNECTION]→ NetworkConnection
              ├─[:HAS_OPEN_PORT]→ OpenPort
              └─[:HAS_USER]→ ContainerUser
```

## Indexes

All indexes are created for performance optimization:

1. **compute_node_id_index** - Index on `ComputeNode.id`
2. **compute_node_namespace_index** - Index on `ComputeNode.namespace`
3. **cluster_id_index** - Index on `Cluster.id`
4. **node_id_index** - Index on `Node.id`
5. **pod_id_index** - Index on `Pod.id`
6. **service_id_index** - Index on `Service.id`
7. **container_id_index** - Index on `Container.id`
8. **resource_usage_cluster_index** - Index on `ResourceUsage.cluster_id`
9. **docker_container_id_index** - Index on `DockerContainer.id`
10. **process_id_index** - Index on `Process.id`
11. **network_connection_id_index** - Index on `NetworkConnection.id`
12. **external_ip_id_index** - Index on `ExternalIP.id`
13. **open_port_id_index** - Index on `OpenPort.id`
14. **container_user_id_index** - Index on `ContainerUser.id`

## Constraints

All constraints enforce uniqueness:

1. **compute_node_id_unique** - UNIQUE constraint on `ComputeNode.id`
2. **cluster_id_unique** - UNIQUE constraint on `Cluster.id`
3. **node_id_unique** - UNIQUE constraint on `Node.id`
4. **pod_id_unique** - UNIQUE constraint on `Pod.id`
5. **service_id_unique** - UNIQUE constraint on `Service.id`
6. **container_id_unique** - UNIQUE constraint on `Container.id`
7. **resource_usage_cluster_unique** - UNIQUE constraint on `ResourceUsage.cluster_id`
8. **docker_container_id_unique** - UNIQUE constraint on `DockerContainer.id`
9. **process_id_unique** - UNIQUE constraint on `Process.id`
10. **network_connection_id_unique** - UNIQUE constraint on `NetworkConnection.id`
11. **external_ip_id_unique** - UNIQUE constraint on `ExternalIP.id`
12. **open_port_id_unique** - UNIQUE constraint on `OpenPort.id`
13. **container_user_id_unique** - UNIQUE constraint on `ContainerUser.id`

## Data Types

- **String**: Text values
- **Integer**: Whole numbers
- **Float**: Decimal numbers
- **List[String]**: Array of strings
- **DateTime**: Neo4J datetime type (auto-generated)
- **String/JSON**: JSON data stored as string (for complex nested structures)

## Notes

1. **Resource Usage Metrics**: The `cpu_usage` and `memory_usage` fields in `Node` and `Container` nodes are populated from metrics-server data when available. If metrics-server is not installed, these fields default to `0.0`.

2. **JSON Storage**: Some properties like `cluster_info`, `ports`, `selector`, `pod_metrics`, and `node_metrics` are stored as JSON strings. These need to be parsed when querying.

3. **Timestamps**: The `timestamp` property varies in type:
   - `ComputeNode.timestamp`: ISO string format
   - `ResourceUsage.timestamp`: ISO string format
   - All other `timestamp` properties: Neo4J DateTime type (auto-generated)
   - All `last_updated` properties: Neo4J DateTime type (auto-generated)

4. **ID Generation**: All node IDs follow `{type}_{identifiers}_{cluster_id_or_compute_node_id}` (Docker objects include truncated container IDs) to ensure uniqueness across the graph.

5. **Compute Node Detection**: The `node_type` field is automatically detected using multiple methods:
   - `systemd-detect-virt` command (most reliable)
   - DMI product name (`/sys/class/dmi/id/product_name`)
   - DMI system vendor (`/sys/class/dmi/id/sys_vendor`)
   - CPU info hypervisor flags (`/proc/cpuinfo`)
   - If none of these indicate virtualization, the node is marked as `Physical`

6. **Namespace Support**: All compute nodes, clusters, and Docker containers include a `namespace` field for organizational grouping. Namespace can be set via environment variables (`KUBERNETES_NAMESPACE` or `NAMESPACE`) or defaults to `default`.

5. **Relationships**: Relationships are created using `MERGE` to avoid duplicates if the same data is stored multiple times. The `HOSTS` and `CONTAINS` relationship types are deliberately reused across multiple entity pairs for readability.

6. **Cluster Metrics Linking**: `ClusterMetrics` nodes are keyed by `cluster_id` but currently have no explicit relationship; consumers should join them via the shared property.

## Example Queries

### Get all clusters for a Compute Node
```cypher
MATCH (cn:ComputeNode {id: $compute_node_id})-[:HOSTS]->(c:Cluster)
RETURN c.id, c.context, c.namespace, c.timestamp
```

### Get all Compute Nodes in a namespace
```cypher
MATCH (cn:ComputeNode {namespace: $namespace})
RETURN cn.id, cn.hostname, cn.node_type, cn.virtualization_type
```

### Get complete infrastructure graph
```cypher
MATCH (cn:ComputeNode)-[:HOSTS]->(c:Cluster)
OPTIONAL MATCH (c)-[:CONTAINS]->(n:Node)
OPTIONAL MATCH (c)-[:CONTAINS]->(p:Pod)
OPTIONAL MATCH (c)-[:CONTAINS]->(s:Service)
OPTIONAL MATCH (n)-[:HOSTS]->(p)
OPTIONAL MATCH (p)-[:CONTAINS]->(ct:Container)
RETURN cn, c, n, p, s, ct
```

### Get all VMs vs Physical machines
```cypher
MATCH (cn:ComputeNode)
RETURN cn.node_type, count(cn) as count
ORDER BY count DESC
```

### Get pods with high CPU usage
```cypher
MATCH (p:Pod)-[:CONTAINS]->(ct:Container)
WHERE ct.cpu_usage > 0.5
RETURN p.name, p.namespace, ct.name, ct.cpu_usage
ORDER BY ct.cpu_usage DESC
```

### Get resource usage for a cluster
```cypher
MATCH (c:Cluster {id: $cluster_id})-[:HAS_RESOURCE_USAGE]->(ru:ResourceUsage)
RETURN ru.pod_metrics, ru.node_metrics, ru.timestamp
```

