from pathlib import Path

TARGET_DIR = Path(r"Z:\GAME DESIGN\NOMMSTERS\card-gallery\cards\nommsters")

def capitalize_first_letter(filename: str) -> str:
    if not filename:
        return filename
    return filename[0].upper() + filename[1:]


def main():
    if not TARGET_DIR.exists():
        raise FileNotFoundError(TARGET_DIR)

    for path in TARGET_DIR.iterdir():
        if not path.is_file():
            continue

        old_name = path.name
        new_name = capitalize_first_letter(old_name)

        if old_name == new_name:
            continue  # already correct

        temp_path = path.with_name(f"__tmp__{old_name}")

        # Two-step rename is REQUIRED on Windows to force case change
        path.rename(temp_path)
        temp_path.rename(path.with_name(new_name))

        print(f"{old_name}  ->  {new_name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
