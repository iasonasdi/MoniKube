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

### 3. Start the Flask Server (Local Python)

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

## 🐳 Run with Docker

Running the dashboard in Docker keeps it alive even after you close your terminal window.

1. **Build the image** (from the `CYBERNEMO` project root; only the `Monitoring` service and shared `neo4j_handler.py` are included in this image):
   ```bash
   docker build -t monitoring-dashboard -f Monitoring/Dockerfile .
   ```

2. **Set Neo4j connection variables** (optional—Docker image defaults mirror these values, but override them here when needed):
   ```bash
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USERNAME="neo4j"
   export NEO4J_PASSWORD="password"
   export NEO4J_DATABASE="neo4j"
   ```

3. **Run the container in the background**:

Current port selected for browser is *5100* but can change based on desires
   ```bash
   docker run -d \
     --name monitoring-dashboard \
     -p 5100:5000 \
     -e NEO4J_URI \
     -e NEO4J_USERNAME \
     -e NEO4J_PASSWORD \
     -e NEO4J_DATABASE \
     monitoring-dashboard
   ```

4. **View logs or manage the container**:
   - Stream logs: `docker logs -f monitoring-dashboard`
   - Stop the container: `docker stop monitoring-dashboard`
   - Start again later: `docker start monitoring-dashboard`
   - Remove it completely: `docker rm -f monitoring-dashboard`

5. **Open the dashboard** at `http://localhost:5000`

> 💡 Tip: store these variables in an `.env` file and run `docker run --env-file .env ...` so you can update Neo4j credentials once and reuse them across environments.

### 🧰 Run Neo4j and the Dashboard Together (Docker Compose)

When you want a portable setup that always launches both Neo4j and the monitoring dashboard on the same machine, use the `docker-compose.yml` inside the `Monitoring/` folder:

1. Build and start both services from the Monitoring directory:
   ```bash
   cd /home/cosmote/CYBERNEMO/Monitoring
   docker compose up -d
   ```

   This will:
   - Start `neo4j:5.15-community` with default credentials `neo4j/password`
   - Build the monitoring image from `Monitoring/Dockerfile`
   - Expose the dashboard on `http://localhost:5100`
   - Expose Neo4j Browser on `http://localhost:7474`

2. Check logs if needed:
   ```bash
   docker compose logs -f dashboard
   docker compose logs -f neo4j
   ```

3. Stop everything when you are done:
   ```bash
   docker compose down
   ```

4. Persist Neo4j data using the named volumes declared in `docker-compose.yml` (`neo4j_data`, `neo4j_logs`).

> 🔐 Change the default Neo4j credentials by editing `docker-compose.yml` (env var `NEO4J_AUTH`) and updating the monitoring service environment variables accordingly before running `docker compose up`.

### 🔁 Updating the Docker Image after Code Changes

When you edit `app.py`, `index.html`, or any supporting files, rebuild the image so the container picks up the new version:

1. Stop (and optionally remove) the running container:
   ```bash
   docker stop monitoring-dashboard
   docker rm monitoring-dashboard   # omit if you want to reuse the container name without removing
   ```

2. Rebuild the image from the project root:
   ```bash
   docker build -t monitoring-dashboard -f Monitoring/Dockerfile .
   ```

   Add `--no-cache` if you want to bypass Docker's layer cache:
   ```bash
   docker build --no-cache -t monitoring-dashboard -f Monitoring/Dockerfile .
   ```

3. Start a new container from the freshly built image:
   ```bash
   docker run -d \
     --name monitoring-dashboard \
     -p 5000:5000 \
     -e NEO4J_URI \
     -e NEO4J_USERNAME \
     -e NEO4J_PASSWORD \
     -e NEO4J_DATABASE \
     monitoring-dashboard
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

