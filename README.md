# Bear Log

A daily journal stored as plain text files, with an MCP server for reading and recording entries.

## Data structure

Entries are stored as `data/YYYY/MM/YYYYMMDD.txt`. When multiple entries exist for the same date, additional files use a `_1`, `_2`, ... suffix. Existing entries are never modified.

## Setup on a new machine

### Prerequisites

- Git (with push access to this repo)
- [uv](https://docs.astral.sh/uv/) (installed automatically by the setup script if missing)

### Steps

```bash
git clone git@github.com:jcrousse/jcrousse_bear_log.git
cd jcrousse_bear_log
chmod +x setup.sh
./setup.sh
```

The setup script installs `uv` if needed, fetches Python dependencies, and verifies the server starts.

### Run the server manually

```bash
uv run mcp_server.py
```

## Adding to OpenClaw

Run:

```
openclaw mcp set bear-log --transport stdio -- uv run /path/to/jcrousse_bear_log/mcp_server.py
```

Replace `/path/to/jcrousse_bear_log` with the actual path where you cloned the repo.

## SKILL.md

Paste the following into a `SKILL.md` file to let the bot know when and how to use this server:

```markdown
# Bear Log

Read and record daily journal entries via the bear-log MCP server.

## When to use

Use this skill when the user wants to:
- Look up a journal entry for a specific date
- Record a new journal entry for a date
- Check whether an entry exists for a given date

## Tools

### get_entry

Fetch the journal entry for a given date.

- `date_str` (required): The date to look up. Accepts YYYY-MM-DD, YYYYMMDD, or DD/MM/YYYY.
- Returns the entry text, or a message saying no entry was found.

### record_entry

Save a new journal entry. Never overwrites existing entries — if one already exists for that date, a new file is created with a _1, _2, ... suffix.

- `date_str` (required): The date for the entry. Accepts YYYY-MM-DD, YYYYMMDD, or DD/MM/YYYY.
- `text` (required): The journal entry text to save.

## Notes

- Every tool call pulls the latest changes from git before reading/writing.
- After recording an entry, the new file is committed and pushed automatically.
- Entries are plain text, stored under `data/YYYY/MM/YYYYMMDD.txt`.
```
