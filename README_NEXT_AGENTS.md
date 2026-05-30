# Next Agents Upgrade

This upgrade adds three production-style agents:

1. `DataQualityAgent`
   - validates and normalizes incoming transactions before scoring.
2. `AgentTraceAgent`
   - records which agents ran, in what order, and what each produced.
3. `AuditAgent`
   - writes every scoring decision to `audits/scoring_audit.jsonl`.

## Files added

```text
app/agents/data_quality_agent.py
app/agents/agent_trace_agent.py
app/agents/audit_agent.py
scripts/view_audits.py
```

## Files replaced

```text
app/agents/triage_orchestrator_agent.py
app/schemas/transaction_schema.py
app/main.py
```

## Run

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Run `POST /score`. The response now includes:

```text
data_quality
agent_trace
audit_id
```

To view saved audit logs:

```powershell
python scripts\view_audits.py
```
