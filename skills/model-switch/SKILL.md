---
name: model-switch
description: Switch OpenClaw default model between openai-codex/gpt-5.2 and minimax/MiniMax-M2.5, or check the current model. Use when the user says “切换模型/换模型”, “切到 openai-codex/codex”, “切到 minimax/minmax”, or “当前是什么模型/查看当前模型/status”.
---

# Model switch

Use the bundled script to switch the OpenClaw default model.

## Commands

Run:

- `bash scripts/switch-model.sh status`
- `bash scripts/switch-model.sh openai-codex` (→ openai-codex/gpt-5.2)
- `bash scripts/switch-model.sh minimax` (→ minimax/MiniMax-M2.5)

The script updates `agents.defaults.model.primary` and triggers a gateway reload/restart so the change takes effect.
