# build_cards_v13_json_from_files_code_first.py
from pathlib import Path
import json
import re

# -------- EDIT THESE --------
CARDS_ROOT = Path(r"Z:\GAME DESIGN\NOMMSTERS\card-gallery\cards")
OUTPUT_JSON = Path(r"Z:\GAME DESIGN\NOMMSTERS\card-gallery\cards_v13.json")
FORCE_VERSION = 13
# ---------------------------

# code-first: <guild><rarity><type><vv>_<slug>.jpg
# examples:
#   a1a12_academic-enrollment.jpg
#   c1c12_backup-vocalist.jpg
FILENAME_RE = re.compile(
    r"^(?P<g>[abcfsv])(?P<rar>[123])(?P<t>[acs])(?P<ver>\d{2})_(?P<slug>.+)\.jpg$",
    re.IGNORECASE
)

GUILD_FOLDER_TO_PROPER = {
    "axalon": "Axalon",
    "burlindor": "Burlindor",
    "coronis": "Coronis",
    "flaria": "Flaria",
    "sylvani": "Sylvani",
    "veralyn": "Veralyn",
}

RARITY_MAP = {"1": "Rare", "2": "Uncommon", "3": "Common"}
TYPE_MAP   = {"a": "Action", "c": "Character", "s": "Asset"}

def title_from_slug(slug: str) -> str:
    parts = re.split(r"[-_]+", slug.strip())
    parts = [p for p in parts if p]
    return " ".join(w[:1].upper() + w[1:] if w else "" for w in parts)

def main():
    if not CARDS_ROOT.exists():
        raise FileNotFoundError(f"Cards root not found: {CARDS_ROOT}")

    cards = []
    unmatched = []
    guild_mismatch = []

    for guild_dir in sorted([p for p in CARDS_ROOT.iterdir() if p.is_dir()]):
        folder = guild_dir.name.lower()

        if folder == "nommsters":
            continue
        if folder not in GUILD_FOLDER_TO_PROPER:
            continue

        guild_proper = GUILD_FOLDER_TO_PROPER[folder]
        folder_letter = folder[0]  # a/b/c/f/s/v

        for img_path in sorted(guild_dir.glob("*.jpg")):
            fname = img_path.name

            if fname.lower().endswith("_thumb.jpg"):
                continue

            m = FILENAME_RE.match(fname)
            if not m:
                unmatched.append(f"cards/{folder}/{fname}")
                continue

            g_letter = m.group("g").lower()
            rar_digit = m.group("rar")
            t_letter = m.group("t").lower()
            slug = m.group("slug")

            if g_letter != folder_letter:
                guild_mismatch.append(f"cards/{folder}/{fname} (code guild='{g_letter}', folder='{folder}')")

            rarity = RARITY_MAP.get(rar_digit, "Unknown")
            ctype = TYPE_MAP.get(t_letter, "Unknown")

            image_rel = f"cards/{folder}/{fname}"
            thumb_rel = image_rel.replace(".jpg", "_thumb.jpg")

            cards.append({
                "name": title_from_slug(slug),
                "guild": guild_proper,
                "rarity": rarity,
                "type": ctype,
                "version": FORCE_VERSION,   # ignore the "12" in the filename
                "image": image_rel,
                "thumbnail": thumb_rel,
            })

    cards.sort(key=lambda c: (c["guild"], c["name"], c["image"]))
    for i, c in enumerate(cards, start=1):
        c["id"] = i

    OUTPUT_JSON.write_text(json.dumps(cards, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(cards)} cards -> {OUTPUT_JSON}")

    if unmatched:
        print("\n[UNMATCHED FILENAMES] (expected: <g><rar><type><vv>_<slug>.jpg)")
        for x in unmatched[:80]:
            print("  -", x)
        if len(unmatched) > 80:
            print(f"  ...and {len(unmatched)-80} more")

    if guild_mismatch:
        print("\n[GUILD LETTER MISMATCH] (code letter doesn't match folder)")
        for x in guild_mismatch[:80]:
            print("  -", x)
        if len(guild_mismatch) > 80:
            print(f"  ...and {len(guild_mismatch)-80} more")

if __name__ == "__main__":
    main()
