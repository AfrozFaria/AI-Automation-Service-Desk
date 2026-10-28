import json
from pathlib import Path
import db, pipeline, support, advisor

db.reset()

for i in range(1, 13):                      # in order, so duplicates are detected
    pipeline.process(Path("inbox") / f"claim{i}.txt")

for q in ["Can I paste a customer's policy number into a public AI tool?",
          "How do I request a new automation?",
          "What is the office wifi password?"]:
    rec = support.ask(q)
    if not rec["escalated"]:
        db.set_feedback(rec["id"], "up")

for title, desc in advisor.EXAMPLES.items():
    advisor.assess(title, desc)

seed = {"claims": db.all_claims(), "support": db.all_support(),
        "requests": db.all_requests()}
Path("data/seed.json").write_text(json.dumps(seed, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
print("Saved data/seed.json:", len(seed["claims"]), "claims,",
      len(seed["support"]), "support questions,", len(seed["requests"]), "requests")