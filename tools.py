import json
from pathlib import Path
from db import conn

POLICIES = json.loads(Path("data/policies.json").read_text(encoding="utf-8"))

def lookup_policy(policy_number: str, **_):
    p = POLICIES.get(policy_number.strip().upper())
    return p if p else {"found": False}

def check_duplicate_claims(policy_number: str, incident_date: str, source_file: str = "", **_):
    with conn() as con:
        rows = con.execute(
            "SELECT source_file FROM claims WHERE policy_number=? AND incident_date=? AND source_file!=?",
            (policy_number, incident_date, source_file)).fetchall()
    return {"duplicates": [r["source_file"] for r in rows]}

REGISTRY = {"lookup_policy": lookup_policy, "check_duplicate_claims": check_duplicate_claims}

TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_policy",
        "description": "Look up a policy by number in the internal policy register.",
        "parameters": {"type": "object",
                       "properties": {"policy_number": {"type": "string"}},
                       "required": ["policy_number"]}}},
    {"type": "function", "function": {
        "name": "check_duplicate_claims",
        "description": "Check whether a claim for the same policy and incident date was already filed.",
        "parameters": {"type": "object",
                       "properties": {"policy_number": {"type": "string"},
                                      "incident_date": {"type": "string"}},
                       "required": ["policy_number", "incident_date"]}}},
]