import os
import sys
import subprocess
import tempfile
import shutil

# prefer yt_dlp because pytube frequently breaks due to YouTube API
# changes.  yt-dlp is actively maintained and handles most edge cases.
try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None  # we'll raise a helpful error later

def _check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("ffmpeg not found. Install ffmpeg and ensure it's on PATH.")
        sys.exit(1)

def _on_progress(stream, chunk, bytes_remaining):
    total = stream.filesize
    downloaded = total - bytes_remaining
    pct = downloaded / total * 100
    print(f"\rDownloading: {pct:5.1f}% ", end="", flush=True)

def _find_ffmpeg_exe() -> str:
    """
    Return path to ffmpeg executable.
    Checks env vars FFMPEG_PATH or FFMPEG_BIN, then shutil.which, then `where ffmpeg`, then common locations.
    Raises RuntimeError if not found.
    """
    # 1) env var (file or folder)
    env = os.environ.get("FFMPEG_PATH") or os.environ.get("FFMPEG_BIN")
    if env:
        if os.path.isfile(env):
            return env
        maybe = os.path.join(env, "ffmpeg.exe")
        if os.path.isfile(maybe):
            return maybe

    # 2) shutil.which
    which_ff = shutil.which("ffmpeg")
    if which_ff:
        return which_ff

    # 3) Windows 'where' (can reveal WindowsApps path aliases)
    try:
        r = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, check=False)
        if r.returncode == 0 and r.stdout:
            for line in r.stdout.splitlines():
                line = line.strip()
                if os.path.isfile(line):
                    return line
    except Exception:
        pass

    # 4) common install locations
    common = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\ffmpeg.exe",
        r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\ffmpeg.exe".format(user=os.getlogin()),
    ]
    for p in common:
        if os.path.isfile(p):
            return p

    raise RuntimeError(
        "ffmpeg not found. Install ffmpeg, add it to PATH, or set FFMPEG_PATH to the full path of ffmpeg.exe."
    )

def download_mp3(youtube_url: str, output_dir: str = ".") -> str:
    """
    Download audio from a YouTube URL and convert to MP3.

    This implementation prefers ``yt_dlp`` which is more robust than
    ``pytube`` and avoids the numerous HTTP 400/404 errors caused by
    outdated client versions or API keys.  The function still uses
    ``ffmpeg`` for conversion, as before.
    """
    ffmpeg_exe = _find_ffmpeg_exe()

    if YoutubeDL is None:
        raise RuntimeError(
            "yt-dlp is required but not installed. ``pip install yt-dlp``"
        )

    # ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # make sure ffmpeg from PATH is used
        'ffmpeg_location': ffmpeg_exe,
        'quiet': False,
        'noplaylist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url)

    # yt-dlp returns the full path (with extension .mp3)
    if isinstance(info, dict) and 'title' in info:
        base = info.get('title')
        # ydl_opts outtmpl may append .mp3 automatically
        # we'll just recompute path
        return os.path.join(output_dir, base + '.mp3')
    # fallback: try to inspect ydl.last_info_dict
    return os.path.join(output_dir, os.path.basename(ydl.prepare_filename(info)).rsplit('.',1)[0] + '.mp3')

if __name__ == "__main__":
    # If URL passed as argument use it, otherwise prompt the user.
    if len(sys.argv) >= 2:
        url = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    else:
        try:
            url = input("Enter YouTube URL: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNo URL provided. Exiting.")
            sys.exit(1)
        if not url:
            print("No URL provided. Exiting.")
            sys.exit(1)
        out_dir = input("Output directory (leave empty for current folder): ").strip() or "."

    os.makedirs(out_dir, exist_ok=True)

    try:
        out = download_mp3(url, out_dir)
        print(f"Saved MP3: {out}")
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
