#!/bin/bash
#
# CYBERNEMO Monitoring Script
# Automatically ensures kind cluster exists, then runs main.py
#

set -e

CLUSTER_NAME="cybernemo-test"
KUBECTL_CONTEXT="kind-${CLUSTER_NAME}"

echo "🚀 CYBERNEMO Kubernetes Cluster Monitor"
echo "========================================"
echo ""

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "❌ Error: kind is not installed"
    echo "   Install with: curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 && chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind"
    exit 1
fi

# Check if cluster exists
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "✅ Kind cluster '${CLUSTER_NAME}' already exists"
    
    # Check if cluster is running
    if kubectl cluster-info --context ${KUBECTL_CONTEXT} &> /dev/null; then
        echo "✅ Cluster is running and accessible"
    else
        echo "⚠️  Cluster exists but may not be ready. Waiting for it to be ready..."
        # Wait for cluster to be ready (max 60 seconds)
        timeout=60
        elapsed=0
        while ! kubectl cluster-info --context ${KUBECTL_CONTEXT} &> /dev/null; do
            if [ $elapsed -ge $timeout ]; then
                echo "❌ Cluster did not become ready within ${timeout} seconds"
                echo "   Try: kind delete cluster --name ${CLUSTER_NAME} && kind create cluster --name ${CLUSTER_NAME}"
                exit 1
            fi
            sleep 2
            elapsed=$((elapsed + 2))
            echo -n "."
        done
        echo ""
        echo "✅ Cluster is now ready"
    fi
else
    echo "📦 Kind cluster '${CLUSTER_NAME}' does not exist. Creating it..."
    kind create cluster --name ${CLUSTER_NAME}
    echo "✅ Cluster created successfully"
    
    # Wait for cluster to be ready
    echo "⏳ Waiting for cluster to be ready..."
    timeout=120
    elapsed=0
    while ! kubectl cluster-info --context ${KUBECTL_CONTEXT} &> /dev/null; do
        if [ $elapsed -ge $timeout ]; then
            echo "❌ Cluster did not become ready within ${timeout} seconds"
            exit 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done
    echo ""
    echo "✅ Cluster is ready"
fi

# Wait for nodes to be ready
echo "⏳ Waiting for nodes to be ready..."
timeout=120
elapsed=0
while ! kubectl get nodes --context ${KUBECTL_CONTEXT} -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -q "True"; do
    if [ $elapsed -ge $timeout ]; then
        echo "⚠️  Warning: Nodes did not become ready within ${timeout} seconds, but continuing anyway..."
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo -n "."
done
echo ""

# Show cluster status
echo ""
echo "📊 Cluster Status:"
kubectl get nodes --context ${KUBECTL_CONTEXT}
echo ""

# Run main.py with all provided arguments
echo "🔄 Starting monitoring with main.py..."
echo "========================================"
echo ""
echo "💡 Tip: Use --no-docker to disable Docker container monitoring"
echo ""

# Pass all arguments to main.py
python3 main.py "$@"

