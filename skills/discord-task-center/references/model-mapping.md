# Model to Tag Mapping

## Default Model

- **Model**: `openai-codex/gpt-5.2`
- **Tag Name**: `openai-codex` or `codex` or `gpt-5.2`
- **Use Case**: Default model for new tasks

## Supported Models

### Available Models

| Model ID               | Tag Name Options                     | Description                  |
| ---------------------- | ------------------------------------ | ---------------------------- |
| `openai-codex/gpt-5.2` | `openai-codex`, `codex`, `gpt-5.2`   | OpenAI Codex model (default) |
| `minimax/MiniMax-M2.5` | `minimax`, `MiniMax`, `MiniMax-M2.5` | MiniMax model                |

## Status Tags

| Tag Name | Meaning     | Use Case                     |
| -------- | ----------- | ---------------------------- |
| `进行中` | In Progress | Active tasks being worked on |
| `已归档` | Archived    | Completed or archived tasks  |
| `待处理` | Pending     | Tasks waiting to start       |
| `已完成` | Completed   | Successfully finished tasks  |
| `暂停`   | Paused      | Temporarily suspended tasks  |

## Tag Naming Conventions

- **Model tags**: Use short, recognizable names (`openai-codex`, `minimax`, `gpt-5.2`, `MiniMax-M2.5`)
- **Status tags**: Use Chinese for consistency with user's language
- **Custom tags**: Keep under 20 characters for readability

## Mapping Logic

When user requests a model switch:

1. **Parse user intent**:
   - "switch to minimax" → `minimax/MiniMax-M2.5`
   - "use codex" → `openai-codex/gpt-5.2`
   - "change to openai-codex" → `openai-codex/gpt-5.2`
   - "切到 minimax" → `minimax/MiniMax-M2.5`

2. **Find corresponding tag**:
   - Look up model ID in mapping table
   - Get tag name options from table (case-insensitive)
   - Search forum's `available_tags` for matching name

3. **Update thread tags**:
   - Preserve non-model tags (status, custom tags)
   - Replace old model tag with new model tag
   - Apply changes via `thread-edit` action

## Example Workflow

```
User: "切换到 MiniMax"

1. Parse: "minimax" → minimax/MiniMax-M2.5
2. Map: minimax/MiniMax-M2.5 → tag name options: "minimax", "MiniMax", "MiniMax-M2.5"
3. Get available tags from forum channel
4. Find tag with name matching any option (case-insensitive) → get tag ID
5. Get current thread tags
6. Replace model tag, keep status tag
7. Update thread with new appliedTags array
```

## Fallback Behavior

If requested model tag doesn't exist:

1. Inform user the tag is not available
2. List available model tags (openai-codex, minimax)
3. Ask user to choose from available options
4. Do not create new tags automatically (requires moderator permissions)

## Model Detection

When reading thread tags to determine current model:

- Look for tags matching known model names (openai-codex, codex, gpt-5.2, minimax, MiniMax, MiniMax-M2.5)
- Case-insensitive matching
- If no model tag found, assume default (openai-codex/gpt-5.2)
- If multiple model tags found, use the first one and warn user

## Integration with OpenClaw Config

The model IDs match OpenClaw's configuration:

- `agents.defaults.model.primary` = `openai-codex/gpt-5.2` (default)
- Available providers: `openai-codex`, `minimax`
- Model aliases: `minimax/MiniMax-M2.1` → alias "Minimax"
