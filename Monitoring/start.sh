#!/bin/bash

# Neo4j Graph Visualization Dashboard Starter Script

echo "🚀 Starting CYBERNEMO Neo4j Graph Visualization Dashboard"
echo "=========================================================="
echo ""

# Check if Neo4j connection parameters are set
if [ -z "$NEO4J_URI" ]; then
    export NEO4J_URI="bolt://localhost:7687"
fi

if [ -z "$NEO4J_USERNAME" ]; then
    export NEO4J_USERNAME="neo4j"
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    export NEO4J_PASSWORD="password"
fi

if [ -z "$NEO4J_DATABASE" ]; then
    export NEO4J_DATABASE="neo4j"
fi

echo "📊 Neo4j Configuration:"
echo "   URI: $NEO4J_URI"
echo "   Username: $NEO4J_USERNAME"
echo "   Database: $NEO4J_DATABASE"
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing requirements..."
    pip3 install -r requirements.txt
    echo ""
fi

# Start the Flask server
echo "🌐 Starting Flask server..."
echo "📝 Open your browser at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================================="
echo ""

python3 app.py

