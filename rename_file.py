from pathlib import Path
import re

def rename_datasets_images(DATASET_DIR=False):
    pattern = re.compile(r"^img(\d{4})\.jpg$", re.IGNORECASE)

    for person_dir in sorted(DATASET_DIR.iterdir()):

        if not person_dir.is_dir():
            continue

        print(f"\nProcessing: {person_dir.name}")

        # Find highest existing index in current folder
        max_index = 0

        for file in person_dir.iterdir():
            if file.is_file():
                match = pattern.match(file.name)
                if match:
                    max_index = max(max_index, int(match.group(1)))

        # Find JPG files that are not already renamed
        jpg_files = sorted([
            f for f in person_dir.iterdir()
            if (
                f.is_file()
                and f.suffix.lower() == ".jpg"
                and not pattern.match(f.name)
            )
        ])

        print(f"Highest existing index: {max_index}")
        print(f"Files to rename: {len(jpg_files)}")

        # Rename files
        for file in jpg_files:
            max_index += 1

            new_name = person_dir / f"img{max_index:04d}.jpg"

            file.rename(new_name)

            print(f"  {file.name} -> {new_name.name}")

    print("\nCompleted.")


# Rename files
DATASET_DIR = Path("datasets/raw_data")
rename_datasets_images(DATASET_DIR=DATASET_DIR)