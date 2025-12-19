import os
import json
import re

# ================== CONFIG ==================

BASE_DIR = r"Z:\GAME DESIGN\NOMMSTERS\card-gallery\cards"
OUTPUT_JSON = r"Z:\GAME DESIGN\NOMMSTERS\card-gallery\cards_v13.json"

GUILD_MAP = {
    "a": "Axalon",
    "b": "Burlindor",
    "c": "Coronis",
    "f": "Flaria",
    "s": "Sylvani",
    "v": "Veralyn"
}

RARITY_MAP = {
    "a": "Common",
    "u": "Uncommon",
    "c": "Rare",
    "r": "Rare"
}

FILENAME_PATTERN = re.compile(
    r"^([a-z])(\d+)([a-z])(\d+)_([a-z0-9\-]+)\.jpg$",
    re.IGNORECASE
)

# ================== SCRIPT ==================

cards = []
skipped = []

for guild_folder in os.listdir(BASE_DIR):
    folder_path = os.path.join(BASE_DIR, guild_folder)

    if not os.path.isdir(folder_path):
        continue

    for filename in os.listdir(folder_path):
        print("\n---")
        print("RAW FILENAME:", repr(filename))

        lower = filename.lower()

        if not lower.endswith(".jpg"):
            print("❌ Not a JPG")
            continue

        if lower.endswith("_thumb.jpg"):
            print("⏭️ Thumb file, skipping")
            continue

        print("✔ JPG, non-thumb")

        match = FILENAME_PATTERN.match(filename)

        if not match:
            print("❌ REGEX DID NOT MATCH")
            print("   Pattern:", FILENAME_PATTERN.pattern)
            print("   Filename chars:", [c for c in filename])
            continue

        print("✅ REGEX MATCHED")

        guild_letter, set_num, rarity_letter, version, slug = match.groups()

        print("   Parsed:")
        print("     guild_letter:", guild_letter)
        print("     set_num:", set_num)
        print("     rarity_letter:", rarity_letter)
        print("     version:", version)
        print("     slug:", slug)

        guild = GUILD_MAP.get(guild_letter.lower())
        if not guild:
            print("❌ Unknown guild letter:", guild_letter)
            continue

        print("✔ Guild resolved:", guild)

        rarity = RARITY_MAP.get(rarity_letter.lower(), "Unknown")
        print("✔ Rarity resolved:", rarity)

        card = {
            "id": slug,
            "name": slug.replace("-", " ").title(),
            "guild": guild,
            "rarity": rarity,
            "set": int(set_num),
            "version": int(version),
            "image": f"cards/{guild.lower()}/{filename}",
            "thumbnail": f"cards/{guild.lower()}/{filename.replace('.jpg', '_thumb.jpg')}"
        }

        print("✅ Card object created")
        cards.append(card)


# Stable sort for clean diffs
cards.sort(key=lambda c: (c["guild"], c["name"]))

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(cards, f, indent=2)

print(f"✅ Generated {len(cards)} cards")

if skipped:
    print("⚠️ Skipped files:")
    for f in skipped:
        print("  -", f)
