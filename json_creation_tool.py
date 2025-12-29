#!/usr/bin/env python3
"""
json_creation_tool.py

Interactive, future-proof CSV → JSON generator for Nommsters.

- Column order does not matter
- Extra columns are ignored safely
- Image filenames are generated from NAME (spaces + & kept)
- Guild folders are lowercase (cards/axalon, cards/ziotech, etc.)
- Builds a normalized searchText field with emoji expansions
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ---------- CONFIG ----------

RARITY_LABEL = {
    1: "Rare",
    2: "Uncommon",
    3: "Common",
}

EMOJI_MAP = {
    "🏹": ["ranged"],
    "🛡️": ["durable", "durability", "armor", "defense", "defensive"],
    "🌫️": ["swift"],
    "🔥": ["aggression", "aggressive"],
    "🌸": ["gentle"],
    "🍬": ["treat", "candy", "treats"],
    "🧊": ["sugarcoated"],
    "💥": ["damage", "damaged"],
}

IMAGES_ROOT = "cards"

REQUIRED_COLUMNS = [
    "GUILD",
    "RARITY",
    "TYPE",
    "NAME",
    "TEXTBOX",
    "TRAITS",
    "COMBAT",
]

# ----------------------------


def say(msg: str):
    print(f"\n{msg}")

def clean_path_input(s: str) -> Path:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    return Path(s)

def ask(msg: str) -> str:
    return input(f"\n{msg}\n> ").strip()


def confirm(msg: str) -> bool:
    return ask(msg + " (y/n)").lower() == "y"


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
    try:
        return int(s)
    except ValueError:
        return None


def split_traits(s: str) -> List[str]:
    s = safe_str(s)
    if not s:
        return []
    return [t.strip() for t in s.split(" - ") if t.strip()]


def filename_base_from_name(name: str) -> str:
    """
    Mason filename convention:
    - lowercase
    - keep spaces
    - keep '&'
    - keep '-' (and normalize any long dashes to '-')
    - remove apostrophes and other punctuation
    - collapse whitespace
    - remove spaces around hyphens (so "Red - Handed" -> "red-handed")
    """
    s = safe_str(name).lower()

    # Normalize long dashes to a normal hyphen
    s = s.replace("–", "-").replace("—", "-")

    # Remove apostrophes entirely (Day's -> days)
    s = s.replace("'", "").replace("’", "")

    # Replace everything except letters/numbers/spaces/&/- with a space
    s = re.sub(r"[^a-z0-9 &\-]+", " ", s)

    # Normalize spacing around '&' (optional but keeps it tidy)
    s = re.sub(r"\s*&\s*", " & ", s)

    # Normalize spacing around hyphens: "red - handed" -> "red-handed"
    s = re.sub(r"\s*-\s*", "-", s)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s




def expand_emojis(text: str) -> str:
    extras = []
    for emoji, words in EMOJI_MAP.items():
        if emoji in text:
            extras.extend(words)
    return text + (" " + " ".join(extras) if extras else "")


def normalize_for_search(text: str) -> str:
    t = text.lower()
    emoji_chars = "".join(map(re.escape, EMOJI_MAP.keys()))
    t = re.sub(rf"[^\w\s&{emoji_chars}]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def build_search_text(card: Dict[str, Any]) -> str:
    parts = [
        card["name"],
        card["guild"],
        card["type"],
        card.get("rarityLabel", ""),
        f"rarity{card['rarity']}" if card["rarity"] is not None else "",
        " ".join(card["traits"]),
        card["text"],
        card.get("combatRaw") or "",
    ]

    expanded = " ".join(expand_emojis(p) for p in parts if p)
    return normalize_for_search(expanded)


# ---------- MAIN ----------

def main():
    say("Hey Mason. This tool generates a JSON file for your card gallery.")

    csv_path = clean_path_input(ask("Paste the path to your CSV file"))
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    version = ask("What version label should go in the JSON? (e.g. v15, v16)")
    out_path = Path(ask("Where should the JSON be saved? (full path, including filename)"))

    say("Reading spreadsheet…")
    df = pd.read_csv(csv_path).fillna("")

    header_map = {normalize_header(h): h for h in df.columns}

    for col in REQUIRED_COLUMNS:
        if normalize_header(col) not in header_map:
            raise KeyError(f"Missing required column: {col}")

    cards = []
    seen_paths = {}

    for _, row in df.iterrows():
        name = safe_str(row[header_map["NAME"]])
        if not name:
            continue

        guild = safe_str(row[header_map["GUILD"]])
        guild_folder = guild.lower()

        file_base = filename_base_from_name(name)
        image_path = f"{IMAGES_ROOT}/{guild_folder}/{file_base}_large.jpg"
        thumb_path = f"{IMAGES_ROOT}/{guild_folder}/{file_base}_thumb.jpg"


        if image_path in seen_paths:
            raise ValueError(
                f"Filename collision:\n{image_path}\n"
                f"'{seen_paths[image_path]}' and '{name}'"
            )
        seen_paths[image_path] = name

        rarity = to_int_or_none(row[header_map["RARITY"]])

        card = {
            "id": file_base,
            "name": name,
            "guild": guild,
            "type": safe_str(row[header_map["TYPE"]]),
            "rarity": rarity,
            "rarityLabel": RARITY_LABEL.get(rarity),
            "power": to_int_or_none(row.get(header_map.get("POWER"))),
            "combatRaw": safe_str(row[header_map["COMBAT"]]) or None,
            "traits": split_traits(row[header_map["TRAITS"]]),
            "text": safe_str(row[header_map["TEXTBOX"]]),
            "flags": {
                "trueDamage": safe_str(
                    row.get(header_map.get("DEALS TRUE DAMAGE"))
                ).lower() == "true"
            },
            "image": image_path,
            "thumb": thumb_path,
        }

        card["searchText"] = build_search_text(card)
        cards.append(card)

    say(f"I found {len(cards)} cards.")
    say(f"Images are expected under: {IMAGES_ROOT}/<guild>/")
    say(f"JSON will be written to:\n{out_path}")

    if not confirm("Does this all look correct?"):
        say("Okay, nothing written. Exiting.")
        return

    out = {"version": version, "cards": cards}
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    say("Done. JSON generated successfully.")


if __name__ == "__main__":
    main()
