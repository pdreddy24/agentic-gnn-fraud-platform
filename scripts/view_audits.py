from __future__ import annotations

import json
from pathlib import Path

path = Path("audits/scoring_audit.jsonl")
if not path.exists():
    print("No audit file found yet. Run POST /score first.")
    raise SystemExit(0)

lines = path.read_text(encoding="utf-8").strip().splitlines()
print(f"Found {len(lines)} audit records. Showing last 5:\n")
for line in lines[-5:]:
    record = json.loads(line)
    print(json.dumps(record, indent=2))
