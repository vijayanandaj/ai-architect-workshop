#!/usr/bin/env python
import argparse, yaml, re, sys, pathlib
VAGUE = re.compile(r"\b(fast|robust|user[- ]?friendly|scalable|reliable|soon)\b", re.I)
UNIT_HINTS = [("ms","latency"), ("rps","throughput"), ("%","error rate")]
def lint_req(r):
    issues=[]
    if VAGUE.search(r["text"]): issues.append("vague terms present")
    if r["type"]=="nfr":
        has_unit=any(u in r["text"].lower() for u,_ in UNIT_HINTS)
        if not has_unit: issues.append("nfr without quantifiable unit")
    return issues
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("yaml_file")
    a=ap.parse_args()
    data=yaml.safe_load(pathlib.Path(a.yaml_file).read_text())
    bad=[]
    for r in data["requirements"]:
        issues=lint_req(r)
        if issues: bad.append((r["id"], issues, r["text"]))
    if bad:
        print("LINT ISSUES:")
        for rid,issues,text in bad: print(f"- {rid}: {', '.join(issues)} :: {text}")
        sys.exit(1)
    print("Lints: OK")
