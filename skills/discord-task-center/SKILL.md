---
name: discord-task-center
description: Manage AI tasks using Discord Forum channel tags. Use when working with Discord Forum channels to (1) switch AI models via tags, (2) archive tasks by updating tags, (3) create new task threads with proper tags. Triggers on requests like "switch to opus", "archive this task", "create a new task for X".
---

# Discord Task Center

Manage AI tasks using Discord Forum channel tags as a lightweight task management system.

## Core Capabilities

### 1. Dynamic Model Switching via Tags

Read the current thread's tags to determine which AI model to use, and update tags to switch models for future conversations.

**Supported models:**

- `openai-codex/gpt-5.2` (default) - OpenAI Codex model
- `minimax/MiniMax-M2.5` - MiniMax model

**How it works:**

1. Read thread tags using `message` tool with `action: "thread-get"`
2. Look for model tags in `applied_tags` field
3. Switch model by editing thread tags with `action: "thread-edit"` and `appliedTags` parameter

**Example workflow:**

```json
// 1. Get current thread info
{
  "action": "thread-get",
  "channel": "discord",
  "channelId": "1476577699232223495",
  "threadId": "123456789"
}

// 2. Update tags to switch model
{
  "action": "thread-edit",
  "channel": "discord",
  "channelId": "1476577699232223495",
  "threadId": "123456789",
  "appliedTags": ["tag-id-for-opus", "tag-id-for-in-progress"]
}
```

### 2. Task Status Management

Update thread tags to reflect task status (进行中, 已归档, 待处理, etc.).

**Common status tags:**

- `进行中` (In Progress) - Active tasks
- `已归档` (Archived) - Completed/archived tasks
- `待处理` (Pending) - Tasks waiting to start

**When user says "归档这个任务" (archive this task):**

1. Get current thread info
2. Replace status tag with "已归档" tag
3. Confirm the update

### 3. Automatic Task Creation

Create new Forum threads with appropriate model and status tags.

**Default configuration:**

- Model: `openai-codex/gpt-5.2`
- Status: `进行中` (In Progress)

**When user says "新建一个任务" (create a new task):**

1. Ask for task title/description if not provided
2. Get available tags from the forum channel
3. Create thread with `action: "thread-create"` and `appliedTags` parameter
4. Start working on the task in the new thread

**Example:**

```json
{
  "action": "thread-create",
  "channel": "discord",
  "channelId": "1476577699232223495",
  "name": "Task: Implement user authentication",
  "content": "Starting work on user authentication feature",
  "appliedTags": ["tag-id-for-openai-codex", "tag-id-for-in-progress"]
}
```

## Tag Management

### Getting Available Tags

Before creating or editing threads, fetch the forum channel's available tags:

```json
{
  "action": "channel-get",
  "channel": "discord",
  "channelId": "1476577699232223495"
}
```

Response includes `available_tags` array with tag IDs and names.

### Tag ID Mapping

Always map tag names to IDs before using `appliedTags`:

- Read `available_tags` from channel info
- Find matching tag by name
- Use the tag's `id` field in `appliedTags` array

**Important:** `appliedTags` accepts tag IDs (Snowflakes), not tag names. Maximum 5 tags per thread.

## Implementation Notes

- Forum threads automatically create when posting to a forum channel
- Tags are immutable once created (can only apply/remove, not rename)
- Model switching takes effect on the next conversation turn
- Always preserve non-model, non-status tags when updating
- Use `references/discord-api.md` for detailed API documentation

## Common Patterns

**Pattern 1: Check current model**

```
User: "What model am I using?"
Agent: Read thread tags → identify model tag → respond with model name
```

**Pattern 2: Switch model mid-conversation**

```
User: "Switch to MiniMax for this task"
Agent: Get thread info → find MiniMax tag ID → update appliedTags → confirm switch
```

**Pattern 3: Archive completed task**

```
User: "Archive this task"
Agent: Get thread info → replace status tag with "已归档" → confirm archival
```

**Pattern 4: Create task with specific model**

```
User: "Create a new task using MiniMax"
Agent: Get available tags → create thread with MiniMax + 进行中 tags → start working
```

## Resources

### references/

- `discord-api.md` - Discord API reference for forum channels and tags
- `model-mapping.md` - Model name to tag name mapping reference

### scripts/

- `get_forum_tags.py` - Utility to fetch and display forum channel tags
- `create_task_thread.py` - Helper script for creating threads with tags
