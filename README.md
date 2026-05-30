# Agentic GNN Fraud Triage Platform with Neo4j

This is a runnable ML-powered multi-agent fraud triage project.

It uses agents, but not LLMs:

| Agent | Model / Logic |
|---|---|
| Feature Agent | Feature engineering logic |
| Neo4j Graph Agent | Stores/reads graph relationships from Neo4j |
| GNN Graph Agent | Simple GraphSAGE-style GNN using PyTorch |
| ML Scoring Agent | RandomForest tabular model |
| Policy Agent | Business rules and thresholds |
| Orchestrator Agent | Coordinates the full workflow |

Neo4j is the graph database. The GNN model is the ML model that learns from graph patterns.

---

## 1. Install Python dependencies

```bash
pip install -r requirements.txt
```


---

## 2. Generate synthetic graph fraud data

```bash
python ml/generate_data.py --rows 2500
```

This creates:

```text
data/transactions.csv
```

Columns:

```text
transaction_id,user_id,device_id,card_id,ip_address,merchant_id,amount,timestamp,channel,country,is_fraud
```

---

## 3. Train the GNN and tabular ML models

```bash
python ml/train_all.py --epochs 80
```

For a quick test:

```bash
python ml/train_all.py --epochs 5
```

This creates:

```text
artifacts/gnn_model.pt
artifacts/graph_artifact.joblib
artifacts/tabular_model.joblib
artifacts/metrics.json
```

---

## 4. Start Neo4j

Make sure Docker Desktop is running, then:

```bash
docker compose up -d
```

Open Neo4j Browser:

```text
http://localhost:7474
```

Login:

```text
username: neo4j
password: password123
```

---

## 5. Load transactions into Neo4j

```bash
python scripts/load_neo4j.py --clear
```

For fast testing:

```bash
python scripts/load_neo4j.py --clear --limit 500
```

Test graph context:

```bash
python scripts/test_neo4j_context.py
```

You can also run queries from:

```text
neo4j_sample_queries.cypher
```

---

## 6. Enable Neo4j for the API

Create a `.env` file or set environment variables.

Example `.env`:

```env
ENABLE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
NEO4J_DATABASE=neo4j
```

On Windows PowerShell, you can also run:

```powershell
$env:ENABLE_NEO4J="true"
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="password123"
$env:NEO4J_DATABASE="neo4j"
```

On Mac/Linux:

```bash
export ENABLE_NEO4J=true
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password123
export NEO4J_DATABASE=neo4j
```

---

## 7. Run local demo

Without API:

```bash
python demo_score.py
```

---

## 8. Start FastAPI

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Use `POST /score`.

Example request:

```json
{
  "transaction_id": "TNEW001",
  "user_id": "U0001",
  "device_id": "D0001",
  "card_id": "C0001",
  "ip_address": "IP0001",
  "merchant_id": "M0001",
  "amount": 1800,
  "timestamp": "2026-05-28T23:15:00",
  "channel": "web",
  "country": "US"
}
```

Example response fields:

```json
{
  "transaction_id": "TNEW001",
  "gnn_graph_score": 0.63,
  "ml_score": 0.21,
  "final_risk": 0.462,
  "decision": "REVIEW",
  "reason_codes": ["HIGH_AMOUNT", "NEO4J_SHARED_DEVICE_MANY_USERS"],
  "neo4j_enabled": true,
  "neo4j_graph_context": {
    "shared_device_users": 5,
    "shared_ip_users": 3,
    "shared_card_users": 1,
    "merchant_fraud_rate": 0.12,
    "device_fraud_rate": 0.41,
    "ip_fraud_rate": 0.20
  },
  "model_versions": {
    "neo4j_graph_context": "neo4j_graph_context_v1",
    "gnn": "simple_graphsage_v1",
    "tabular_ml": "random_forest_v1"
  }
}
```

---

## How Neo4j fits

Neo4j stores this graph:

```text
(User)-[:MADE]->(Transaction)
(User)-[:USED_DEVICE]->(Device)
(User)-[:USED_CARD]->(Card)
(User)-[:USED_IP]->(IPAddress)
(Transaction)-[:FROM_DEVICE]->(Device)
(Transaction)-[:FROM_IP]->(IPAddress)
(Transaction)-[:USED_CARD]->(Card)
(Transaction)-[:PAID_TO]->(Merchant)
```

The Neo4j Graph Agent reads graph context such as:

```text
shared_device_users
shared_ip_users
shared_card_users
device_fraud_rate
ip_fraud_rate
merchant_fraud_rate
```

The GNN Graph Agent uses the trained PyTorch GNN model.

The Policy Agent combines GNN + ML + Neo4j reason codes.

---

## Important note

This is a working educational version. For production, you still need real fraud data, stronger auth, logging, monitoring, CI/CD, model registry, and a real deployment environment.
