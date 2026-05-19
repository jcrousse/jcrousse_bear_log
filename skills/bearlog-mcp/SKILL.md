# Bear Log MCP — Journal Skill

Use the `bear-log` MCP server to read and write daily journal entries. All entries are plain text in French, stored as files under `data/YYYY/MM/YYYYMMDD.txt`.

## Available tools

### `get_entry(date_str)`
Fetch a single entry by date. Accepts `YYYY-MM-DD`, `YYYYMMDD`, or `DD/MM/YYYY`.

### `record_entry(date_str, text)`
Save a journal entry for a given date. If an entry already exists, appends to it. Store the user's text **verbatim** — no spelling, grammar, or style corrections.

### `get_same_day_previous_years(date_str)`
Fetch all entries from the same day/month across every previous year in a single call. Returns entries labeled by date, or a message if none exist. This is the primary tool for the daily recap.

### `fetch_last_n(n)`
Fetch all entries from the past `n` days (including today). Returns them newest-first with date headers.

## Ideas for later

The user can send ideas or notes throughout the day without triggering a journal entry. When the user signals this (e.g. "idée pour plus tard", "note pour ce soir", "à inclure"), acknowledge briefly and **do not** call `record_entry`. These messages stay in the conversation history and are surfaced during the daily prompt.

## Daily prompt workflow (20h)

1. Call `get_same_day_previous_years` with today's date.
2. If past entries are returned:
   - Present a 2-3 sentence summary of what was happening.
   - Quote each past entry in full, labeled by year.
3. Review the day's conversation messages for any ideas or notes flagged for later. If there are any, present them as a reminder list.
4. Ask the user if they want to record today's entry.
5. When the user dictates an entry, call `record_entry` with today's date and the text exactly as given.

## Rules

- **Never alter entries.** Store exactly what the user says, mistakes included.
- **Never suggest edits** to an entry after recording it.
- **Language:** all communication and all entries are in French.
- **Date formats:** the MCP server accepts `YYYY-MM-DD`, `YYYYMMDD`, or `DD/MM/YYYY`. Pick whichever is convenient; `YYYY-MM-DD` is preferred for consistency.
- **Git sync:** the MCP server handles git pull/commit/push automatically. No manual git operations needed.
