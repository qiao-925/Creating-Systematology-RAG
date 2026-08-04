<p align="center">
  <img src="assets/logo.svg" alt="Wayfinding" width="480">
</p>

Connecting the unknown to the human knowledge coordinates.

## Quick Start

```bash
doppler setup     # one-time: link to Doppler project (wayfinding / dev)
make              # install deps + start backend (:8000) & frontend (:3000)
```

> Secrets are injected by [Doppler](https://doppler.com) (`doppler run`) — there is no `.env` file.
> Model selection lives in `application.yml` (three pre-registered sources: cloud API / local Ollama / HF endpoint) and can be overridden per-environment via the `LLM_MODEL_ID` secret in Doppler.

## Usage

todo add a gif or video

Submit a question — Wayfinding lights up the relevant DDC knowledge nodes, each returning a core insight plus a pointer to the original source:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "How do fiscal subsidies affect housing affordability?"}'
```

## Documentation

| Doc | Description |
|-----|-------------|
| [ARCHITECTURE](ARCHITECTURE.md) | System design — *to be written* |
| [Decision Log](docs/decision-log.md) | Design decisions — *to be written* |
| [Constraint System](docs/constraint-system.md) | Rules / hooks / yaml — *to be written* |

*Placeholders — expanded as the V2 system lands.*
