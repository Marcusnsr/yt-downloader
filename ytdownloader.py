"""YT Downloader - a small desktop app for saving YouTube videos as MP3 or MP4."""

import os
import shutil
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

# Apps launched from Finder get a minimal PATH, so add the usual install
# locations for ffmpeg and deno (used by yt-dlp for YouTube's JS challenges).
for extra in ("/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".deno/bin")):
    if extra not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + extra

import yt_dlp  # noqa: E402

APP_NAME = "YT Downloader"
DEFAULT_DIR = Path.home() / "Downloads"


def find_ffmpeg():
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.resizable(False, False)
        self.ffmpeg = find_ffmpeg()
        self.out_dir = tk.StringVar(value=str(DEFAULT_DIR))
        self.fmt = tk.StringVar(value="mp4")
        self.status = tk.StringVar(value="Paste a YouTube link and press Download.")
        self.busy = False
        self._build()

    def _build(self):
        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self, padding=12)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text="YouTube link").grid(row=0, column=0, sticky="w", **pad)
        self.url_entry = ttk.Entry(frm, width=52)
        self.url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", **pad)
        self.url_entry.focus_set()
        self.url_entry.bind("<Return>", lambda _e: self.start())

        fmt_row = ttk.Frame(frm)
        fmt_row.grid(row=2, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(fmt_row, text="Format:").pack(side="left")
        ttk.Radiobutton(fmt_row, text="MP4 (video)", value="mp4", variable=self.fmt).pack(side="left", padx=8)
        ttk.Radiobutton(fmt_row, text="MP3 (audio)", value="mp3", variable=self.fmt).pack(side="left")

        ttk.Label(frm, text="Save to").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.out_dir, width=40).grid(row=4, column=0, columnspan=2, sticky="ew", **pad)
        ttk.Button(frm, text="Browse…", command=self.choose_dir).grid(row=4, column=2, sticky="e", **pad)

        self.progress = ttk.Progressbar(frm, mode="determinate", maximum=100, length=420)
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", **pad)

        ttk.Label(frm, textvariable=self.status, wraplength=420).grid(row=6, column=0, columnspan=3, sticky="w", **pad)

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=7, column=0, columnspan=3, sticky="e", **pad)
        ttk.Button(btn_row, text="Open folder", command=self.open_folder).pack(side="left", padx=6)
        self.dl_btn = ttk.Button(btn_row, text="Download", command=self.start)
        self.dl_btn.pack(side="left")

    def choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_dir.get())
        if d:
            self.out_dir.set(d)

    def open_folder(self):
        folder = self.out_dir.get()
        if sys.platform == "darwin":
            os.system(f'open "{folder}"')
        elif sys.platform == "win32":
            os.startfile(folder)  # type: ignore[attr-defined]
        else:
            os.system(f'xdg-open "{folder}"')

    def set_status(self, text, pct=None):
        def apply():
            self.status.set(text)
            if pct is not None:
                self.progress["value"] = pct

        self.after(0, apply)

    def start(self):
        if self.busy:
            return
        url = self.url_entry.get().strip()
        if not url:
            self.set_status("Please paste a YouTube link first.")
            return
        if not self.ffmpeg:
            self.set_status("ffmpeg was not found. Install it with: brew install ffmpeg")
            return
        out = Path(self.out_dir.get()).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        self.busy = True
        self.dl_btn.state(["disabled"])
        self.progress["value"] = 0
        self.set_status("Starting…")
        threading.Thread(target=self.download, args=(url, out, self.fmt.get()), daemon=True).start()

    def _hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes", 0)
            pct = done / total * 100 if total else 0
            name = Path(d.get("filename", "")).stem
            self.set_status(f"Downloading {name[:50]}… {pct:.0f}%", pct)
        elif d["status"] == "finished":
            self.set_status("Processing…", 100)

    def download(self, url, out, fmt):
        opts = {
            "outtmpl": str(out / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "progress_hooks": [self._hook],
            "ffmpeg_location": self.ffmpeg,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }
        if fmt == "mp3":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]
        else:
            opts["format"] = "bv*[vcodec^=avc1]+ba[ext=m4a]/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"
            opts["merge_output_format"] = "mp4"
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            self.set_status(f"Done! Saved \"{info.get('title', 'file')}\" as {fmt.upper()}.", 100)
        except Exception as e:  # noqa: BLE001
            msg = str(e).replace("ERROR: ", "")
            self.set_status(f"Failed: {msg[:200]}", 0)
        finally:
            self.after(0, self._done)

    def _done(self):
        self.busy = False
        self.dl_btn.state(["!disabled"])


def cli(url, out, fmt):
    """Headless mode: `YT Downloader --cli URL FOLDER mp3|mp4`."""

    class Headless:
        ffmpeg = find_ffmpeg()
        _hook = App._hook

        def set_status(self, text, pct=None):
            if not text.startswith("Downloading"):
                print(text, flush=True)

        def after(self, _ms, fn):
            fn()

        def _done(self):
            pass

    App.download(Headless(), url, Path(out).expanduser(), fmt)


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--cli":
        cli(*sys.argv[2:])
    else:
        App().mainloop()
