# Architecture

All architecture diagrams are embedded in [README.md](../README.md#architecture--data-sovereignty).

## Security & Data Sovereignty Comparison

| Aspect | OpenRouter | Anthropic Direct | Local LLM (Custom) |
| --- | --- | --- | --- |
| Data Location | OpenRouter infra (US) | Anthropic infra (US) | Municipal infrastructure |
| Network Exposure | Internet traffic | Internet traffic | Internal traffic only |
| Third-party Trust | Required (OpenRouter) | Required (Anthropic) | Not required |
| GDPR Compliance | Depends on provider | Depends on Anthropic | Full control |
| Audit Trail | Limited | Limited | Complete control |
| Model Selection | 30+ models | Claude only | Any local model |
| Cost Model | Pay-per-use | Pay-per-use | Fixed infrastructure cost |
| Latency | Internet dependent | Internet dependent | Local network speed |
| GPU Required | No | No | Yes |
