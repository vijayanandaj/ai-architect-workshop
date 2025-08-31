#!/usr/bin/env python
import argparse, yaml, pathlib, json, datetime as dt

LOWER_BETTER = {"performance_p95_ms","cost_monthly_usd","time_to_market_weeks"}
HIGHER_BETTER = {"availability_pct","operability_score","scalability_score","security_score"}

def clamp01(x): return max(0.0, min(1.0, x))

def norm_score(metric, val, lo, hi):
    if metric in LOWER_BETTER:   # lower is better
        return clamp01((hi - val) / (hi - lo))
    else:                        # higher is better
        return clamp01((val - lo) / (hi - lo))

def load_yaml(p): return yaml.safe_load(pathlib.Path(p).read_text(encoding="utf-8"))

def check_constraints(metrics, constraints):
    msgs=[]; ok=True
    for c in constraints or []:
        m=c["metric"]; mn=c.get("min"); mx=c.get("max"); v=metrics.get(m)
        if v is None: continue
        if mn is not None and v < mn: ok=False; msgs.append(f"{m}={v} < min {mn}")
        if mx is not None and v > mx: ok=False; msgs.append(f"{m}={v} > max {mx}")
    return ok, msgs

def main():
    ap=argparse.ArgumentParser(description="Score architecture options vs NFR profile")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--options", required=True)
    ap.add_argument("--outdir", default="docs/decisions")
    args=ap.parse_args()

    prof=load_yaml(args.profile)
    opts=load_yaml(args.options)["options"]
    weights=prof["weights"]; bounds=prof["bounds"]

    total=sum(weights.values()) or 1.0
    weights={k:v/total for k,v in weights.items()}

    scored=[]
    for opt in opts:
        m=opt["metrics"]
        ok,viol=check_constraints(m, prof.get("hard_constraints"))
        per={}
        for k in weights:
            lo,hi=bounds[k]
            per[k]=norm_score(k, m[k], lo, hi)
        overall = sum(weights[k]*per[k] for k in weights)
        scored.append({
            "name": opt["name"], "kind": opt.get("kind",""),
            "ok": ok, "violations": viol,
            "overall": round(overall,4),
            "per_metric": {k: round(per[k],3) for k in per},
            "raw": m, "notes": opt.get("notes",[]), "risks": opt.get("risks",[])
        })

    scored.sort(key=lambda x: (x["ok"], x["overall"]), reverse=True)
    best=scored[0]

    outdir=pathlib.Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    (outdir/"decision_scores.json").write_text(json.dumps({"profile":prof,"scored":scored}, indent=2), encoding="utf-8")

    # Simple markdown summary
    lines=[f"# Architecture Decision Report — {prof.get('system','System')}",
           f"_Generated: {dt.date.today().isoformat()}_\n",
           "## Overall ranking"]
    for i,s in enumerate(scored,1):
        lines.append(f"{i}. **{s['name']}** — {s['overall']:.3f}" + ("" if s["ok"] else " (DISQUALIFIED)"))
    (outdir/"decision_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {outdir/'decision_report.md'} and {outdir/'decision_scores.json'}. Best: {best['name']} ({best['overall']:.3f})")

if __name__=="__main__":
    main()
