# ADR 010: Select event-driven architecture — Event-driven microservices + Kafka

- **Status**: Proposed
- **Date**: 2025-08-31
- **System**: ShopPlus

## Context
- We compared multiple candidate architectures using weighted NFR scoring.
- Hard constraints: availability_pct, security_score

## Decision
We will adopt **Event-driven microservices + Kafka** (event-driven) based on the highest overall score (0.843) and satisfaction of hard constraints.

## Consequences
- Looser coupling and replay; decoupled scale.
- Eventual consistency; schema and DLQ governance required.

## Trade-offs & Scores
- performance_p95_ms: 0.85 (raw=320)
- availability_pct: 0.96 (raw=99.95)
- cost_monthly_usd: 0.76 (raw=6800)
- operability_score: 0.75 (raw=4)
- scalability_score: 1.00 (raw=5)
- security_score: 1.00 (raw=5)
- time_to_market_weeks: 0.50 (raw=14)

## Alternatives considered
- Microservices on AKS + API Gateway — score 0.839
- Monolith on AKS + Postgres — score 0.745
