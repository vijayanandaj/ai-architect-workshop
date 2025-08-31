#!/usr/bin/env python
import argparse, json, datetime as dt, pathlib

TEMPLATES = {
  "monolith": [
    "Simpler operational model and lower platform cost.",
    "Faster initial delivery; risk of coupling over time."
  ],
  "microservices": [
    "Team autonomy; independent deploys; scale per service.",
    "Higher ops complexity; needs API governance and observability."
  ],
  "event-driven": [
    "Looser coupling and replay; decoupled scale.",
    "Eventual consistency; schema and DLQ governance required."
  ]
}

if __name__ == "__main__":
  ap = argparse.ArgumentParser(description="Create an ADR from decision_scores.json")
  ap.add_argument("--scores", default="docs/decisions/decision_scores.json")
  ap.add_argument("--adr-id", default="010")
  ap.add_argument("--outdir", default="docs/decisions")
  args = ap.parse_args()

  data = json.loads(pathlib.Path(args.scores).read_text(encoding="utf-8"))
  scored = data["scored"]; prof = data["profile"]
  best = scored[0]
  today = dt.date.today().isoformat()
  system = prof.get("system","System")
  kind = best.get("kind","option")
  pros_cons = TEMPLATES.get(kind, [])

  lines = []
  lines.append(f"# ADR {args.adr_id}: Select {kind} architecture — {best['name']}\n")
  lines.append(f"- **Status**: Proposed")
  lines.append(f"- **Date**: {today}")
  lines.append(f"- **System**: {system}\n")
  lines.append("## Context")
  hc = prof.get('hard_constraints', [])
  lines.append("- We compared multiple candidate architectures using weighted NFR scoring.")
  lines.append("- Hard constraints: " + (", ".join(c.get('metric') for c in hc) if hc else "None") + "\n")
  lines.append("## Decision")
  lines.append(f"We will adopt **{best['name']}** ({kind}) based on the highest overall score "
               f"({best['overall']:.3f}) and satisfaction of hard constraints.\n")
  lines.append("## Consequences")
  for p in pros_cons: lines.append(f"- {p}")
  lines.append("\n## Trade-offs & Scores")
  for k,v in best["per_metric"].items():
    lines.append(f"- {k}: {v:.2f} (raw={best['raw'][k]})")
  lines.append("\n## Alternatives considered")
  for s in scored[1:]:
    suffix = "" if s["ok"] else " (DISQUALIFIED)"
    lines.append(f"- {s['name']} — score {s['overall']:.3f}{suffix}")
  out = pathlib.Path(args.outdir) / f"ADR-{args.adr_id}-{kind}.md"
  out.write_text("\n".join(lines) + "\n", encoding="utf-8")
  print(f"Wrote {out}")
