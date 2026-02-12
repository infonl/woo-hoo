# Architecture Diagrams

## Diagram Files

The following Mermaid diagram files are available in `docs/diagrams/`:

- **current-architecture.mmd** - Current Architecture (OpenRouter Only)
- **proposed-architecture.mmd** - Proposed Architecture (Local LLM Support)
- **data-flow-comparison.mmd** - Data Flow Comparison
- **implementation-architecture.mmd** - Implementation Architecture
- **system-overview.mmd** - System Overview (from README)
- **data-sovereignty-comparison.mmd** - Data Sovereignty Comparison (from README)

## Security & Data Sovereignty Benefits

| Aspect               | Current (OpenRouter) | Local LLM               |
|----------------------|----------------------|-------------------------|
| Data Location        | US infrastructure (OpenRouter) | Municipal infrastructure |
| Network Exposure     | Internet traffic required | Internal traffic only |
| Third-party Trust    | Required (OpenRouter) | Not required |
| GDPR Compliance      | Depends on OpenRouter | Full control |
| Audit Trail          | Limited (OpenRouter logs) | Complete control |
| Custom Models        | Limited to OpenRouter catalog | Any local model |
| Cost Control         | Pay-per-use | Fixed infrastructure cost |
| Latency              | Internet dependent | Local network speed |
