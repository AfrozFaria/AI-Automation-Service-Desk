from pathlib import Path
import db, pipeline, support

TUNED = {
    "claim1.txt": "standard_queue",
    "claim2.txt": "senior_review",
    "claim3.txt": "request_more_info",
    "claim4.txt": "manual_review",
    "claim5.txt": "standard_queue",
    "claim6.txt": "policy_issue",
    "claim7.txt": "fraud_review",
}
HELD_OUT = {
    "claim8.txt": "fraud_review",
    "claim9.txt": "senior_review",
    "claim10.txt": "manual_review",
    "claim11.txt": "policy_issue",
    "claim12.txt": "fraud_review",
}
SUPPORT_TESTS = [   # (question, should it escalate?)
    ("Can I paste a customer's policy number into a public AI tool?", False),
    ("How do I request a new automation?", False),
    ("Does the claims automation approve claims by itself?", False),
    ("What is the office wifi password?", True),
]

def run_claims(title, tests):
    print(f"== {title} ==")
    ok = 0
    for name, expected in tests.items():
        rec = pipeline.process(Path("inbox") / name)
        passed = rec["action"] == expected
        ok += passed
        print(f"{'PASS' if passed else 'FAIL'}  {name:12} expected={expected:18} got={rec['action']}")
        if not passed:
            print("      reasons:", rec["reasons"])
    print()
    return ok

db.reset()
ok_t = run_claims("Claims routing: original set (used for tuning)", TUNED)
ok_h = run_claims("Claims routing: new set", HELD_OUT)

print("== Support: answer vs escalate ==")
ok_s = 0
for q, should_escalate in SUPPORT_TESTS:
    rec = support.ask(q)
    ok = rec["escalated"] == should_escalate
    ok_s += ok
    print(f"{'PASS' if ok else 'FAIL'}  escalated={rec['escalated']!s:5} sim={rec['top_score']}  {q}")

print(f"\nOriginal set: {ok_t}/{len(TUNED)} | New set: {ok_h}/{len(HELD_OUT)} | Support: {ok_s}/{len(SUPPORT_TESTS)}")