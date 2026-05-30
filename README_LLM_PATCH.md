# LLM + User Input Patch

Copy these files into your project root.

Important fix:
Delete this wrong nested folder if it exists:

```powershell
rmdir app\agents\app -Recurse -Force
```

The correct LLM file path is:

```text
app/agents/fraud_explanation_agent.py
```

## Local run

```powershell
pip install -r requirements.txt

$env:OPENAI_API_KEY="your_key_here"
$env:OPENAI_MODEL="gpt-5.5"

$env:ENABLE_NEO4J="true"
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="password123"
$env:NEO4J_DATABASE="neo4j"

uvicorn app.main:app --port 8002
```

## Dashboard

```powershell
streamlit run dashboard/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## Docker

Set your key in PowerShell first:

```powershell
$env:OPENAI_API_KEY="your_key_here"
$env:OPENAI_MODEL="gpt-5.5"
```

Then:

```powershell
docker compose -f docker-compose.full.yml down
docker compose -f docker-compose.full.yml up --build
```
