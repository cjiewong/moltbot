---
name: bird-twitter
description: Use the @steipete/bird CLI ("bird") to read/search/bookmark/collect tweets and timelines from X/Twitter via the undocumented web GraphQL API (cookie auth). Use when the user asks to install/configure/run bird, troubleshoot auth_token/ct0 cookie issues, run common commands (whoami, read, thread, replies, search, user-tweets, bookmarks, likes, news/trending, lists), or automate exports with --json/--all/--max-pages.
---

# bird-twitter (steipete/bird)

## Quick start

1) Ensure `bird` is installed:

```bash
bird --version
# If missing:
npm install -g @steipete/bird
```

2) Authenticate (recommended on servers): supply cookies explicitly.

- Required cookies: `auth_token` and `ct0` from a logged-in browser session on `https://x.com`.
- Provide them via env vars (preferred) or CLI flags.

```bash
export AUTH_TOKEN='...'
export CT0='...'

bird check
bird whoami
```

3) Run common reads/exports:

```bash
bird read https://x.com/<user>/status/<id>
bird thread <id-or-url>
bird replies <id-or-url> --max-pages 3 --json
bird search "from:steipete" -n 5 --json
bird user-tweets @steipete -n 20 --json
bird bookmarks --all --json
bird likes -n 10
bird news --ai-only -n 10 --json
```

## Authentication workflow (server-friendly)

Preferred pattern: store secrets in a local file with strict permissions and `source` it.

```bash
mkdir -p ~/.config/bird
cat > ~/.config/bird/secret-env.sh <<'EOF'
export AUTH_TOKEN='...'
export CT0='...'
EOF
chmod 600 ~/.config/bird/secret-env.sh

source ~/.config/bird/secret-env.sh
bird whoami
```

### Local setup note (this machine)

On this host, the credentials file already exists at:

```bash
source ~/.config/bird/secret-env.sh
bird check
```

Credential resolution order (important for debugging):

1. CLI flags: `--auth-token`, `--ct0`
2. Env vars: `AUTH_TOKEN`, `CT0` (fallback: `TWITTER_AUTH_TOKEN`, `TWITTER_CT0`)
3. Browser cookie extraction (macOS-oriented; usually not available on headless Linux)

## Output + pagination conventions

- `--json` outputs tweet objects.
- For paginated endpoints (`--all`, `--cursor`, `--max-pages`, or some `-n` values), JSON output is usually:

```json
{ "tweets": [...], "nextCursor": "..." }
```

Useful flags:

- `--all`: fetch all pages (can be slow / risk blocks)
- `--max-pages N`: cap pages
- `--cursor <string>`: resume
- `--delay ms`: slow down between pages to reduce rate limits
- `--plain`: stable output (no emoji/color)

## Troubleshooting checklist

### "Permission denied" on `bird`

- If the `bird` you installed is a macOS Homebrew binary (Mach-O), it will not run on Linux.
- On Linux servers, install via npm:

```bash
npm install -g @steipete/bird
which bird
file "$(which bird)"
```

### Missing credentials

If `bird check` shows missing `auth_token` / `ct0`:

- Ensure you exported `AUTH_TOKEN` and `CT0` in the same shell session.
- Or pass them explicitly:

```bash
bird --auth-token "$AUTH_TOKEN" --ct0 "$CT0" whoami
```

### Blocks / breakage

This tool uses undocumented endpoints and can break anytime. Prefer read-only commands; tweeting may trigger automated-request blocks.

## References

- For a compact command cookbook: read `references/command-cookbook.md`.
