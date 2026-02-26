#!/usr/bin/env python3
"""
Create a new task thread in a Discord forum channel with tags.

Usage:
    python3 create_task_thread.py <channel_id> <title> [--model MODEL] [--status STATUS]

Arguments:
    channel_id    Forum channel ID
    title         Task title/name

Options:
    --model       Model tag name (default: openai-codex)
    --status      Status tag name (default: 进行中)
    --content     Initial message content (default: uses title)

Example:
    python3 create_task_thread.py 1476577699232223495 "Implement user auth" --model minimax
    python3 create_task_thread.py 1476577699232223495 "Fix bug #123" --status 待处理
"""

import sys
import json
import argparse
import subprocess


def get_available_tags(channel_id: str) -> list:
    """Fetch available tags from forum channel."""

    payload = {
        "action": "channel-get",
        "channel": "discord",
        "channelId": channel_id
    }

    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--json", json.dumps(payload)],
            capture_output=True,
            text=True,
            check=True
        )
        channel_info = json.loads(result.stdout)
        return channel_info.get("available_tags", [])
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error fetching tags: {e}", file=sys.stderr)
        sys.exit(1)


def find_tag_id(tags: list, tag_name: str) -> str | None:
    """Find tag ID by name (case-insensitive)."""

    tag_name_lower = tag_name.lower()
    for tag in tags:
        if tag.get("name", "").lower() == tag_name_lower:
            return tag["id"]
    return None


def create_thread(channel_id: str, title: str, content: str, tag_ids: list[str]) -> dict:
    """Create a new forum thread with tags."""

    payload = {
        "action": "thread-create",
        "channel": "discord",
        "channelId": channel_id,
        "name": title,
        "content": content,
        "appliedTags": tag_ids
    }

    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--json", json.dumps(payload)],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error creating thread: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new task thread in Discord forum with tags"
    )
    parser.add_argument("channel_id", help="Forum channel ID")
    parser.add_argument("title", help="Task title")
    parser.add_argument("--model", default="openai-codex", help="Model tag name (default: openai-codex)")
    parser.add_argument("--status", default="进行中", help="Status tag name (default: 进行中)")
    parser.add_argument("--content", help="Initial message content (default: uses title)")

    args = parser.parse_args()

    # Get available tags
    print(f"📋 Fetching available tags from channel {args.channel_id}...")
    available_tags = get_available_tags(args.channel_id)

    if not available_tags:
        print("❌ No tags available in this forum channel.", file=sys.stderr)
        sys.exit(1)

    # Find tag IDs
    model_tag_id = find_tag_id(available_tags, args.model)
    status_tag_id = find_tag_id(available_tags, args.status)

    tag_ids = []
    if model_tag_id:
        tag_ids.append(model_tag_id)
        print(f"✅ Found model tag: {args.model} (ID: {model_tag_id})")
    else:
        print(f"⚠️  Model tag '{args.model}' not found, skipping...")

    if status_tag_id:
        tag_ids.append(status_tag_id)
        print(f"✅ Found status tag: {args.status} (ID: {status_tag_id})")
    else:
        print(f"⚠️  Status tag '{args.status}' not found, skipping...")

    if not tag_ids:
        print("❌ No valid tags found. Thread will be created without tags.", file=sys.stderr)

    # Create thread
    content = args.content or f"Starting work on: {args.title}"
    print(f"\n🚀 Creating thread: {args.title}")
    print(f"📝 Content: {content}")
    print(f"🏷️  Tags: {len(tag_ids)} tag(s)")

    thread_info = create_thread(args.channel_id, args.title, content, tag_ids)

    print(f"\n✅ Thread created successfully!")
    print(f"🆔 Thread ID: {thread_info.get('id')}")
    print(f"🔗 Jump to thread: https://discord.com/channels/{thread_info.get('guild_id')}/{thread_info.get('id')}")


if __name__ == "__main__":
    main()
