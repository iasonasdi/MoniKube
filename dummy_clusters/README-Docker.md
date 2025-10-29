# CYBERNEMO Docker Test Environment

This directory contains multiple Docker-based testing approaches for the CYBERNEMO Kubernetes monitoring script.

## 🚀 Choose Your Approach

### Option 1: Simple Setup (Recommended)
**Use this if you have Docker Compose issues**

```bash
# Setup Kubernetes cluster with test applications
./simple-docker-setup.sh

# Run your monitoring script
cd .. && python3 main.py -n 1

[...]
# Clean up when done
kind delete cluster --name cybernemo-test
```

### Option 2: Docker Compose Setup
**Use this if Docker Compose works on your system**

```bash
# Start the test environment
./setup-cluster.sh

# Run the monitoring script
docker-compose up monitor

[...]
# Clean up when done
docker-compose down -v
```

## 📁 Available Scripts

| Script | Purpose | Requirements |
|--------|---------|--------------|
| `simple-docker-setup.sh` | Kubernetes cluster with kind | Docker only |
| `neo4j-docker.sh` | Neo4J database (optional) | Docker only |
| `setup-cluster.sh` | Full Docker Compose setup | Docker + Docker Compose |

## 🏗️ What's Included

### Kubernetes Cluster
- **kind cluster**: 3 nodes (1 control-plane + 2 workers)
- **Test Applications**: Nginx, Redis, Busybox deployments
- **Real Kubernetes API**: Authentic K8s experience

### Neo4J Database (Optional)
- **Web UI**: http://localhost:7474 (neo4j/password)
- **Bolt URI**: bolt://localhost:7687
- **Data Storage**: For monitoring metrics and topology

## 🏗️ Architecture

The Docker setup includes:

- **Neo4J Database** (port 7474/7687): Stores monitoring data
- **K3s Kubernetes Cluster**: Lightweight Kubernetes for testing
- **CYBERNEMO Monitor**: Your monitoring application
- **Test Applications**: Nginx, Redis, and Busybox deployments

## 📊 Services

| Service | Port | Description |
|---------|------|-------------|
| Neo4J HTTP | 7474 | Web interface (neo4j/password) |
| Neo4J Bolt | 7687 | Database connection |
| Kubernetes API | 6443 | K3s API server |
| K3s API | 8080 | K3s HTTP API |

## 🧪 Test Applications

The setup includes several test deployments:

- **Nginx Deployment**: 3 replicas with service
- **Redis Deployment**: 2 replicas with service  
- **Busybox Deployment**: 1 replica with service

## 🔧 Usage Examples

### Basic Monitoring
```bash
# Run monitoring once
docker-compose run --rm monitor python3 main.py -n 1

# Run monitoring continuously
docker-compose run --rm monitor python3 main.py -t 30
```

### With Database Storage
```bash
# Store data in Neo4J
docker-compose run --rm monitor python3 main.py -db -t 30 -n 5
```

### Custom Configuration
```bash
# Custom Neo4J settings
docker-compose run --rm monitor python3 main.py -db \
  --neo4j-uri bolt://neo4j:7687 \
  --neo4j-username neo4j \
  --neo4j-password password \
  -t 60 -n 3
```

## 🧹 Cleanup and Stop Clusters

### Simple Setup Cleanup
```bash
# Stop and delete the Kubernetes cluster
kind delete cluster --name cybernemo-test

# Optional: Clean up Docker resources
docker system prune -f
```

### Docker Compose Cleanup
```bash
# Stop all services and remove volumes
docker-compose down -v

# Optional: Remove all containers and images
docker-compose down --rmi all --volumes --remove-orphans

# Optional: Clean up Docker resources
docker system prune -f
```

### Neo4J Cleanup (if used separately)
```bash
# Stop and remove Neo4J container
docker stop cybernemo-neo4j && docker rm cybernemo-neo4j

# Optional: Remove Neo4J data volume
docker volume rm $(docker volume ls -q | grep neo4j)
```

## 🐛 Troubleshooting

### Cluster Not Ready
```bash
# Check K3s status
docker exec cybernemo-k3s kubectl get nodes

# Check pods
docker exec cybernemo-k3s kubectl get pods --all-namespaces
```

### Neo4J Connection Issues
```bash
# Check Neo4J logs
docker logs cybernemo-neo4j

# Test connection
docker exec cybernemo-monitor python3 -c "
from neo4j_handler import Neo4JHandler
handler = Neo4JHandler('bolt://neo4j:7687', 'neo4j', 'password')
print('Connected!' if handler.connect() else 'Failed!')
"
```

### Reset Everything
```bash
# Stop and remove all containers/volumes
docker-compose down -v
docker system prune -f

# Restart setup
./setup-cluster.sh
```

## 📁 File Structure

```
dummy_clusters/
├── simple-docker-setup.sh     # Simple Kubernetes setup (recommended)
├── neo4j-docker.sh           # Neo4J database setup
├── README-Simple-Docker.md   # Simple setup documentation
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # CYBERNEMO application container
├── setup-cluster.sh          # Docker Compose setup script
├── k8s-manifests/            # Kubernetes test deployments
│   ├── nginx-deployment.yaml
│   ├── redis-deployment.yaml
│   └── busybox-deployment.yaml
├── logs/                     # Application logs (created automatically)
├── kubeconfig/              # Kubernetes config (created automatically)
└── README-Docker.md         # This file
```

## 🔍 Monitoring Data

The monitoring script will collect:
- Node information and status
- Pod details and health
- Service configurations
- Resource usage metrics
- Cluster topology (if Neo4J enabled)

## 🎯 Next Steps

1. **Customize Deployments**: Modify `k8s-manifests/*.yaml` files
2. **Add More Tests**: Create additional Kubernetes resources
3. **Scale Testing**: Increase replica counts for load testing
4. **Network Testing**: Add network policies and ingress controllers
5. **Storage Testing**: Add persistent volumes and storage classes

## 🆘 Support

If you encounter issues:
1. Check Docker logs: `docker logs <container-name>`
2. Verify cluster status: `docker exec cybernemo-k3s kubectl get all`
3. Test Neo4J connection: Visit http://localhost:7474
4. Review the main README.md for application-specific help
