from __future__ import annotations

import io
import shutil
from pathlib import Path

import cairosvg
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = PROJECT_ROOT / "data" / "image"
OUTPUT_PATH = PROJECT_ROOT / "data" / "favicons"

FAVICON_SVG = IMAGE_DIR / "favicon.svg"
FAVICON_PNG = IMAGE_DIR / "favicon.png"
OG_IMAGE_PNG = IMAGE_DIR / "og-image.png"

FAVICON_SIZES = [16, 32, 48, 192, 512]
APPLE_SIZES = [120, 152, 180]
ICO_SIZES = [16, 32, 48]
OG_IMAGE_SIZE = (1200, 630)


def ensure_output_path() -> None:
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


def load_base_icon() -> Image.Image:
    if FAVICON_SVG.exists():
        png_bytes = cairosvg.svg2png(url=str(FAVICON_SVG))
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    if FAVICON_PNG.exists():
        return Image.open(FAVICON_PNG).convert("RGBA")
    raise FileNotFoundError(
        "No se encontró un archivo base para el favicon. "
        "Asegúrate de tener 'favicon.svg' o 'favicon.png' en la carpeta."
    )


def generate_png_variants(base_icon: Image.Image, sizes: list[int], name_pattern: str) -> None:
    for size in sizes:
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
        target = OUTPUT_PATH / name_pattern.format(size=size)
        resized.save(target, format="PNG")


def generate_favicon_pngs(base_icon: Image.Image) -> None:
    generate_png_variants(base_icon, FAVICON_SIZES, "favicon-{size}x{size}.png")


def generate_apple_icons(base_icon: Image.Image) -> None:
    generate_png_variants(base_icon, APPLE_SIZES, "apple-favicon-{size}.png")


def generate_favicon_ico(base_icon: Image.Image) -> None:
    target = OUTPUT_PATH / "favicon.ico"
    base_icon.save(target, format="ICO", sizes=[(size, size) for size in ICO_SIZES])


def copy_svg() -> None:
    if FAVICON_SVG.exists():
        shutil.copy2(FAVICON_SVG, OUTPUT_PATH / "favicon.svg")


def generate_og_image() -> None:
    if not OG_IMAGE_PNG.exists():
        raise FileNotFoundError(
            "No se encontró 'og-image.png'. Asegúrate de colocarlo en la carpeta."
        )
    og_img = Image.open(OG_IMAGE_PNG)
    if og_img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", og_img.size, (255, 255, 255))
        background.paste(og_img, mask=og_img.split()[-1])
        og_img = background
    else:
        og_img = og_img.convert("RGB")
    if og_img.size != OG_IMAGE_SIZE:
        og_img = og_img.resize(OG_IMAGE_SIZE, Image.Resampling.LANCZOS)
    og_img.save(OUTPUT_PATH / "og-image.jpg", format="JPEG", quality=90, optimize=True)


def main() -> None:
    ensure_output_path()
    copy_svg()
    base_icon = load_base_icon()
    generate_favicon_pngs(base_icon)
    generate_apple_icons(base_icon)
    generate_favicon_ico(base_icon)
    generate_og_image()
    print(f"Imágenes generadas en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()