#!/usr/bin/env python3
"""Split daily journal entries from yearly raw files into individual day files.

Target structure: data/YYYY/mm/YYYYmmDD.txt

Step 1: Identify and report the various date formats found in the raw files
Step 2: Parse entries and write each daily paragraph to its own file
Step 3: Print all missing/gap dates
"""

import re
import os
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data")

MONTH_MAP = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}

MONTH_NAMES_PAT = "|".join(MONTH_MAP.keys())
DAY_NAMES_PAT = r"(?:Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)"

# Known typos in the source files: (filename, original_line) -> fixed_line
KNOWN_TYPOS = {
    ("2025.txt", "Samedi 06/0692025"): "Samedi 06/09/2025",
}

# Patterns ordered from most specific to least specific
PATTERNS = [
    # 1: [DayName] DD/MM/YYYY — numeric with full year (2 or 4 digits)
    #    Handles: "01/10/2023", "Lundi 01/01/2024", "25/01.2026", "01/11/25"
    #    Optional trailing colon, period, or " - NNN jours" etc.
    (
        re.compile(
            rf"^{DAY_NAMES_PAT}?\s*(\d{{1,2}})[/.](\d{{1,2}})[/.](\d{{2,4}})\s*[:.]*\s*(?:[-–].*)?$",
            re.IGNORECASE,
        ),
        "numeric_dmy",
    ),
    # 2: DayName DDer? MonthName YYYY — text month with year
    #    Handles: "Mercredi 1er Janvier 2025", "Mardi 3 juin 2025"
    (
        re.compile(
            rf"^{DAY_NAMES_PAT}\s+(\d{{1,2}})(?:er)?\s+({MONTH_NAMES_PAT})\s+(\d{{4}})\s*[:.]*\s*(?:[-–].*)?$",
            re.IGNORECASE,
        ),
        "text_dmy",
    ),
    # 3: DayName DDer? MonthName — text month, no year
    #    Handles: "Dimanche 5 janvier", "Jeudi 21 Novembre", "Dimanche 1er décembre."
    #    Also handles trailing " - NNN" or " -NNN" or ". -- NNN"
    (
        re.compile(
            rf"^{DAY_NAMES_PAT}\s+(\d{{1,2}})(?:er)?\s+({MONTH_NAMES_PAT})\s*[:.]*\s*(?:[-–].*)?$",
            re.IGNORECASE,
        ),
        "text_dm",
    ),
    # 4: DayName DD/MM — numeric without year
    #    Handles: "Jeudi 28/08"
    (
        re.compile(
            rf"^{DAY_NAMES_PAT}\s+(\d{{1,2}})[/.](\d{{1,2}})\s*[:.]*\s*(?:[-–].*)?$",
            re.IGNORECASE,
        ),
        "numeric_dm",
    ),
    # 5: DayName DD — day number only
    #    Handles: "Mercredi 22", "Jeudi 23", "Lundi 27 - 484 jours"
    (
        re.compile(
            rf"^{DAY_NAMES_PAT}\s+(\d{{1,2}})\s*[:.]*\s*(?:[-–].*)?$",
            re.IGNORECASE,
        ),
        "day_only",
    ),
]


def parse_date_line(line, file_year, prev_month):
    """Try to parse a date from a line.

    Returns (date_obj, format_name) or None.
    """
    line = line.strip()
    if not line:
        return None

    for pattern, fmt_name in PATTERNS:
        m = pattern.match(line)
        if not m:
            continue

        try:
            if fmt_name == "numeric_dmy":
                day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if year < 100:
                    year += 2000
            elif fmt_name == "text_dmy":
                day = int(m.group(1))
                month = MONTH_MAP[m.group(2).lower()]
                year = int(m.group(3))
            elif fmt_name == "text_dm":
                day = int(m.group(1))
                month = MONTH_MAP[m.group(2).lower()]
                year = file_year
            elif fmt_name == "numeric_dm":
                day, month = int(m.group(1)), int(m.group(2))
                year = file_year
            elif fmt_name == "day_only":
                day = int(m.group(1))
                month = prev_month if prev_month else 1
                year = file_year
            else:
                continue

            return date(year, month, day), fmt_name
        except ValueError:
            continue

    return None


def process_file(filepath, file_year):
    """Process a single raw file. Returns list of (date, text) and set of (fmt, example)."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # Apply known typo fixes
    filename = filepath.name
    lines = []
    for raw_line in raw_lines:
        stripped = raw_line.strip()
        key = (filename, stripped)
        if key in KNOWN_TYPOS:
            lines.append(KNOWN_TYPOS[key] + "\n")
        else:
            lines.append(raw_line)

    entries = []
    formats_seen = set()
    current_date = None
    current_text_lines = []
    prev_month = None

    for line in lines:
        result = parse_date_line(line, file_year, prev_month)

        if result:
            if current_date is not None:
                text = "\n".join(current_text_lines).strip()
                if text:
                    entries.append((current_date, text))

            current_date, fmt_name = result
            prev_month = current_date.month
            formats_seen.add((fmt_name, line.strip()))
            current_text_lines = []
        else:
            if current_date is not None:
                current_text_lines.append(line.rstrip("\n"))

    if current_date is not None:
        text = "\n".join(current_text_lines).strip()
        if text:
            entries.append((current_date, text))

    return entries, formats_seen


def main():
    all_entries = []
    all_formats = defaultdict(list)

    # ── Step 1: Identify date formats ──
    print("=" * 70)
    print("STEP 1: Date formats identified in each file")
    print("=" * 70)

    raw_files = sorted(RAW_DIR.glob("*.txt"))
    for raw_file in raw_files:
        file_year = int(raw_file.stem)
        entries, formats = process_file(raw_file, file_year)
        all_entries.extend(entries)

        fmt_groups = defaultdict(list)
        for fmt_name, example in formats:
            fmt_groups[fmt_name].append(example)

        print(f"\n{raw_file.name}  ({len(entries)} entries)")
        for fmt_name in sorted(fmt_groups):
            examples = fmt_groups[fmt_name]
            shown = examples[:3]
            extra = f"  (+{len(examples) - 3} more)" if len(examples) > 3 else ""
            print(f"  {fmt_name:16s}  e.g. {', '.join(shown)}{extra}")

    # Check for duplicate dates
    date_entries = defaultdict(list)
    for d, text in all_entries:
        date_entries[d].append(text)

    duplicates = {d: texts for d, texts in date_entries.items() if len(texts) > 1}

    # ── Step 2: Write daily files ──
    print("\n" + "=" * 70)
    print("STEP 2: Writing daily files")
    print("=" * 70)

    written_count = 0
    written_files = set()
    for entry_date, text in all_entries:
        dir_path = OUTPUT_DIR / f"{entry_date.year:04d}" / f"{entry_date.month:02d}"
        dir_path.mkdir(parents=True, exist_ok=True)

        fname = f"{entry_date.year:04d}{entry_date.month:02d}{entry_date.day:02d}.txt"
        file_path = dir_path / fname

        if file_path in written_files:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("\n\n" + text)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            written_files.add(file_path)

        written_count += 1

    print(f"\n  Wrote {len(written_files)} unique daily files ({written_count} total entries)")

    # ── Step 3: Duplicate dates ──
    print("\n" + "=" * 70)
    print("STEP 3: Duplicate dates")
    print("=" * 70)

    print(f"\n  Duplicates : {len(duplicates)}")

    if duplicates:
        print(f"\n  Duplicate dates by month:")
        current_ym = None
        for d in sorted(duplicates):
            ym = (d.year, d.month)
            if ym != current_ym:
                print(f"\n    {d.strftime('%B %Y')}:")
                current_ym = ym
            weekday = d.strftime("%A")
            print(f"      {d.strftime('%Y-%m-%d')}  ({weekday}) — {len(duplicates[d])} entries")

    # ── Step 4: Missing / gap dates ──
    print("\n" + "=" * 70)
    print("STEP 4: Missing / gap dates")
    print("=" * 70)

    start = date(2023, 10, 1)
    end = date.today()

    expected = set()
    d = start
    while d <= end:
        expected.add(d)
        d += timedelta(days=1)

    present = set(date_entries.keys()) & expected
    missing = sorted(expected - present)

    print(f"\n  Date range : {start} → {end}")
    total_days = (end - start).days + 1
    print(f"  Total days : {total_days}")
    print(f"  Present    : {len(present)}")
    print(f"  Missing    : {len(missing)}")

    if missing:
        print(f"\n  Missing dates by month:")
        current_ym = None
        for d in missing:
            ym = (d.year, d.month)
            if ym != current_ym:
                print(f"\n    {d.strftime('%B %Y')}:")
                current_ym = ym
            weekday = d.strftime("%A")
            print(f"      {d.strftime('%Y-%m-%d')}  ({weekday})")


if __name__ == "__main__":
    main()
