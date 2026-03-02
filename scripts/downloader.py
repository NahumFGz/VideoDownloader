from pathlib import Path

import yt_dlp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "original"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

url = "https://www.youtube.com/watch?v=hzR3qPMTQzQ"

ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': str(OUTPUT_DIR / '%(id)s.%(ext)s'),  # <- usa el ID como nombre
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])