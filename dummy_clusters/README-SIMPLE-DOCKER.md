# CYBERNEMO Simple Docker Test Environment

This is a simplified Docker setup for testing your CYBERNEMO Kubernetes monitoring script without the complexity of Docker Compose.

## 🚀 Quick Start

### Option 1: Kubernetes Cluster Only
```bash
# Setup Kubernetes cluster with test applications
./simple-docker-setup.sh

# Run your monitoring script
python3 main.py -n 1
```

### Option 2: With Neo4J Database
```bash
# Terminal 1: Start Neo4J database
./neo4j-docker.sh

# Terminal 2: Setup Kubernetes cluster
./simple-docker-setup.sh

# Terminal 3: Run monitoring with database storage
python3 main.py -db -t 30 -n 5
```

## 🏗️ What's Included

### Kubernetes Cluster (kind)
- **3 nodes**: 1 control-plane + 2 workers
- **Test Applications**:
  - Nginx: 3 replicas
  - Redis: 2 replicas  
  - Busybox: 1 replica
- **All in `test-apps` namespace**

### Neo4J Database (Optional)
- **Web UI**: http://localhost:7474
- **Credentials**: neo4j/password
- **Bolt URI**: bolt://localhost:7687

## 🔧 Usage Examples

### Basic Monitoring
```bash
# Single monitoring cycle
python3 main.py -n 1

# Continuous monitoring (every 30 seconds)
python3 main.py -t 30

# Limited cycles (5 times, every 60 seconds)
python3 main.py -t 60 -n 5
```

### With Database Storage
```bash
# Store data in Neo4J
python3 main.py -db -t 30 -n 5

# Custom Neo4J settings
python3 main.py -db \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-username neo4j \
  --neo4j-password password \
  -t 60 -n 3
```

## 🧹 Cleanup and Stop Clusters

### Stop Kubernetes Cluster
```bash
# Delete the kind cluster
kind delete cluster --name cybernemo-test

# Optional: Clean up Docker resources
docker system prune -f
```

### Stop Neo4J Database
```bash
# Stop and remove Neo4J container
docker stop cybernemo-neo4j && docker rm cybernemo-neo4j

# Optional: Remove Neo4J data volume
docker volume rm $(docker volume ls -q | grep neo4j)
```

### Complete Cleanup
```bash
# Stop everything and clean up
kind delete cluster --name cybernemo-test
docker stop cybernemo-neo4j && docker rm cybernemo-neo4j
docker system prune -f
```

## 🧪 Test Applications

The setup creates several test workloads:

| Application | Replicas | Namespace | Purpose |
|-------------|----------|-----------|---------|
| Nginx | 3 | test-apps | Web server testing |
| Redis | 2 | test-apps | Database testing |
| Busybox | 1 | test-apps | Utility pod testing |

## 🐛 Troubleshooting

### Check Cluster Status
```bash
# View all nodes
kubectl get nodes

# View all pods
kubectl get pods --all-namespaces

# View test applications
kubectl get pods -n test-apps
```

### Check Neo4J Status
```bash
# Check if Neo4J is running
docker ps | grep neo4j

# View Neo4J logs
docker logs cybernemo-neo4j

# Test connection
curl http://localhost:7474
```

### Reset Everything
```bash
# Stop and remove Neo4J
docker stop cybernemo-neo4j && docker rm cybernemo-neo4j

# Delete Kubernetes cluster
kind delete cluster --name cybernemo-test

# Clean up Docker
docker system prune -f
```

## 📊 Expected Output

When running your monitoring script, you should see:

```
🚀 Kubernetes Cluster Monitor
==================================================
✅ Found 1 Kubernetes context(s): kind-cybernemo-test

============================================================
MONITORING CYCLE #1 - 2024-10-24 13:45:30
============================================================

📊 DETAILED STATUS:
   Nodes: 3 total
   Pods: 6 total
   Services: 3 total

🖥️  NODES:
   ✅ cybernemo-test-control-plane (Ready) - Roles: control-plane
   ✅ cybernemo-test-worker (Ready) - Roles: worker
   ✅ cybernemo-test-worker2 (Ready) - Roles: worker

🚀 PODS BY STATUS:
   🟢 Running: 6

🌐 SERVICES BY TYPE:
   📡 ClusterIP: 3
```

## 🎯 Benefits

- ✅ **No Docker Compose issues** - Uses simple Docker commands
- ✅ **Real Kubernetes cluster** - kind provides authentic K8s experience
- ✅ **Lightweight** - Minimal resource usage
- ✅ **Easy cleanup** - Simple commands to remove everything
- ✅ **Optional Neo4J** - Database storage when needed

## 🆘 Support

If you encounter issues:

1. **Check Docker**: `docker info`
2. **Check kind**: `kind version`
3. **Check kubectl**: `kubectl version --client`
4. **View logs**: `docker logs <container-name>`
5. **Reset everything**: Run cleanup commands above

## 📁 File Structure

```
CYBERNEMO/
├── simple-docker-setup.sh    # Kubernetes cluster setup
├── neo4j-docker.sh          # Neo4J database setup
├── README-Simple-Docker.md  # This documentation
├── main.py                  # Your monitoring script
├── kubernetes_monitor.py   # Core monitoring logic
└── neo4j_handler.py        # Database integration
```
