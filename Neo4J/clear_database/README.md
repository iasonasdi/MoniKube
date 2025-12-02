# Option 1: Python script (recommended)

Keeps Neo4j running and deletes all data via Cypher queries:

```bash
# With confirmation prompt
python3 CYBERNEMO/Neo4J/clear_database.py

# Without confirmation (use with caution!)
python3 CYBERNEMO/Neo4J/clear_database.py --yes

# With custom connection details
python3 CYBERNEMO/Neo4J/clear_database.py --uri bolt://localhost:7687 --username neo4j --password yourpassword
```


# Option 2: Interactive bash script

Provides multiple cleanup methods:
```bash
bash CYBERNEMO/Neo4J/clear_database.sh
```

This will let you choose:
- Python script (keeps DB running)
- Docker Compose down with volumes (if using docker-compose)
- Stop standalone container (if using standalone Docker)