# Neo4j Graph Visualization Dashboard

An interactive web-based visualization tool for exploring Neo4j graph data stored by the CYBERNEMO monitoring system.

## 🎯 Features

- **Interactive Graph Visualization**: Beautiful, interactive graph using vis.js
- **Real-time Data**: Live connection to Neo4j database
- **Node Details**: Click on any node to see detailed information
- **Search & Filter**: Quickly find nodes by name, ID, or type
- **Export**: Export graph data as JSON
- **Statistics**: Real-time counts of nodes and edges
- **Responsive Design**: Modern, gradient-based UI
- **Color-coded Nodes**: Different colors for VM, Cluster, Node, Pod, Service, Container

## 📋 Prerequisites

1. **Neo4j Database**: Must be running and accessible
2. **Python 3.7+**: For the Flask backend
3. **Required Python packages**:
   ```bash
   pip install flask flask-cors neo4j
   ```

## 🚀 Quick Start

### 1. Start Neo4j Database

Make sure your Neo4j database is running. Default connection:
- URI: `bolt://localhost:7687`
- Username: `neo4j`
- Password: `password`

### 2. Configure Connection (Optional)

You can set environment variables to customize the connection:

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="password"
export NEO4J_DATABASE="neo4j"
```

### 3. Start the Flask Server

Navigate to the Monitoring directory and run:

```bash
cd /home/cosmote/CYBERNEMO/Monitoring
python app.py
```

The server will start on `http://localhost:5000`

### 4. Open in Browser

Open your web browser and navigate to:
```
http://localhost:5000
```

## 🎮 Usage

### Viewing the Graph

1. **Load Graph**: Click "🔄 Refresh Graph" to load the latest data
2. **Zoom**: Use mouse wheel to zoom in/out
3. **Pan**: Click and drag to move around
4. **Reset**: Click "🎯 Reset View" to return to default view

### Exploring Nodes

1. **Click a Node**: Click on any node (circle) to see its details
2. **View Details**: Node information appears in the left sidebar
3. **Browse Properties**: Scroll to see all node properties

### Searching

1. **Search Box**: Type in the search box to filter nodes
2. **Filter**: Results filter by name, ID, or type
3. **Clear**: Clear the search box to show all nodes

### Exporting Data

1. **Export**: Click "💾 Export JSON" to save the current graph
2. **Format**: Data is exported as JSON format
3. **File**: Downloads as `neo4j-graph-export.json`

## 🎨 Node Types and Colors

The visualization uses color-coding to distinguish node types:

- **VM** (Red): Virtual machines hosting clusters
- **Cluster** (Teal): Kubernetes clusters
- **Node** (Blue): Kubernetes nodes
- **Pod** (Green): Running pods
- **Service** (Yellow): Kubernetes services
- **Container** (Pink): Containers within pods

## 🔧 API Endpoints

The Flask backend provides the following REST API:

### `GET /api/health`
Health check endpoint to verify Neo4j connection

**Response:**
```json
{
  "status": "healthy",
  "neo4j": "connected"
}
```

### `GET /api/graph`
Get complete graph data for visualization

**Response:**
```json
{
  "nodes": [...],
  "edges": [...]
}
```

### `GET /api/node/<node_id>`
Get detailed information about a specific node

**Response:**
```json
{
  "id": "node_id",
  "labels": ["Node"],
  "properties": {...},
  "type": "Node"
}
```

### `GET /api/nodes`
Get summary of all nodes grouped by type

**Response:**
```json
{
  "summary": [
    {"type": "Node", "count": 5},
    {"type": "Pod", "count": 10}
  ]
}
```

## 🏗️ Architecture

### Backend (`app.py`)
- Flask web server
- Neo4j database integration
- REST API endpoints
- Data transformation for vis.js

### Frontend (`index.html`)
- vis.js for graph visualization
- Modern, responsive UI
- Interactive features
- Real-time updates

## 🔒 Security Notes

- The `/api/query` endpoint allows custom Cypher queries (restrict in production)
- Default connection uses basic authentication
- For production, implement proper authentication and HTTPS

## 🐛 Troubleshooting

### "Failed to connect to Neo4j"
- Verify Neo4j is running: `docker ps` (if using Docker)
- Check connection parameters in `app.py` or environment variables
- Test connection: `neo4j-admin check-uri bolt://localhost:7687`

### "No data in graph"
- Ensure monitoring data has been imported to Neo4j
- Check if Neo4j contains any nodes with `MATCH (n) RETURN count(n)`
- Verify the CYBERNEMO monitoring tool has populated the database

### "Port 5000 already in use"
- Change the port in `app.py`: `app.run(port=5001)`
- Or stop the process using port 5000

### "ModuleNotFoundError: flask"
- Install requirements: `pip install -r requirements.txt`
- Or install manually: `pip install flask flask-cors neo4j`

## 🔄 Updating the Graph

The graph loads data from Neo4j when:
1. You click "🔄 Refresh Graph"
2. You reload the page
3. The page first loads

To add new data, run the CYBERNEMO monitoring tool to collect fresh cluster information.

## 📝 File Structure

```
Monitoring/
├── app.py                    # Flask backend API
├── index.html                # Frontend HTML with vis.js
├── requirements.txt          # Python dependencies
└── Readme-Monitoring.md      # This file
```

## 🎯 Future Enhancements

- Real-time updates using WebSockets
- Historical data visualization
- Advanced filtering and querying
- Export to PNG/SVG formats
- 3D graph visualization
- Multi-cluster comparison
- Performance metrics over time

## 📞 Support

For issues or questions:
1. Check Neo4j connection with `bolt://` URL
2. Verify all required Python packages are installed
3. Check Flask logs for error messages
4. Ensure Neo4j database contains monitoring data

---

**CYBERNEMO Monitoring** - Visualize your Kubernetes infrastructure at a glance! 🚀

