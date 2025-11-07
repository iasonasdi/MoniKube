# Neo4J Schema Documentation

This document describes the complete Neo4J graph database schema used by MoniKube for storing Kubernetes monitoring data.

## Overview

The schema represents a comprehensive graph model of Kubernetes infrastructure, tracking VMs, clusters, nodes, pods, containers, services, and their relationships. It also stores resource usage metrics and cluster-level statistics.

### Schema Overview

| Component | Count | Description |
|-----------|-------|-------------|
| **Node Types** | 8 | VM, Cluster, Node, Pod, Container, Service, ClusterMetrics, ResourceUsage |
| **Relationships** | 5 | HOSTS, CONTAINS (multiple types), HAS_RESOURCE_USAGE |
| **Indexes** | 7 | Performance indexes on key properties |
| **Constraints** | 7 | Uniqueness constraints on all node IDs |

## Node Types

### 1. VM (Virtual Machine)

Represents the physical or virtual machine where the monitoring tool runs.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `vm_{hostname}_{timestamp}`
- `hostname` (String) - Hostname of the VM
- `ip_addresses` (List[String]) - List of IP addresses assigned to the VM
- `platform` (String) - Operating system platform information
- `python_version` (String) - Python version running on the VM
- `timestamp` (String) - ISO timestamp when VM information was first collected
- `last_updated` (DateTime) - Last update timestamp (auto-generated)

**Constraints:**
- UNIQUE constraint on `id`

**Indexes:**
- Index on `id`

---

### 2. Cluster

Represents a Kubernetes cluster.

**Properties:**
- `id` (String, Unique, Indexed) - Unique identifier: `cluster_{context}_{vm_id}`
- `context` (String) - Kubernetes context name
- `vm_id` (String) - Reference to the VM that hosts this cluster
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

**Direction:** `VM` → `Cluster`

**Description:** Indicates that a VM hosts a Kubernetes cluster.

**Properties:** None

**Example:**
```cypher
(vm:VM {id: "vm_hostname_20240101_120000"})-[:HOSTS]->(cluster:Cluster {id: "cluster_default_vm_id"})
```

---

### 2. CONTAINS

**Direction:** `Cluster` → `Node`, `Cluster` → `Pod`, `Cluster` → `Service`

**Description:** Indicates that a cluster contains nodes, pods, or services.

**Properties:** None

**Example:**
```cypher
(cluster:Cluster {id: "cluster_default_vm_id"})-[:CONTAINS]->(node:Node {id: "node_node1_cluster_id"})
(cluster:Cluster {id: "cluster_default_vm_id"})-[:CONTAINS]->(pod:Pod {id: "pod_app1_default_cluster_id"})
(cluster:Cluster {id: "cluster_default_vm_id"})-[:CONTAINS]->(service:Service {id: "service_svc1_default_cluster_id"})
```

---

### 3. HOSTS

**Direction:** `Node` → `Pod`

**Description:** Indicates that a node hosts (runs) a pod.

**Properties:** None

**Example:**
```cypher
(node:Node {id: "node_node1_cluster_id"})-[:HOSTS]->(pod:Pod {id: "pod_app1_default_cluster_id"})
```

---

### 4. CONTAINS

**Direction:** `Pod` → `Container`

**Description:** Indicates that a pod contains a container.

**Properties:** None

**Example:**
```cypher
(pod:Pod {id: "pod_app1_default_cluster_id"})-[:CONTAINS]->(container:Container {id: "container_app_container_pod_app1_default_cluster_id"})
```

---

### 5. HAS_RESOURCE_USAGE

**Direction:** `Cluster` → `ResourceUsage`

**Description:** Links a cluster to its resource usage metrics.

**Properties:** None

**Example:**
```cypher
(cluster:Cluster {id: "cluster_default_vm_id"})-[:HAS_RESOURCE_USAGE]->(ru:ResourceUsage {cluster_id: "cluster_default_vm_id"})
```

---

## Schema Structure Diagram

```
VM
 └─[:HOSTS]→ Cluster
              ├─[:CONTAINS]→ Node
              │   └─[:HOSTS]→ Pod
              │       └─[:CONTAINS]→ Container
              ├─[:CONTAINS]→ Pod
              │   └─[:CONTAINS]→ Container
              ├─[:CONTAINS]→ Service
              └─[:HAS_RESOURCE_USAGE]→ ResourceUsage

ClusterMetrics (related via cluster_id property)
```

## Indexes

All indexes are created for performance optimization:

1. **vm_id_index** - Index on `VM.id`
2. **cluster_id_index** - Index on `Cluster.id`
3. **node_id_index** - Index on `Node.id`
4. **pod_id_index** - Index on `Pod.id`
5. **service_id_index** - Index on `Service.id`
6. **container_id_index** - Index on `Container.id`
7. **resource_usage_cluster_index** - Index on `ResourceUsage.cluster_id`

## Constraints

All constraints enforce uniqueness:

1. **vm_id_unique** - UNIQUE constraint on `VM.id`
2. **cluster_id_unique** - UNIQUE constraint on `Cluster.id`
3. **node_id_unique** - UNIQUE constraint on `Node.id`
4. **pod_id_unique** - UNIQUE constraint on `Pod.id`
5. **service_id_unique** - UNIQUE constraint on `Service.id`
6. **container_id_unique** - UNIQUE constraint on `Container.id`
7. **resource_usage_cluster_unique** - UNIQUE constraint on `ResourceUsage.cluster_id`

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
   - `VM.timestamp`: ISO string format
   - `ResourceUsage.timestamp`: ISO string format
   - All other `timestamp` properties: Neo4J DateTime type (auto-generated)
   - All `last_updated` properties: Neo4J DateTime type (auto-generated)

4. **ID Generation**: All node IDs are generated using a pattern: `{type}_{identifiers}_{cluster_id_or_vm_id}` to ensure uniqueness across the graph.

5. **Relationships**: Relationships are created using `MERGE` to avoid duplicates if the same data is stored multiple times.

## Example Queries

### Get all clusters for a VM
```cypher
MATCH (v:VM {id: $vm_id})-[:HOSTS]->(c:Cluster)
RETURN c.id, c.context, c.timestamp
```

### Get complete infrastructure graph
```cypher
MATCH (v:VM)-[:HOSTS]->(c:Cluster)
OPTIONAL MATCH (c)-[:CONTAINS]->(n:Node)
OPTIONAL MATCH (c)-[:CONTAINS]->(p:Pod)
OPTIONAL MATCH (c)-[:CONTAINS]->(s:Service)
OPTIONAL MATCH (n)-[:HOSTS]->(p)
OPTIONAL MATCH (p)-[:CONTAINS]->(ct:Container)
RETURN v, c, n, p, s, ct
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

