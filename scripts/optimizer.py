from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "data" / "original"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Extensiones típicas de video
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

# --- Calidad vs peso (para web en /public) ---
# CRF: 18 = casi sin pérdida, 23 = muy buena calidad, 27–28 = más compresión, aceptable para web.
CRF = 27
# Preset: slow = buen balance; veryslow = más compresión y menor peso pero tarda bastante más.
PRESET = "slow"

# Resolución máxima (alto). 540p reduce más el peso; sube a 640/720 si quieres más nitidez.
# None = no reescalar, solo re-codificar.
MAX_HEIGHT = 540

# Audio: 64k suficiente para voz; 96k/128k si quieres más calidad.
AUDIO_BITRATE = "64k"

# FPS de salida. Menos fps = menos peso. 24 es fluido y ahorra bastante; 30 estándar web. None = mantener original.
TARGET_FPS = 24

# Miniatura: frame del medio. Dimensiones estándar tipo YouTube (1280×720, 16:9).
THUMBNAIL_EXT = ".webp"
THUMBNAIL_QUALITY = 85
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def format_size(size_bytes: int) -> str:
    """Formatea bytes a KB/MB/GB legible."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_duration_seconds(src: Path) -> float | None:
    """Obtiene la duración del video en segundos con ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(src),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def extract_thumbnail(src: Path, dst: Path) -> bool:
    """Extrae un frame del medio del video como miniatura en formato ligero (WebP)."""
    duration = get_duration_seconds(src)
    if duration is None or duration <= 0:
        seek_sec = 0
    else:
        seek_sec = duration / 2.0

    # -ss antes de -i = seek rápido; -vframes 1 = un solo frame.
    # Escala para cubrir 1280×720 y recorta al centro (vertical u horizontal → siempre 16:9).
    scale_crop = (
        f"scale={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(seek_sec),
        "-i",
        str(src),
        "-vframes",
        "1",
        "-vf",
        scale_crop,
        "-c:v",
        "libwebp",
        "-quality",
        str(THUMBNAIL_QUALITY),
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  ⚠ Miniatura no generada: {e}")
        return False


def build_ffmpeg_cmd(src: Path, dst: Path) -> list[str]:
    # Dimensiones siempre múltiplo de 2 (requisito H.264). Si limitamos alto, -2 ajusta ancho.
    if MAX_HEIGHT is None:
        scale_filter = "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    else:
        # La coma en min() debe ir escapada (\,) para que ffmpeg no la tome como separador de filtros.
        scale_filter = (
            f"scale=trunc(min(iw\\,iw*{MAX_HEIGHT}/ih)/2)*2:trunc(min(ih\\,{MAX_HEIGHT})/2)*2"
        )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        scale_filter,
        "-c:v",
        "libx264",
        "-preset",
        PRESET,
        "-crf",
        str(CRF),
        "-tune",
        "film",  # mejor compresión para contenido real; usa "animation" si son dibujos
        "-profile:v",
        "main",
        "-level",
        "4.0",  # compatibilidad navegadores y móviles
        "-pix_fmt",
        "yuv420p",
    ]
    if TARGET_FPS is not None:
        cmd.extend(["-r", str(TARGET_FPS)])
    cmd.extend([
        "-c:a",
        "aac",
        "-b:a",
        AUDIO_BITRATE,
        "-movflags",
        "+faststart",  # metadata al inicio = mejor streaming en web
        str(dst),
    ])
    return cmd


def main() -> None:
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"No existe INPUT_DIR: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    videos = [p for p in INPUT_DIR.rglob("*") if p.suffix.lower() in VIDEO_EXTS]
    if not videos:
        print(f"No encontré videos en {INPUT_DIR}")
        return

    for src in videos:
        dst = OUTPUT_DIR / f"{src.stem}.mp4"
        thumb_path = OUTPUT_DIR / f"{src.stem}{THUMBNAIL_EXT}"

        print(f"\nProcesando:\n  IN : {src}\n  OUT: {dst}")
        size_original = src.stat().st_size
        cmd = build_ffmpeg_cmd(src, dst)

        try:
            run(cmd)
            size_nuevo = dst.stat().st_size
            if size_original > 0:
                reduccion = (1 - size_nuevo / size_original) * 100
                print(
                    f"  Peso: {format_size(size_original)} → {format_size(size_nuevo)} "
                    f"(reducción: {reduccion:.1f}%)"
                )
            if extract_thumbnail(src, thumb_path):
                print(f"  Miniatura: {thumb_path.name}")
        except subprocess.CalledProcessError as e:
            print(f"Error procesando {src.name}: {e}")

    print("\n✅ Listo. Videos y miniaturas en:", OUTPUT_DIR)


if __name__ == "__main__":
    main()