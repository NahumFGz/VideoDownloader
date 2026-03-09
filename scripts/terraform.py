import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIR = PROJECT_ROOT / "data"

FOLDERS = ("favicons", "image", "original", "processed")


def main() -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    for name in FOLDERS:
        folder = DIR / name
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)


if __name__ == "__main__":
    main()