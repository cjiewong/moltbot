#!/usr/bin/env python3
"""
Get and display forum channel tags.

Usage:
    python3 get_forum_tags.py <channel_id>

Example:
    python3 get_forum_tags.py 1476577699232223495
"""

import sys
import json
import subprocess


def get_forum_tags(channel_id: str) -> dict:
    """Fetch forum channel info including available tags."""

    # Use OpenClaw message tool to get channel info
    payload = {
        "action": "channel-get",
        "channel": "discord",
        "channelId": channel_id
    }

    # Call via openclaw CLI (assumes openclaw is in PATH)
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--json", json.dumps(payload)],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching channel info: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: openclaw command not found. Is OpenClaw installed?", file=sys.stderr)
        sys.exit(1)


def display_tags(channel_info: dict):
    """Display available tags in a readable format."""

    channel_name = channel_info.get("name", "Unknown")
    available_tags = channel_info.get("available_tags", [])

    print(f"\n📋 Forum Channel: {channel_name}")
    print(f"🆔 Channel ID: {channel_info.get('id')}")
    print(f"\n🏷️  Available Tags ({len(available_tags)}):\n")

    if not available_tags:
        print("  No tags available in this forum channel.")
        return

    # Group tags by category (model vs status vs other)
    model_tags = []
    status_tags = []
    other_tags = []

    for tag in available_tags:
        tag_name = tag.get("name", "").lower()
        if any(model in tag_name for model in ["gpt", "opus", "sonnet", "haiku", "claude"]):
            model_tags.append(tag)
        elif any(status in tag_name for status in ["进行中", "已归档", "待处理", "完成", "暂停"]):
            status_tags.append(tag)
        else:
            other_tags.append(tag)

    # Display model tags
    if model_tags:
        print("  🤖 Model Tags:")
        for tag in model_tags:
            emoji = f" {tag['emoji_name']}" if tag.get('emoji_name') else ""
            print(f"    • {tag['name']}{emoji} (ID: {tag['id']})")
        print()

    # Display status tags
    if status_tags:
        print("  📊 Status Tags:")
        for tag in status_tags:
            emoji = f" {tag['emoji_name']}" if tag.get('emoji_name') else ""
            print(f"    • {tag['name']}{emoji} (ID: {tag['id']})")
        print()

    # Display other tags
    if other_tags:
        print("  🔖 Other Tags:")
        for tag in other_tags:
            emoji = f" {tag['emoji_name']}" if tag.get('emoji_name') else ""
            moderated = " [MODERATED]" if tag.get('moderated') else ""
            print(f"    • {tag['name']}{emoji}{moderated} (ID: {tag['id']})")
        print()


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    channel_id = sys.argv[1]

    print(f"Fetching tags for channel {channel_id}...")
    channel_info = get_forum_tags(channel_id)
    display_tags(channel_info)


if __name__ == "__main__":
    main()
