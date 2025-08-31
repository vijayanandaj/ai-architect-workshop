#!/usr/bin/env python
"""
Advisory LLM pass for requirements linting.

- Reads a requirements YAML (same format used by req_extract.py).
- Reuses rule-based lints from tools/req_lint.py to find issues.
- For each failing requirement, asks an LLM to propose clearer, measurable wording
  (and acceptance criteria for functional reqs lacking them).
- Writes a non-blocking Markdown report to docs/reviews/lint_advice.md.

Usage:
  OPENAI_API_KEY=sk-... python tools/req_lint_llm.py samples/requirements.yaml
Env:
  OPENAI_API_KEY  -> required for LLM suggestions (otherwise advisory falls back to rule-only text)
  LLM_MODEL       -> optional (default: gpt-4o-mini)
"""
import os, sys, yaml, pathlib, datetime as dt, textwrap, importlib.util

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Load req_lint.py dynamically (no package needed)
rl_path = ROOT / "tools" / "req_lint.py"
spec = importlib.util.spec_from_file_location("req_lint", str(rl_path))
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)

def load_yaml(p):
    return yaml.safe_load(pathlib.Path(p).read_text(encoding="utf-8"))

def llm_client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None

SYSTEM_PROMPT = (
    "You are an assistant that rewrites software requirements to be clear, testable, and measurable. "
    "Use concise language, include numeric targets and units for NFRs (e.g., p95<300 ms, 99.9% availability, RTO 15m, RPO 5m), "
    "and propose 2-3 acceptance criteria for functional requirements when missing. "
    "If security is vague, include concrete controls (e.g., TLS 1.3, mTLS, OAuth2/OIDC, AES-256 at rest). "
    "Return only the rewritten requirement and, if applicable, a short bullet list of acceptance criteria."
)

def ask_llm(client, model, requirement, issues):
    if client is None:
        return None
    msg = textwrap.dedent(f"""
    Original requirement:
    {requirement.get('text','').strip()}

    Type: {requirement.get('type','').strip().lower()}
    Lint issues detected: {', '.join(issues) if issues else 'none'}

    Rewrite the requirement to resolve these issues.
    - For NFRs: include numeric thresholds and units.
    - For availability: include % (e.g., 99.9%).
    - For latency: include ms (e.g., p95<300 ms).
    - For security: name concrete controls/policies.
    - For functional requirements that lack acceptance criteria: add 2-3 concise acceptance bullets.

    Output format:
    Requirement: <one-line improved requirement>
    AcceptanceCriteria (optional):
    - <bullet 1>
    - <bullet 2>
    - <bullet 3>
    """).strip()

    try:
        resp = client.chat.completions.create(
            model=os.getenv("LLM_MODEL","gpt-4o-mini"),
            messages=[{"role":"system","content":SYSTEM_PROMPT},
                      {"role":"user","content":msg}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"(LLM error: {e})"

def main():
    yaml_file = sys.argv[1] if len(sys.argv) > 1 else "samples/requirements.yaml"
    data = load_yaml(yaml_file)
    reqs = data.get("requirements", [])

    # Collect per-requirement issues via req_lint functions
    per_req = []
    any_issues = False
    for r in reqs:
        rid = r.get("id","?")
        issues = rl.lint_req(r)
        per_req.append((rid, r, issues))
        if issues:
            any_issues = True

    conflicts = rl.detect_conflicts(reqs)

    outdir = ROOT / "docs" / "reviews"
    outdir.mkdir(parents=True, exist_ok=True)
    out_md = outdir / "lint_advice.md"

    lines = []
    lines.append(f"# Lint Advisory Report")
    lines.append(f"_Generated: {dt.date.today().isoformat()}_")
    lines.append(f"\nSource: `{yaml_file}`")
    lines.append("\n> This is **advisory only**. Your blocking gate remains `tools/req_lint.py`.\n")

    if not any_issues and not conflicts:
        lines.append("No lint issues detected by the rule-based linter. 🎉")
        out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {out_md}")
        return

    if conflicts:
        lines.append("## Cross-requirement conflicts")
        for c in conflicts:
            lines.append(f"- {c}")
        lines.append("")

    client = llm_client()
    if client is None:
        lines.append("> **Note:** OPENAI_API_KEY not set; showing rule-based issues only (no LLM rewrites).\n")

    lines.append("## Requirement-level advice")
    for rid, r, issues in per_req:
        if not issues:
            continue
        lines.append(f"### {rid}")
        lines.append(f"**Original**: {r.get('text','').strip()}")
        lines.append("**Issues:**")
        for i in issues:
            lines.append(f"- {i}")
        suggestion = ask_llm(client, os.getenv("LLM_MODEL","gpt-4o-mini"), r, issues)
        if suggestion:
            lines.append("**LLM Suggestion:**")
            lines.append(suggestion)
        lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_md}")

if __name__ == "__main__":
    main()
