#!/bin/bash

# CYBERNEMO Kubernetes Test Cluster Setup Script
# This script sets up a local Kubernetes cluster for testing the monitoring script

set -e

echo "🚀 Setting up CYBERNEMO Kubernetes Test Environment"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create necessary directories
mkdir -p logs
mkdir -p kubeconfig

echo "📁 Created necessary directories"

# Start the services
echo "🐳 Starting Docker services..."
docker-compose up -d neo4j k3s-server

echo "⏳ Waiting for services to be ready..."
sleep 30

# Wait for K3s to be ready
echo "🔄 Waiting for K3s cluster to be ready..."
timeout=60
counter=0
while ! docker exec cybernemo-k3s kubectl get nodes > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Timeout waiting for K3s to be ready"
        exit 1
    fi
    echo "   Waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

echo "✅ K3s cluster is ready!"

# Copy kubeconfig from K3s container
echo "📋 Copying kubeconfig..."
docker cp cybernemo-k3s:/tmp/kubeconfig ./kubeconfig/config

# Deploy test applications
echo "🚀 Deploying test applications..."
docker exec cybernemo-k3s kubectl apply -f /var/lib/rancher/k3s/server/manifests/

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
sleep 20

# Show cluster status
echo "📊 Cluster Status:"
docker exec cybernemo-k3s kubectl get nodes
docker exec cybernemo-k3s kubectl get pods
docker exec cybernemo-k3s kubectl get services

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Available services:"
echo "   - Neo4J Database: http://localhost:7474 (neo4j/password)"
echo "   - Kubernetes API: https://localhost:6443"
echo "   - K3s API: http://localhost:8080"
echo ""
echo "🔧 To run the monitoring script:"
echo "   docker-compose up monitor"
echo ""
echo "🧪 To run with test applications:"
echo "   docker-compose --profile testing up"
echo ""
echo "🛑 To stop everything:"
echo "   docker-compose down"
