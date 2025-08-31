# Architecture→Architecture (A→A) Transformer

Generate a draft **ADR**, **migration backlog**, and **C4 (Mermaid)** skeletons from a source brief.

## Usage
# from repo root
python tools/a2a_transform.py samples/source_architecture.yaml --target-style microservices --system-name ShopPlus
python tools/a2a_transform.py samples/source_architecture.yaml --target-style event-driven --system-name ShopPlus
python tools/a2a_transform.py samples/source_architecture.yaml --target-style medallion --system-name ShopPlus

Outputs → docs/a2a/ :
- adr/ADR-0001-<style>.md
- backlog.md
- c4/context.mmd, c4/containers.mmd
