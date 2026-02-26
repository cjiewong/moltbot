# Discord Forum API Reference

## Forum Channel Structure

Forum channels (ChannelType.GuildForum = 15) support tags for categorization and filtering.

### Channel Object Fields

```typescript
{
  id: string;              // Channel ID
  type: 15;                // GuildForum
  name: string;            // Channel name
  available_tags: Tag[];   // Available tags for this forum
  // ... other fields
}
```

### Tag Object

```typescript
{
  id: string;              // Tag ID (Snowflake)
  name: string;            // Tag display name
  moderated: boolean;      // Whether only mods can apply
  emoji_id?: string;       // Custom emoji ID
  emoji_name?: string;     // Unicode emoji or custom emoji name
}
```

## Thread Operations

### Get Thread Info

```json
{
  "action": "thread-get",
  "channel": "discord",
  "channelId": "<forum-channel-id>",
  "threadId": "<thread-id>"
}
```

Response includes `applied_tags` array with current tag IDs.

### Create Thread in Forum

```json
{
  "action": "thread-create",
  "channel": "discord",
  "channelId": "<forum-channel-id>",
  "name": "Thread title",
  "content": "Initial message content",
  "appliedTags": ["<tag-id-1>", "<tag-id-2>"]
}
```

**Notes:**

- `appliedTags` is optional, defaults to empty
- Maximum 5 tags per thread
- Tag IDs must exist in channel's `available_tags`
- Forum threads require an initial message (via `content` or `message` field)

### Edit Thread Tags

```json
{
  "action": "thread-edit",
  "channel": "discord",
  "channelId": "<forum-channel-id>",
  "threadId": "<thread-id>",
  "appliedTags": ["<tag-id-1>", "<tag-id-2>"]
}
```

**Important:** This replaces all tags. To preserve existing tags, include them in the array.

### Get Channel Info (for available tags)

```json
{
  "action": "channel-get",
  "channel": "discord",
  "channelId": "<forum-channel-id>"
}
```

Returns channel object with `available_tags` array.

## Tag Filtering

Discord UI allows filtering threads by tags. When you update a thread's tags:

- Threads appear in tag-filtered views
- Users can click tags to see all threads with that tag
- Multiple tags create AND filtering (thread must have all selected tags)

## Best Practices

1. **Always fetch available tags first** before creating/editing threads
2. **Map tag names to IDs** - never hardcode tag IDs
3. **Preserve unrelated tags** when updating (read current tags, modify only what's needed)
4. **Limit to 5 tags** - Discord enforces this limit
5. **Handle missing tags gracefully** - tags may be deleted by moderators

## Common Errors

- `50035: Invalid Form Body` - Tag ID doesn't exist or exceeds 5 tag limit
- `50001: Missing Access` - Bot lacks permission to manage threads/tags
- `50013: Missing Permissions` - Tag is moderated and bot isn't a moderator
