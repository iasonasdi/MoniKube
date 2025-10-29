#!/bin/bash

# Simple Docker Setup for CYBERNEMO Kubernetes Testing
# This script creates a minimal Kubernetes cluster using kind (Kubernetes in Docker)

set -e

echo "🚀 Setting up Simple CYBERNEMO Kubernetes Test Environment"
echo "=========================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is available"

# Install kind if not available
if ! command -v kind &> /dev/null; then
    echo "📦 Installing kind (Kubernetes in Docker)..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
    echo "✅ kind installed"
else
    echo "✅ kind is already available"
fi

# Create kind cluster
echo "🏗️  Creating Kubernetes cluster with kind..."
kind create cluster --name cybernemo-test --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF

echo "✅ Kubernetes cluster created with 3 nodes (1 control-plane, 2 workers)"

# Wait for cluster to be ready
echo "⏳ Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Deploy test applications
echo "🚀 Deploying test applications..."

# Create namespace
kubectl create namespace test-apps

# Deploy nginx
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: test-apps
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  namespace: test-apps
spec:
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: ClusterIP
EOF

# Deploy redis
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-deployment
  namespace: test-apps
  labels:
    app: redis
spec:
  replicas: 2
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: test-apps
spec:
  selector:
    app: redis
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
  type: ClusterIP
EOF

# Deploy busybox
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: busybox-deployment
  namespace: test-apps
  labels:
    app: busybox
spec:
  replicas: 1
  selector:
    matchLabels:
      app: busybox
  template:
    metadata:
      labels:
        app: busybox
    spec:
      containers:
      - name: busybox
        image: busybox:latest
        command: ['sh', '-c', 'while true; do echo "Hello from busybox!"; sleep 30; done']
        resources:
          requests:
            memory: "32Mi"
            cpu: "100m"
          limits:
            memory: "64Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: busybox-service
  namespace: test-apps
spec:
  selector:
    app: busybox
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
  type: ClusterIP
EOF

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available deployment --all -n test-apps --timeout=300s

# Show cluster status
echo ""
echo "📊 Cluster Status:"
echo "=================="
kubectl get nodes
echo ""
kubectl get pods -n test-apps
echo ""
kubectl get services -n test-apps

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Your Kubernetes cluster is ready with:"
echo "   - 3 nodes (1 control-plane, 2 workers)"
echo "   - Nginx deployment (3 replicas)"
echo "   - Redis deployment (2 replicas)"
echo "   - Busybox deployment (1 replica)"
echo ""
echo "🔧 To test your monitoring script:"
echo "   python3 main.py -n 1"
echo ""
echo "🧪 To run continuous monitoring:"
echo "   python3 main.py -t 30"
echo ""
echo "🛑 To clean up:"
echo "   kind delete cluster --name cybernemo-test"
