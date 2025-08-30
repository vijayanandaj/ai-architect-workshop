# AI Architect Workshop — Template-ready

A code-backed training repo for **architects** to use GenAI + automation for requirements, design, ADRs, compliance checks, and governance.

- **Format:** 3 days
- **Audience:** Enterprise / Solution / Domain Architects, senior tech leads
- **Outcomes:** Faster & clearer requirements, AI-assisted design docs/ADRs, risk & compliance checks, living architecture docs
- **Pre-reqs:** Python 3.11+, VS Code; *no Java required*

> See **[Program Overview](docs/overview.md)** and the **[3-Day Agenda](docs/agenda.md)**.

## Quick Start (local)
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Run sample pipeline on provided example:
python tools/req_extract.py samples/requirements_sample.md --out samples/requirements.yaml
python tools/req_validate.py samples/requirements.yaml
python tools/req_lint.py samples/requirements.yaml
python tools/generate_mermaid_er.py samples/requirements.yaml --out docs/er.mmd
pytest -q

