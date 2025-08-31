#!/usr/bin/env python
import argparse, pathlib, yaml, datetime as dt, re
from typing import Dict, Any, List

def load_source(p: pathlib.Path) -> Dict[str, Any]:
    if p.suffix.lower() in {".yml",".yaml"}:
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    data={"system":None,"domains":[],"services":[],"datastores":[],"integrations":[],
          "quality_attributes":{},"pain_points":[]}
    cur=None
    for line in p.read_text(encoding="utf-8").splitlines():
        t=line.strip()
        if t.startswith("#"):
            h=t.lstrip("# ").lower()
            cur=("system" if "system" in h else
                 "domains" if "domain" in h else
                 "services" if "service" in h else
                 "datastores" if ("datastore" in h or "database" in h) else
                 "integrations" if "integration" in h else
                 "quality_attributes" if ("quality" in h or "nfr" in h) else
                 "pain_points" if ("pain" in h or "issue" in h) else None)
            continue
        if t.startswith("- "):
            v=t[2:].strip()
            if cur=="domains": data["domains"].append(v)
            elif cur=="services": data["services"].append({"name":v})
            elif cur=="datastores": data["datastores"].append({"name":v})
            elif cur=="integrations": data["integrations"].append({"name":v})
            elif cur=="pain_points": data["pain_points"].append(v)
        elif cur=="system" and t:
            data["system"]=t
    return data

def infer_system_name(d:Dict[str,Any], override:str|None)->str:
    return override or str(d.get("system") or "TargetSystem")

def list_service_names(d:Dict[str,Any])->List[str]:
    s=[(x["name"] if isinstance(x,dict) else str(x)) for x in d.get("services",[])]
    return s or ["Monolith"]

def mk_adr(system, style, d, adr_id):
    today=dt.date.today().isoformat()
    pain=d.get("pain_points",[])
    qa=d.get("quality_attributes",{})
    ctx=[]
    if pain: ctx.append("Known pain points:\n"+"\n".join([f"- {p}" for p in pain]))
    if qa:   ctx.append("Quality attributes / constraints:\n"+"\n".join([f"- {k}: {v}" for k,v in qa.items()]))
    context="\n\n".join(ctx) or "- Existing system requires modernization and clearer boundaries."
    details={
      "microservices":[
        "Define bounded contexts and split monolith by domain.",
        "Each service owns its data; enforce clear API contracts.",
        "Minimize sync calls; prefer async where feasible."
      ],
      "event-driven":[
        "Adopt event-driven architecture with durable topics/queues.",
        "Use Outbox for exactly-once publish from transactional stores.",
        "Idempotent consumers; schema evolution & versioning."
      ],
      "medallion":[
        "Adopt Bronze/Silver/Gold on Delta/Parquet.",
        "Bronze raw; Silver cleansed/conformed; Gold KPIs/serving.",
        "Streaming where possible; checkpoints and DQ checks."
      ],
    }[style]
    consequences={
      "microservices":[
        "↑ Autonomy & deploy speed; ↑ ops complexity.",
        "Needs API governance, observability, contract tests."
      ],
      "event-driven":[
        "Looser coupling & replay; ↑ eventual consistency concerns.",
        "Needs schema registry, idempotency, DLQs."
      ],
      "medallion":[
        "Better data quality/lineage; ↑ platform ops needs.",
        "Needs compaction strategy and cost controls."
      ],
    }[style]
    return f"""# ADR {adr_id}: Adopt {style} architecture for {system}

- **Status**: Proposed
- **Date**: {today}
- **Decision Makers**: Architecture Team
- **Context**
{context}

- **Decision**
We will adopt **{style}** for **{system}**, with the following key choices:
{chr(10).join([f"- {d}" for d in details])}

- **Consequences**
{chr(10).join([f"- {c}" for c in consequences])}

- **Alternatives considered**
- Keep current architecture (does not address pain & scale needs)
- Partial refactor only (insufficient impact)
"""

def mk_backlog(system, style, svcs):
    phases={
      "Discovery / Foundations":[
        "Inventory current services, datastores, integrations, SLAs.",
        "Define target NFRs (latency p95, availability, throughput).",
        "Stand up observability (traces, metrics, logs)."
      ],
      "Design":[],
      "Implementation (waves)":[],
      "Operations / Rollout":[
        "Canary strategy & rollback.",
        "SLOs & alerting configured.",
        "Runbook & readiness review."
      ]
    }
    if style=="microservices":
        phases["Design"]=[
          "Define bounded contexts & ownership.",
          "Define service contracts and data ownership.",
          "Choose comms (sync vs async)."
        ]
        phases["Implementation (waves)"]=[f"Extract {s} into its own deployable with DB ownership." for s in svcs]
    elif style=="event-driven":
        phases["Design"]=[
          "Define event taxonomy; topics & retention; pick broker.",
          "Specify schemas & versioning; add schema registry.",
          "Mandate Outbox for producers; idempotent consumers."
        ]
        phases["Implementation (waves)"]=[f"Make {s} a producer/consumer with idempotent handlers." for s in svcs]
    else: # medallion
        phases["Design"]=[
          "Define Bronze/Silver/Gold datasets and contracts.",
          "Plan checkpoints, schema evolution, and DQ policy.",
          "Plan compaction/OPTIMIZE & clustering."
        ]
        phases["Implementation (waves)"]=[
          "Bronze ingestion live.",
          "Silver conformance/CDC live.",
          "Gold KPIs & serving live."
        ]
    out=[f"# Migration Backlog — {system} ({style})\n"]
    for phase, items in phases.items():
        out.append(f"## {phase}")
        out.extend([f"- [ ] {i}" for i in items])
        out.append("")
    return "\n".join(out)

def mk_c4_context(system, svcs, integrations):
    lines=["C4Context","title System Context", f'Person(user, "End User")', f'System(system, "{system}")']
    for i, s in enumerate(svcs,1):
        lines += [f'System_Ext(s{i}, "{s}")', f'Rel(user, s{i}, "Uses")', f'Rel(s{i}, system, "Via API/Events")']
    for j, x in enumerate(integrations,1):
        lines += [f'System_Ext(x{j}, "{x}")', f'Rel(system, x{j}, "Integrates")']
    return "\n".join(lines)+"\n"

def mk_c4_containers(system, style, svcs, datastores):
    lines=["C4Container", f'title Containers — {system}', f'System_Boundary(system, "{system}") {{']
    if style=="medallion":
        for L in ["Bronze","Silver","Gold"]:
            lines.append(f'  Container({L.lower()}, "{L} Layer", "Delta/Parquet")')
    else:
        for i,s in enumerate(svcs,1):
            lines.append(f'  Container(s{i}, "{s}", "Service")')
    for k,d in enumerate(datastores,1):
        lines.append(f'  ContainerDb(db{k}, "{d}", "Data store")')
    lines.append("}")
    if style=="event-driven":
        lines.append('ContainerQueue(broker, "Event Broker", "Topics/Queues")')
        for i,_ in enumerate(svcs,1):
            lines.append(f'Rel(s{i}, broker, "publish/subscribe")')
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser(description="Architecture-to-Architecture transformer")
    ap.add_argument("source", help="YAML or Markdown brief of current architecture")
    ap.add_argument("--target-style", required=True, choices=["microservices","event-driven","medallion"])
    ap.add_argument("--system-name", default=None)
    ap.add_argument("--outdir", default="docs/a2a")
    ap.add_argument("--adr-id", default="0001")
    a=ap.parse_args()

    p=pathlib.Path(a.source)
    data=load_source(p)
    system= infer_system_name(data, a.system_name)
    svcs = list_service_names(data)
    datastores=[(d["name"] if isinstance(d,dict) else str(d)) for d in data.get("datastores",[])]
    integrations=[(x["name"] if isinstance(x,dict) else str(x)) for x in data.get("integrations",[])]

    outdir=pathlib.Path(a.outdir); (outdir/"adr").mkdir(parents=True, exist_ok=True); (outdir/"c4").mkdir(parents=True, exist_ok=True)

    (outdir/"adr"/f"ADR-{a.adr_id}-{a.target_style}.md").write_text(mk_adr(system,a.target_style,data,a.adr_id), encoding="utf-8")
    (outdir/"backlog.md").write_text(mk_backlog(system,a.target_style,svcs), encoding="utf-8")
    (outdir/"c4"/"context.mmd").write_text(mk_c4_context(system,svcs,integrations), encoding="utf-8")
    (outdir/"c4"/"containers.mmd").write_text(mk_c4_containers(system,a.target_style,svcs,datastores), encoding="utf-8")
    print(f"Generated ADR, backlog, and C4 skeletons under {outdir}/")

if __name__=="__main__":
    main()
