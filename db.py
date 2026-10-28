import json, sqlite3
from datetime import datetime
from pathlib import Path

DB = "claims.db"

def now():
    return datetime.now().isoformat(timespec="seconds")

def conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS claims(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT UNIQUE, created_at TEXT,
        policy_number TEXT, incident_date TEXT,
        claim_json TEXT, trace_json TEXT,
        action TEXT, reasons_json TEXT, payout REAL,
        draft TEXT, status TEXT DEFAULT 'pending')""")
    con.execute("""CREATE TABLE IF NOT EXISTS support_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT,
        question TEXT, answer TEXT, sources_json TEXT,
        escalated INTEGER, top_score REAL, feedback TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT,
        title TEXT, description TEXT, assessment_json TEXT,
        manual_hours REAL, priority REAL, priority_label TEXT)""")
    return con

# ---- claims ----
def save(rec):
    c = rec["claim"]
    with conn() as con:
        con.execute("DELETE FROM claims WHERE source_file=?", (rec["source_file"],))
        con.execute(
            """INSERT INTO claims(source_file, created_at, policy_number, incident_date,
               claim_json, trace_json, action, reasons_json, payout, draft)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (rec["source_file"], now(), c.get("policy_number"), c.get("incident_date"),
             json.dumps(c), json.dumps(rec["trace"]), rec["action"],
             json.dumps(rec["reasons"]), rec["payout"], rec["draft"]))

def all_claims():
    with conn() as con:
        rows = con.execute("SELECT * FROM claims ORDER BY id").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["claim"] = json.loads(d.pop("claim_json"))
        d["trace"] = json.loads(d.pop("trace_json"))
        d["reasons"] = json.loads(d.pop("reasons_json"))
        out.append(d)
    return out

def set_status(cid, status, draft):
    with conn() as con:
        con.execute("UPDATE claims SET status=?, draft=? WHERE id=?", (status, draft, cid))

# ---- support ----
def log_support(question, answer, sources, escalated, top_score):
    with conn() as con:
        cur = con.execute(
            """INSERT INTO support_log(created_at, question, answer, sources_json,
               escalated, top_score) VALUES(?,?,?,?,?,?)""",
            (now(), question, answer, json.dumps(sources), int(escalated), top_score))
        return cur.lastrowid

def set_feedback(sid, fb):
    with conn() as con:
        con.execute("UPDATE support_log SET feedback=? WHERE id=?", (fb, sid))

def all_support():
    with conn() as con:
        return [dict(r) for r in con.execute("SELECT * FROM support_log ORDER BY id")]

# ---- automation requests ----
def save_request(title, description, assessment, score):
    with conn() as con:
        con.execute(
            """INSERT INTO requests(created_at, title, description, assessment_json,
               manual_hours, priority, priority_label) VALUES(?,?,?,?,?,?,?)""",
            (now(), title, description, json.dumps(assessment),
             score["manual_hours"], score["priority"], score["label"]))

def all_requests():
    with conn() as con:
        rows = con.execute("SELECT * FROM requests ORDER BY id").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["assessment"] = json.loads(d.pop("assessment_json"))
        out.append(d)
    return out

def reset():
    with conn() as con:
        for t in ("claims", "support_log", "requests"):
            con.execute(f"DELETE FROM {t}")

def seed_if_empty(path="data/seed.json"):
    p = Path(path)
    if not p.exists():
        return
    with conn() as con:
        n = sum(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("claims", "support_log", "requests"))
    if n:
        return
    seed = json.loads(p.read_text(encoding="utf-8"))
    with conn() as con:
        for c in seed["claims"]:
            con.execute(
                """INSERT INTO claims(source_file, created_at, policy_number, incident_date,
                   claim_json, trace_json, action, reasons_json, payout, draft, status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (c["source_file"], c["created_at"], c["policy_number"], c["incident_date"],
                 json.dumps(c["claim"]), json.dumps(c["trace"]), c["action"],
                 json.dumps(c["reasons"]), c["payout"], c["draft"], c["status"]))
        for s in seed["support"]:
            con.execute(
                """INSERT INTO support_log(created_at, question, answer, sources_json,
                   escalated, top_score, feedback) VALUES(?,?,?,?,?,?,?)""",
                (s["created_at"], s["question"], s["answer"], s["sources_json"],
                 s["escalated"], s["top_score"], s["feedback"]))
        for r in seed["requests"]:
            con.execute(
                """INSERT INTO requests(created_at, title, description, assessment_json,
                   manual_hours, priority, priority_label) VALUES(?,?,?,?,?,?,?)""",
                (r["created_at"], r["title"], r["description"], json.dumps(r["assessment"]),
                 r["manual_hours"], r["priority"], r["priority_label"]))