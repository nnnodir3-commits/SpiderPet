"""Verify that all v38 animated assets are present before packaging."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent
for stem, count in (("walk", 32), ("threat", 12)):
    for index in range(count):
        path = root / f"{stem}_{index:02d}.png"
        if not path.is_file():
            raise SystemExit(f"MISSING: {path.name}")
        with Image.open(path) as image:
            image.verify()
print("OK: 32 walk sprites + 12 threat sprites")
