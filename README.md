# YT Downloader

A small macOS desktop app for downloading YouTube videos as **MP3** (audio) or **MP4** (video).

Paste a link, pick a format, and click **Download**. Files go to `~/Downloads` by default; use **Browse…** to change that.

## Requirements

- macOS
- [ffmpeg](https://ffmpeg.org/) for merging video/audio and converting to MP3
- [deno](https://deno.com/), which yt-dlp uses to solve YouTube's JavaScript challenges

```sh
brew install ffmpeg deno
```

## Install

Download `YT-Downloader-macOS.zip` from [Releases](../../releases), unzip it, and drag **YT Downloader.app** into `Applications`.

The app isn't signed, so the first time you open it, right-click it and choose **Open**.

## Build from source

```sh
./build.sh
```

This creates `dist/YT Downloader.app`.

To run it without building:

```sh
pip install -r requirements.txt
python3 ytdownloader.py
```

## Notes

- MP4 downloads prefer H.264 so they play in QuickTime and most players.
- MP3s are 192 kbps.
- Download only content you have the rights to.

## License

MIT
