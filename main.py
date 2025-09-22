from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import re
import subprocess

app = FastAPI()

# safe filename
def make_safe_filename(name):
    return re.sub(r'[\\/:*?"<>|#]', '-', name)

# API: format list
@app.get("/formats")
def list_formats(url: str = Query(...)):
    ydl_opts = {"listformats": True, "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        available_formats = []

        for f in formats:
            if f.get("vcodec") != "none":  # Only video
                resolution = f.get("height", "unknown")
                ext = f.get("ext", "unknown")
                filesize = f.get("filesize") or f.get("filesize_approx") or 0
                filesize_mb = f"{filesize / 1024 / 1024:.1f} MB" if filesize else "?"
                has_audio = "yes" if f.get("acodec") != "none" else "no"

                available_formats.append({
                    "format_id": f["format_id"],
                    "resolution": f"{resolution}p",
                    "ext": ext,
                    "filesize": filesize_mb,
                    "has_audio": has_audio
                })

        return JSONResponse({
            "title": make_safe_filename(info.get("title", "video")),
            "formats": available_formats
        })

# API: download video direct
@app.get("/download")
def download_video(url: str, format_id: str = Query("best")):
    command = [
        "yt-dlp",
        "-f", f"{format_id}+bestaudio/best",
        "-o", "-",
        "--merge-output-format", "mp4",
        url
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)

    return StreamingResponse(
        process.stdout,
        media_type="video/mp4",
        headers={"Content-Disposition": "attachment; filename=video.mp4"}
    )
