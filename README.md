<p align="center">
  <img src="assets/logo.svg" alt="Wayfinding" width="480">
</p>

Your questions. Your map. Your way.


## Quick Start

```bash
doppler setup     # one-time: link to Doppler project (wayfinding / dev)
make              # install deps + start backend (:8000) & frontend (:3000)
```

> Secrets are injected by [Doppler](https://doppler.com) (`doppler run`) — there is no `.env` file.
> Model selection lives in `application.yml` (three pre-registered sources: cloud API / local Ollama / HF endpoint) and can be overridden per-environment via the `LLM_MODEL_ID` secret in Doppler.

## What it support?

- 可质疑的结构
- 以人为本：图是可编辑的，AI实时人类采集编辑并反馈——这是系统级的设计闭环。

SD自身目标（Forrester / Meadows 背书）：
Forrester：「用仿真展示为什么系统能够这样运行，识别可改进的政策」——启示，不是代劳。
Meadows《杠杆点》：杠杆点是SD核心；高杠杆在「软」处（信息流、规则、目标、范式），没有参数。
SD从出生就是人机良好学习：团体模型搭建/飞行模拟器/双环学习。
本项目=完成一人版建模工坊：把SD靠「资深专家+建模工坊」的启发过程，用LLM压成一个人可用。

像构建一个新应用那样思考！

输入问题
领域定位，数据搜索11  
SD分析
输出可质疑的结构，杠杆点等

## Usage

我我我s
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
