#!/usr/bin/env python
"""
Requirement linter for architecture work.

Rules added:
- Vague/banned words (e.g., "fast", "robust", "user-friendly", "optimize", "soon")
- NFR must include quantifiable unit(s) or measurable form (ms, %, rps, RTO/RPO, p95 comparator)
- Availability must include percent or 'nines'
- Latency/response-time must include a number + unit
- Security specificity (e.g., 'encrypt' -> say at rest/in transit; 'secure' -> name control like TLS/OIDC)
- Functional requirements must have acceptance criteria
- Basic cross-requirement conflict detection (latency & availability)
Exit code: 1 if any issues found.
"""
import argparse, re, sys, yaml, pathlib
from collections import defaultdict

VAGUE_WORDS = {
    "fast","robust","user friendly","user-friendly","scalable","reliable","soon",
    "optimize","best effort","best-effort","state of the art","state-of-the-art",
    "easy","simple","intuitive","secure"  # 'secure' without specifics will be flagged
}

# regexes
NUM_UNIT = re.compile(r"\b\d+(\.\d+)?\s*(ms|s|sec|seconds?|rps|qps|req/s|tps|%|percent|w(?:eeks)?|m(?:in|ins|inutes)?|h(?:r|rs|ours)?)\b", re.I)
HAS_P95 = re.compile(r"\bp9(5|9)\b", re.I)
CMP_NUM = re.compile(r"(<=|>=|<|>)\s*\d+(\.\d+)?")
PCT = re.compile(r"\b\d{2,3}(\.\d+)?\s*%\b")
NINES = re.compile(r"\b([34])\s*nines\b", re.I)  # "3 nines", "4 nines"
LAT_MS = re.compile(r"\b(\d+(\.\d+)?)\s*ms\b", re.I)
LAT_SEC = re.compile(r"\b(\d+(\.\d+)?)\s*s(ec|econds?)?\b", re.I)
AVAIL = re.compile(r"\bavailability|uptime\b", re.I)
LATENCY = re.compile(r"\blatency|response\s*time|rt\b", re.I)
SEC_ENCRYPT = re.compile(r"\bencrypt(?:ion)?\b", re.I)
SEC_PROTOCOLS = re.compile(r"\b(tls|mtls|https|oauth2|oidc|kms|aes|fips|kms)\b", re.I)
RTO_RPO = re.compile(r"\b(RTO|RPO)\b", re.I)

def has_number_unit(text: str) -> bool:
    t = text.lower()
    return bool(NUM_UNIT.search(t) or (HAS_P95.search(t) and CMP_NUM.search(t)) or RTO_RPO.search(t))

def contains_vague(text: str):
    t = text.lower()
    hits = [w for w in VAGUE_WORDS if w in t]
    return hits

def availability_value(text: str):
    t = text.lower()
    m = PCT.search(t)
    if m:
        try: return float(m.group(0).replace("%","").strip())
        except: return None
    if NINES.search(t):
        # "three nines" ~ 99.9; "four nines" ~ 99.99
        n = int(NINES.search(t).group(1))
        return 100 - 10**(-n)*100  # approx
    return None

def latency_ms_value(text: str):
    t = text.lower()
    m = LAT_MS.search(t)
    if m:
        return float(m.group(1))
    m = LAT_SEC.search(t)
    if m:
        return float(m.group(1)) * 1000.0
    return None

def lint_req(r):
    issues=[]
    text = r.get("text","")
    rtype = (r.get("type") or "").lower()   # "func" or "nfr"

    # 1) vague words
    vague = contains_vague(text)
    if vague:
        issues.append(f"vague wording: {', '.join(sorted(vague))}")

    # 2) NFR metrics/units
    if rtype == "nfr":
        if not has_number_unit(text):
            issues.append("nfr missing measurable unit/metric (add ms/%/rps, RTO/RPO, or p95 comparator)")

        # availability specificity
        if AVAIL.search(text) and not (PCT.search(text) or NINES.search(text)):
            issues.append("availability mentioned without explicit percent or 'nines'")

        # latency specificity
        if LATENCY.search(text) and latency_ms_value(text) is None:
            issues.append("latency/response-time mentioned without a number + unit (e.g., 300 ms)")

        # security specificity
        if SEC_ENCRYPT.search(text) and not re.search(r"at rest|in transit", text, re.I):
            issues.append("encryption mentioned; specify 'at rest' and/or 'in transit'")
        if "secure" in text.lower() and not SEC_PROTOCOLS.search(text):
            issues.append("security vague: reference concrete control (TLS/mTLS, OAuth2/OIDC, AES, KMS, etc.)")

    # 3) func acceptance criteria
    if rtype == "func":
        ac = r.get("acceptance", [])
        if not ac:
            issues.append("functional requirement missing acceptance criteria")

    return issues

def detect_conflicts(requirements):
    """Very simple cross-req conflicts for latency & availability."""
    buckets = defaultdict(list)  # metric -> list of (rid, value)
    for r in requirements:
        rid = r.get("id","?")
        t = r.get("text","")
        if AVAIL.search(t):
            v = availability_value(t)
            if v is not None:
                buckets["availability"].append((rid, v))
        if LATENCY.search(t):
            v = latency_ms_value(t)
            if v is not None:
                buckets["latency"].append((rid, v))

    conflicts=[]
    # availability: percent; flag if values differ by > 0.2 percentage points
    if buckets["availability"]:
        vals = [v for _,v in buckets["availability"]]
        if max(vals) - min(vals) > 0.2:
            pairs = ", ".join([f"{rid}:{v}%" for rid,v in buckets['availability']])
            conflicts.append(f"conflicting availability targets across requirements → {pairs}")

    # latency: ms; flag if values differ by > 20%
    if buckets["latency"]:
        vals = [v for _,v in buckets["latency"]]
        if min(vals) > 0 and (max(vals)/min(vals) > 1.2):
            pairs = ", ".join([f"{rid}:{int(v)}ms" for rid,v in buckets['latency']])
            conflicts.append(f"conflicting latency targets across requirements → {pairs}")

    return conflicts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yaml_file", help="requirements YAML produced by req_extract.py")
    args = ap.parse_args()

    data = yaml.safe_load(pathlib.Path(args.yaml_file).read_text(encoding="utf-8"))
    reqs = data.get("requirements", [])
    any_issues=False

    # per-requirement lints
    for r in reqs:
        rid = r.get("id","?")
        issues = lint_req(r)
        if issues:
            any_issues=True
            print(f"- {rid}:")
            for i in issues:
                print(f"  • {i}")

    # cross-requirement conflicts
    conflicts = detect_conflicts(reqs)
    if conflicts:
        any_issues=True
        print("\nCROSS-REQUIREMENT ISSUES:")
        for c in conflicts:
            print(f"  • {c}")

    if any_issues:
        sys.exit(1)
    print("Lints: OK")

if __name__=="__main__":
    main()
