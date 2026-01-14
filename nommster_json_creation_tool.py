#!/usr/bin/env python3
"""
nommster_json_creation_tool.py

Interactive CSV → JSON generator specifically for Nommsters.

Why this exists:
- Regular cards are single-faced and use image paths like: cards/<guild>/<name>_large.jpg
- Nommsters are double-sided and use 4 image paths:
    front/back thumbs + modalFront/modalBack full images

Output shape matches your older nommsters JSON (a plain JSON array of objects).

Expected image naming convention (your *new* naming):
  cards/nommsters/<Name>_dormant.jpg
  cards/nommsters/<Name>_energized.jpg
  cards/nommsters/<Name>_dormant_thumb.jpg
  cards/nommsters/<Name>_energized_thumb.jpg

Notes:
- <Name> keeps its original capitalization (e.g. Frisklaw)
- Spaces and apostrophes are removed for filename safety
Notes:
- Column order does not matter
- Extra columns are ignored safely
- If "Total Cost" is missing, the tool will compute cost = D-COST + E-COST if available
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ---------- CONFIG ----------

IMAGES_ROOT = "cards/nommsters"

# Columns (case-insensitive); tool accepts a few common variants.
REQUIRED_ANY_OF = {
    "GUILD": ["GUILD", "FACTION"],
    "NAME": ["NAME", "NOMMSTER", "CARD NAME"],
    "TOTAL_COST": ["TOTAL COST", "COST", "TOTALCOST"],
    "D_COST": ["D-COST", "D COST", "DORMANT COST", "DORMANTCOST"],
    "E_COST": ["E-COST", "E COST", "ENERGIZED COST", "ENERGIZEDCOST"],
}

# ----------------------------


def say(msg: str) -> None:
    print(f"\n{msg}")


def ask(msg: str) -> str:
    return input(f"\n{msg}\n> ").strip()


def confirm(msg: str) -> bool:
    return ask(msg + " (y/n)").lower() == "y"


def clean_path_input(s: str) -> Path:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    return Path(s)


def normalize_header(h: str) -> str:
    return str(h).strip().upper()


def safe_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and pd.isna(x):
        return ""
    return str(x).strip()


def to_int_or_none(x: Any) -> Optional[int]:
    s = safe_str(x)
    if s in ("", "-", "—"):
        return None
    # Some sheets export numbers like "9.0"
    try:
        return int(float(s))
    except ValueError:
        return None


def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Return the *actual* column name in df matching any candidate (case-insensitive),
    or None if not found.
    """
    norm_to_actual = {normalize_header(c): c for c in df.columns}
    for cand in candidates:
        key = normalize_header(cand)
        if key in norm_to_actual:
            return norm_to_actual[key]
    return None


def file_safe_name_preserve_case(name: str) -> str:
    """
    Builds the <Name> portion used in Nommster image filenames.

    Your existing filenames in v13 JSON look like: axalon_Sniffin_dormant.jpg
    i.e. guild is lowercase, but Name keeps its original capitalization.

    Rules:
    - strip outer whitespace
    - remove apostrophes
    - normalize long dashes to '-'
    - remove spaces (if any)
    - remove any remaining characters that aren't letters/numbers/hyphen/& (conservative)
    """
    s = safe_str(name).strip()
    s = s.replace("’", "").replace("'", "")
    s = s.replace("–", "-").replace("—", "-")
    s = s.replace(" ", "")
    s = re.sub(r"[^A-Za-z0-9&\-]+", "", s)
    return s


def id_from_name(name: str) -> str:
    """
    JSON id is lowercased and alphanumeric only (matches your v13 ids like 'mugchomp').
    """
    s = safe_str(name).lower()
    s = s.replace("’", "").replace("'", "")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def build_paths(guild: str, name: str) -> Dict[str, str]:
    # 'guild' is kept in the JSON output, but NOT used in filenames in the new naming scheme.
    name_part = file_safe_name_preserve_case(name)
    base = f"{IMAGES_ROOT}/{name_part}"

    return {
        "front": f"{base}_dormant_thumb.jpg",
        "back": f"{base}_energized_thumb.jpg",
        "modalFront": f"{base}_dormant.jpg",
        "modalBack": f"{base}_energized.jpg",
    }


def resolve_cost(row: pd.Series, col_total: Optional[str], col_d: Optional[str], col_e: Optional[str]) -> int:
    """
    Prefer Total Cost if present. Otherwise fall back to D-COST + E-COST if possible.
    If still missing, default to 0 (to match your older JSON behavior).
    """
    if col_total:
        v = to_int_or_none(row.get(col_total))
        if v is not None:
            return v

    d = to_int_or_none(row.get(col_d)) if col_d else None
    e = to_int_or_none(row.get(col_e)) if col_e else None
    if d is not None and e is not None:
        return d + e

    return 0


def main() -> None:
    say("Hey Mason. This tool generates a Nommsters JSON file for your card gallery.")

    csv_path = clean_path_input(ask("Paste the path to your Nommsters CSV file"))
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    out_path = Path(ask("Where should the JSON be saved? (full path, including filename)"))

    say("Reading spreadsheet…")
    df = pd.read_csv(csv_path).fillna("")

    # Resolve columns (case-insensitive, supports variants)
    col_guild = find_column(df, REQUIRED_ANY_OF["GUILD"])
    col_name = find_column(df, REQUIRED_ANY_OF["NAME"])
    col_total = find_column(df, REQUIRED_ANY_OF["TOTAL_COST"])
    col_d = find_column(df, REQUIRED_ANY_OF["D_COST"])
    col_e = find_column(df, REQUIRED_ANY_OF["E_COST"])

    missing = []
    if not col_guild:
        missing.append("GUILD")
    if not col_name:
        missing.append("NAME")
    if missing:
        raise KeyError(f"Missing required column(s): {', '.join(missing)}")

    if not col_total and not (col_d and col_e):
        say("Warning: No 'Total Cost' column found and couldn't find both D-COST and E-COST.")
        say("Cost will default to 0 for any rows missing cost data (matches older JSON behavior).")

    nommsters: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_paths = set()

    for _, row in df.iterrows():
        name = safe_str(row.get(col_name))
        if not name:
            continue

        guild = safe_str(row.get(col_guild))
        if not guild:
            continue

        nid = id_from_name(name)
        if not nid:
            raise ValueError(f"Couldn't build a valid id from name: '{name}'")

        if nid in seen_ids:
            raise ValueError(f"Duplicate Nommster id generated: '{nid}' (from name '{name}')")
        seen_ids.add(nid)

        cost = resolve_cost(row, col_total, col_d, col_e)

        paths = build_paths(guild=guild, name=name)
        # Simple collision safety: ensure no two rows generate identical image paths
        for k, p in paths.items():
            if p in seen_paths:
                raise ValueError(f"Image path collision on '{p}' (field '{k}') — check names for duplicates.")
            seen_paths.add(p)

        nommsters.append(
            {
                "name": name,
                "id": nid,
                "guild": guild,
                "cost": cost,
                **paths,
            }
        )

    say(f"I found {len(nommsters)} Nommsters.")
    say(f"Images are expected under: {IMAGES_ROOT}/")
    say(f"JSON will be written to:\n{out_path}")

    if not confirm("Does this all look correct?"):
        say("Okay, nothing written. Exiting.")
        return

    out_path.write_text(json.dumps(nommsters, indent=2, ensure_ascii=False), encoding="utf-8")
    say("Done. Nommsters JSON generated successfully.")


if __name__ == "__main__":
    main()
