import zipfile
import os
from pathlib import Path
from PIL import Image
import shutil

# Paths (adjust if needed)
ZIP_PATH = Path(r"d:/HNU/Deep Learning/files/data_archive.zip")
EXTRACT_DIR = Path(r".")  # extract in current directory
TARGET_DIR = Path(r"d:/HNU/Deep Learning/extracted_images")

# Ensure target directory exists
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# Step 1: Extract zip content
with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
    zip_ref.extractall(EXTRACT_DIR)
    print(f"Extracted {ZIP_PATH} to {EXTRACT_DIR}")

# Step 2: Walk through extracted files and process images
SUPPORTED_INPUT_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}

for root, dirs, files in os.walk(EXTRACT_DIR):
    for file in files:
        src_path = Path(root) / file
        if src_path.suffix.lower() in SUPPORTED_INPUT_EXTS:
            # Open image
            try:
                with Image.open(src_path) as img:
                    # Convert to RGB (handles PNG with alpha)
                    rgb_img = img.convert('RGB')
                    # Determine output filename (same base name, .png)
                    out_name = src_path.stem + ".png"
                    out_path = TARGET_DIR / out_name
                    rgb_img.save(out_path, format='PNG')
                    print(f"Converted {src_path} -> {out_path}")
            except Exception as e:
                print(f"Failed to process {src_path}: {e}")
        else:
            # Skip non‑image files
            continue

print("All done. Images saved to", TARGET_DIR)
