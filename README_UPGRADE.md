# Production Upgrade Pack

This pack adds:

1. Feedback Agent
2. Monitoring Agent
3. Retraining Agent
4. Streamlit Dashboard
5. Docker setup for FastAPI + Neo4j + Dashboard

Copy these files into your existing project:

```text
agentic_gnn_fraud_platform_neo4j/
```

## Files to copy

```text
app/agents/feedback_agent.py
app/agents/monitoring_agent.py
app/agents/retraining_agent.py
app/schemas/feedback_schema.py
app/main.py
dashboard/streamlit_app.py
Dockerfile
docker-compose.full.yml
.dockerignore
```

## Install extra dependency locally

```powershell
pip install streamlit requests
```

Or add these to `requirements.txt`:

```text
streamlit==1.41.1
requests==2.32.3
```

## Run API locally

```powershell
$env:ENABLE_NEO4J="true"
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="password123"
$env:NEO4J_DATABASE="neo4j"

uvicorn app.main:app --port 8002
```

## Run dashboard locally

Open a second PowerShell window:

```powershell
streamlit run dashboard/streamlit_app.py
```

Dashboard opens at:

```text
http://localhost:8501
```

## Run full Docker setup

```powershell
docker compose -f docker-compose.full.yml up --build
```

API:

```text
http://localhost:8002/docs
```

Dashboard:

```text
http://localhost:8501
```

Neo4j:

```text
http://localhost:7474
```

Neo4j login:

```text
username: neo4j
password: password123
```
