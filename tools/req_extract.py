#!/usr/bin/env python
import argparse, yaml, pathlib
def parse_markdown(md:str):
    reqs=[]; rid=1
    for line in md.splitlines():
        t=line.strip()
        if not t or t.startswith("#"): continue
        reqs.append({"id": f"R{rid:03}", "type": "func" if "As a" in t else "nfr",
                     "text": t, "priority": "M", "category": None, "acceptance": []})
        rid+=1
    return {"requirements": reqs}
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("input_md"); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    data=parse_markdown(pathlib.Path(a.input_md).read_text(encoding="utf-8"))
    pathlib.Path(a.out).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"Wrote {a.out}")
