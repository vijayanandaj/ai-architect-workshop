#!/usr/bin/env python
import json, sys, pathlib, subprocess
scores = json.loads(pathlib.Path('docs/decisions/decision_scores.json').read_text())
best = scores['scored'][0]
kind = (best.get('kind','') or '').lower()
style = {'microservices':'microservices','event-driven':'event-driven','monolith':'microservices'}.get(kind,'microservices')
system = scores['profile'].get('system','System')
print(f"Best: {best['name']} ({kind}) → generating A→A for style={style}")
subprocess.check_call([sys.executable,'tools/a2a_transform.py','samples/source_architecture.yaml','--target-style',style,'--system-name',system])
