#!/usr/bin/env python
import argparse, yaml, pathlib, re
def infer_entities(reqs):
    ents=set()
    for r in reqs:
        for w in re.findall(r"[A-Za-z_]{4,}", r["text"]):
            if w.lower() in {"user","system","must","view","handle","error","trace","alert"}: continue
            ents.add(w.capitalize())
    return sorted(list(ents))[:8]
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("yaml_file"); ap.add_argument("--out", required=True)
    a=ap.parse_args()
    reqs = yaml.safe_load(pathlib.Path(a.yaml_file).read_text())["requirements"]
    ents = infer_entities(reqs)
    lines=["erDiagram"]
    for e in ents: lines.append(f"  {e} {{\n    string id\n  }}")
    mmd="\n".join(lines)+"\n"
    pathlib.Path(a.out).write_text(mmd, encoding="utf-8")
    print(f"Wrote {a.out} (Mermaid ER)")
