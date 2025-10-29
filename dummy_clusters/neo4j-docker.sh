#!/bin/bash

# Neo4J Database Setup for CYBERNEMO
# This script starts a Neo4J database for storing monitoring data

set -e

echo "🗄️  Setting up Neo4J Database for CYBERNEMO"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Neo4J container
echo "🐳 Starting Neo4J database..."
docker run -d \
  --name cybernemo-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
  neo4j:5.15-community

# Wait for Neo4J to be ready
echo "⏳ Waiting for Neo4J to be ready..."
timeout=60
counter=0
while ! curl -s http://localhost:7474 > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Timeout waiting for Neo4J to be ready"
        exit 1
    fi
    echo "   Waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

echo "✅ Neo4J is ready!"
echo ""
echo "📋 Neo4J Database Information:"
echo "   - Web Interface: http://localhost:7474"
echo "   - Username: neo4j"
echo "   - Password: password"
echo "   - Bolt URI: bolt://localhost:7687"
echo ""
echo "🔧 To test with your monitoring script:"
echo "   python3 main.py -db -t 30 -n 5"
echo ""
echo "🛑 To stop Neo4J:"
echo "   docker stop cybernemo-neo4j && docker rm cybernemo-neo4j"
