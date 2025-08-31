# ADR Decision Maker — NFR-Weighted Architecture Selection

This mini-toolchain helps you choose among architecture options (monolith, microservices, event-driven, etc.) using **explicit Non-Functional Requirements (NFR) priorities**. It generates a **ranked report** and an **ADR** you can review and tweak.

---

## Why this is useful

- **Forces clarity.** Captures *Context → Decision → Consequences → Alternatives* every time—no tribal memory.
- **Consistency.** Same structure & terminology across teams; faster reviews.
- **Traceability.** ADRs are tied to inputs (weights, targets, constraints, metrics), so you can show *why* an option won.
- **Speed.** You edit the inputs; the tools draft the report/ADR. You finalize the narrative.

---

## What gets automated

1) **Score & rank** candidate architectures against your NFR priorities.  
2) **Generate a Markdown ADR** for the top option.  
3) *(Optional)* Use the winner to generate A→A artifacts (ADR + backlog + C4 skeletons).

---

## Inputs (you edit these)

All inputs live in `samples/decision/` and `samples/`.

### 1) NFR Profile — `samples/decision/nfr_profile.yaml`
- **weights**: how important each metric is (sums to ~1; we normalize anyway).  
- **targets / bounds**: desired values and allowed range per metric.  
- **hard_constraints**: must-pass gates (e.g., `availability_pct ≥ 99.5`).

Example:
```yaml
system: "ShopPlus"
weights:
  performance_p95_ms: 0.25
  availability_pct: 0.20
  cost_monthly_usd: 0.15
  operability_score: 0.10
  scalability_score: 0.10
  security_score: 0.10
  time_to_market_weeks: 0.10
targets:
  performance_p95_ms: 300
  availability_pct: 99.9
  cost_monthly_usd: 3000
  operability_score: 4
  scalability_score: 4
  security_score: 4
  time_to_market_weeks: 8
bounds:
  performance_p95_ms: [200, 1000]
  availability_pct:   [99.0, 99.99]
  cost_monthly_usd:   [1000, 25000]
  operability_score:  [1, 5]
  scalability_score:  [1, 5]
  security_score:     [1, 5]
  time_to_market_weeks: [2, 26]
hard_constraints:
  - metric: availability_pct
    min: 99.5
  - metric: security_score
    min: 3

