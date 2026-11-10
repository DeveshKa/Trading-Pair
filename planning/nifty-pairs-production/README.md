# Nifty pairs trading planning package

Start with [the full plan](production-plan.md). The editable Word version is [in the explanation folder](../../explanation/Nifty%20Pairs%20-%20Production%20System%20Plan.docx).

- [Source probes](source_probe.json): actual archive retrieval metadata and observed schemas.
- [Initial research configuration](initial-research-config.yaml): proposed values with live orders and notifications disabled.
- [Architecture and failure behavior](architecture.md): component diagram, decisions and recovery boundaries.
- [Implementation backlog](backlog.csv): sequenced work, dependencies and acceptance criteria.

Status: planning complete; full data audit, statistical pair discovery, backtests, deployment and notification activation remain implementation work. No ranked live pair or return claim has been produced. Research defaults assume Nifty 50 and daily confirmed signals; configurable expansion follows audited coverage.
