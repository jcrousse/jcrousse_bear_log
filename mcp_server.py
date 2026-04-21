#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp[cli]"]
# ///
"""MCP server for the bear log journal. Read entries by date, record new ones."""

import os
from datetime import date, datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(os.environ.get("BEAR_LOG_DATA_DIR", Path(__file__).parent / "data"))

mcp = FastMCP("bear-log")


def _date_from_string(date_str: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date '{date_str}'. Use YYYY-MM-DD, YYYYMMDD, or DD/MM/YYYY.")


def _entry_path(d: date) -> Path:
    return DATA_DIR / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.year:04d}{d.month:02d}{d.day:02d}.txt"


@mcp.tool()
def get_entry(date_str: str) -> str:
    """Fetch the journal entry for a given date. Returns the text or a not-found message.

    Args:
        date_str: Date to look up (YYYY-MM-DD, YYYYMMDD, or DD/MM/YYYY)
    """
    d = _date_from_string(date_str)
    path = _entry_path(d)
    if not path.exists():
        return f"No entry found for {d.isoformat()}."

    parts = [path.read_text(encoding="utf-8")]

    n = 1
    while True:
        variant = path.with_stem(f"{path.stem}_{n}")
        if not variant.exists():
            break
        parts.append(variant.read_text(encoding="utf-8"))
        n += 1

    if len(parts) == 1:
        return parts[0]
    return "\n\n--- entry {} ---\n\n".join(f"[Part {i+1}]:\n{p}" for i, p in enumerate(parts))


@mcp.tool()
def record_entry(date_str: str, text: str) -> str:
    """Record a new journal entry for a given date. Never overwrites existing entries.

    If an entry already exists for that date, creates a new file with _1, _2, etc. suffix.

    Args:
        date_str: Date for the entry (YYYY-MM-DD, YYYYMMDD, or DD/MM/YYYY)
        text: The journal entry text to save
    """
    d = _date_from_string(date_str)
    path = _entry_path(d)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        target = path
    else:
        n = 1
        while True:
            target = path.with_stem(f"{path.stem}_{n}")
            if not target.exists():
                break
            n += 1

    target.write_text(text, encoding="utf-8")
    return f"Entry saved to {target.relative_to(DATA_DIR)}."


if __name__ == "__main__":
    mcp.run()
