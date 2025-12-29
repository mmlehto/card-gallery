import json
from pathlib import Path

INPUT_JSON = Path("cards_v15.json")
OUTPUT_JSON = Path("cards_v15_fixed.json")

data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))

fixed = 0

for card in data.get("cards", []):
    image = card.get("image", "")
    if image.endswith(".jpg") and not image.endswith("_large.jpg"):
        card["image"] = image.replace(".jpg", "_large.jpg")
        fixed += 1

OUTPUT_JSON.write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"Updated {fixed} image paths.")
print(f"Wrote {OUTPUT_JSON}")
