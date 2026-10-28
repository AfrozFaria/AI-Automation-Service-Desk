import db
for c in db.all_claims():
    if c["source_file"] in ("claim3.txt", "claim7.txt"):
        print(c["source_file"], c["action"], c["reasons"])
        print(c["claim"])
        print(c["trace"], "\n")