<p align="center">
  <img src="assets/logo.svg" alt="Wayfinding" width="480">
</p>

Connecting the unknown to the human knowledge coordinates.

## Quick Start

```bash
make env-pull     # pull & decrypt API keys
make              # install deps + run tests
make run          # start frontend → http://localhost:3000
```

> Manual setup: `cp .env.example .env`, then fill in at least one LLM key (`DEEPSEEK_API_KEY`, `MIMO_API_KEY`, or `KIMI_API_KEY`).

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
