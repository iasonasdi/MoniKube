#!/bin/bash

# Neo4J Database Cleanup Script
# Provides multiple methods to clear Neo4J data

set -e

echo "🧹 Neo4J Database Cleanup Options"
echo "=================================="
echo ""
echo "Choose a method to clear Neo4J data:"
echo ""
echo "1. Clear via Python script (recommended - keeps DB running)"
echo "2. Stop and remove Docker Compose volumes (if using docker-compose)"
echo "3. Stop and remove standalone Docker container (if using standalone)"
echo "4. Exit"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "🧹 Using Python script to clear database..."
        cd "$(dirname "$0")/.."
        python3 Neo4J/clear_database.py
        ;;
    2)
        echo ""
        echo "🐳 Stopping Docker Compose and removing volumes..."
        cd "$(dirname "$0")/../Monitoring"
        if [ -f "docker-compose.yml" ]; then
            docker-compose down -v
            echo "✅ Docker Compose stopped and volumes removed"
            echo "💡 To restart: cd Monitoring && docker-compose up -d"
        else
            echo "❌ docker-compose.yml not found in Monitoring directory"
        fi
        ;;
    3)
        echo ""
        echo "🐳 Stopping and removing standalone Neo4J container..."
        if docker ps -a | grep -q "cybernemo-neo4j"; then
            docker stop cybernemo-neo4j
            docker rm cybernemo-neo4j
            echo "✅ Container stopped and removed"
        elif docker ps -a | grep -q "monitoring-neo4j"; then
            docker stop monitoring-neo4j
            docker rm monitoring-neo4j
            echo "✅ Container stopped and removed"
        else
            echo "❌ No Neo4J container found (cybernemo-neo4j or monitoring-neo4j)"
        fi
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Done! Your Neo4J database is now clean and ready for fresh data."

