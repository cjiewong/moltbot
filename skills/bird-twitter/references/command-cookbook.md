# bird (steipete/bird) command cookbook

This file is a condensed, script-friendly subset of the upstream README.

## Identity / sanity checks

```bash
bird --version
bird help
bird help whoami
bird check
bird whoami
```

## Read a tweet

```bash
bird read <tweet-id-or-url>
# shorthand
bird <tweet-id-or-url>
# JSON
bird read <tweet-id-or-url> --json
```

## Thread and replies

```bash
bird thread <tweet-id-or-url>
bird replies <tweet-id-or-url>

# pagination + JSON
bird thread <tweet-id-or-url> --max-pages 3 --json
bird replies <tweet-id-or-url> --max-pages 3 --json
```

## Search

```bash
bird search "from:steipete" -n 5
bird search "(keyword) lang:en" -n 20 --json
```

## Mentions

```bash
bird mentions -n 5
bird mentions --user @steipete -n 5
```

## User profile tweets

```bash
bird user-tweets @steipete -n 20
bird user-tweets @steipete -n 50 --json
```

## Bookmarks

```bash
bird bookmarks -n 5
bird bookmarks --folder-id <id> -n 5
bird bookmarks --all --json
bird bookmarks --all --max-pages 2 --json
bird bookmarks --include-parent --json

bird unbookmark <tweet-id-or-url...>
```

## Likes

```bash
bird likes -n 5
bird likes --all --json
```

## Lists

```bash
bird lists --json
bird list-timeline <list-id-or-url> -n 20
bird list-timeline <list-id-or-url> --all --json
bird list-timeline <list-id-or-url> --max-pages 3 --json
```

## Following / followers

```bash
bird following -n 20
bird following --user <userId> -n 10

bird followers -n 20
bird followers --user <userId> -n 10
```

## News / trending

```bash
bird news -n 10
bird news --ai-only -n 20
bird news --sports -n 15
bird news --entertainment --ai-only -n 5

# with related tweets
bird news --with-tweets --tweets-per-item 3 -n 10

# JSON
bird news --json -n 5
bird news --json-full --ai-only -n 10
```

## Query IDs cache

```bash
bird query-ids
bird query-ids --fresh
bird query-ids --fresh --json
```

## Auth flags / env

Required cookies:
- `auth_token`
- `ct0`

Sources in priority order:
1) CLI flags: `--auth-token`, `--ct0`
2) Env vars: `AUTH_TOKEN`, `CT0` (fallback: `TWITTER_AUTH_TOKEN`, `TWITTER_CT0`)

Example:

```bash
export AUTH_TOKEN='...'
export CT0='...'

bird whoami
```
