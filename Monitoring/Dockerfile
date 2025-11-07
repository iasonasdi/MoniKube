FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NEO4J_URI=bolt://localhost:7687 \
    NEO4J_USERNAME=neo4j \
    NEO4J_PASSWORD=password \
    NEO4J_DATABASE=neo4j

WORKDIR /app

# Install OS-level dependencies required for some Python wheels (e.g. netifaces)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first to leverage Docker layer caching
COPY requirements.txt /tmp/requirements-root.txt
COPY Monitoring/requirements.txt /tmp/requirements-monitoring.txt

RUN pip install --no-cache-dir -r /tmp/requirements-root.txt && \
    pip install --no-cache-dir -r /tmp/requirements-monitoring.txt

# Copy the monitoring service, shared Neo4J handler package, and required data collection modules
COPY Monitoring /app/Monitoring
COPY Neo4J /app/Neo4J
COPY DataCollection /app/DataCollection

# Switch to the monitoring application directory for runtime
WORKDIR /app/Monitoring

EXPOSE 5000

CMD ["python", "app.py"]

