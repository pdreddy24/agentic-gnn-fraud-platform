# Full-Stack Fraud Detection Code

This package includes:

## Backend files

Copy these into your existing FastAPI project root:

```text
app/database.py
app/schemas/auth_schema.py
app/main.py
requirements.txt
scripts/generate_large_test_csv.py
sample_transactions.csv
```

Important: keep your existing folders too:

```text
app/agents/
app/schemas/transaction_schema.py
app/schemas/feedback_schema.py
ml/
artifacts/
scripts/load_neo4j.py
```

## Frontend files

The React app is inside:

```text
frontend/
```

## Install backend

From your project root:

```powershell
pip install -r requirements.txt
```

## Start Neo4j

```powershell
docker compose up -d neo4j
python scripts/load_neo4j.py --clear
```

## Start backend

```powershell
$env:OPENAI_API_KEY="your_new_openai_key_here"
$env:OPENAI_MODEL="gpt-5.5"

$env:ENABLE_NEO4J="true"
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="password123"
$env:NEO4J_DATABASE="neo4j"

uvicorn app.main:app --port 8002
```

## Install frontend

Open a new PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Generate large CSV test data

From your project root:

```powershell
python scripts/generate_large_test_csv.py --rows 1000 --out large_test_transactions.csv
```

Upload `large_test_transactions.csv` in the React UI.

## Endpoints included

```text
POST /auth/signup
POST /auth/login
GET /auth/me
POST /uploads/predict-file
GET /uploads/history
GET /uploads/{batch_id}/predictions
GET /uploads/compare/{current_batch_id}/{previous_batch_id}
```

## CSV columns required

```csv
transaction_id,user_id,device_id,card_id,ip_address,merchant_id,amount,timestamp,channel,country
```
