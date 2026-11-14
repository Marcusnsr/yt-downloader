#!/bin/sh
# Builds "dist/YT Downloader.app"
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --windowed --name "YT Downloader" \
  --icon assets/icon.icns --osx-bundle-identifier com.marcusnsr.ytdownloader \
  --collect-all yt_dlp_ejs --collect-submodules yt_dlp ytdownloader.py
echo "Built: dist/YT Downloader.app"
