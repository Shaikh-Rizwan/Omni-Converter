# ⚡ OmniConvert - Modern Desktop Video Converter

A high-performance, modern desktop video and audio converter powered by **FFmpeg** and built with **Python & CustomTkinter**. It offers hardware-accelerated transcoding (NVIDIA NVENC, AMD AMF, Intel QSV), lossless stream remuxing, batch processing, audio extraction, and animated GIF creation.

---

## 🚀 Quick Start

Simply double-click the included batch launcher:
```bat
run_converter.bat
```
Or run directly with Python:
```bash
python main.py
```

---

## 🎯 Supported Formats & Codecs

### 🎬 Video Formats (Containers)
* **MP4 (`.mp4`, `.m4v`)** — The universal standard. Plays on smartphones, web browsers, smart TVs, Apple/Android devices.
* **MKV (`.mkv`)** — Matroska container for power users, multiple audio tracks, multi-language subtitles, and archiving.
* **WebM (`.webm`)** — Modern web-optimized video format using VP9 or next-generation AV1.
* **MOV (`.mov`)** — Apple QuickTime standard format, ideal for macOS, iOS, and ProRes editing.
* **AVI (`.avi`)** — Classic Windows format for legacy hardware, car stereos, and older media players.
* **WMV (`.wmv`)** — Windows Media Video format.
* **TS (`.ts`)** — MPEG Transport Stream for broadcast, IPTV, and camcorder streams.
* **GIF (`.gif`)** — Color palette-optimized high-quality animated GIFs.

### ⚙️ Video Codecs
* **H.264 / AVC** — Maximum universal compatibility.
* **H.265 / HEVC** — ~50% smaller file size than H.264 at identical quality (Standard for 4K / HDR).
* **AV1** — Next-gen royalty-free compression format (RTX 40-series / Intel Arc / modern CPU).
* **VP9 / VP8** — Google open web video standard.
* **Apple ProRes** — Visually lossless master format for video editing.
* **MPEG-4 / Xvid** — Legacy codecs for older DVD/car players.
* **Stream Copy (Lossless)** — Instant container remuxing without re-encoding (takes 1–2 seconds).

### 🎵 Audio Extraction Formats
* **MP3 (`.mp3`)** — Universal audio format.
* **WAV (`.wav`)** — Uncompressed 16-bit / 24-bit lossless PCM master audio.
* **AAC (`.m4a`)** — High-efficiency audio.
* **FLAC (`.flac`)** — Free Lossless Audio Codec.
* **OPUS (`.opus`)** — State-of-the-art interactive audio codec.
* **OGG (`.ogg`)** — Open-source Ogg Vorbis.

---

## ✨ Features

- **Drag & Drop Interface**: Drag media files or entire folders right into the app window.
- **Hardware Acceleration (GPU)**: Automatically detects and utilizes NVIDIA NVENC, AMD AMF, or Intel QSV for ultra-fast GPU encoding.
- **Batch Processing**: Convert dozens of files simultaneously with real-time speed, ETA, and progress metrics.
- **Resolution Scaling**: Downscale or upscale to 4K UHD, 2K QHD, 1080p FHD, 720p HD, 480p SD, or keep original dimensions.
- **Framerate Control**: Keep source framerate or convert to 60 FPS, 30 FPS, 25 FPS, or 24 FPS (cinematic).
- **Quality / CRF Tuning**: Balanced, High Quality (near lossless), or Compact presets.
- **Lossless Stream Copy**: Instant remuxing without re-encoding when codecs are compatible.
- **Auto-open Output**: Automatically opens the destination directory when conversions finish.
- **Fluent Modern UI**: Clean Windows 11 Fluent dark/light theme.

---

## 📁 Project Structure

```
d:\File converter/
├── main.py                     # Application entry point
├── run_converter.bat           # 1-click Windows launcher
├── requirements.txt            # Python dependencies
├── sample_test.mp4             # Sample test video
├── core/
│   ├── ffmpeg_finder.py        # Discovers FFmpeg and probes GPU encoders
│   ├── media_probe.py          # Extracts video/audio metadata via ffprobe
│   ├── presets.py              # Format, codec, resolution, and quality presets
│   └── converter_engine.py     # Worker engine with progress & cancellation
└── gui/
    ├── main_window.py          # Main application window & thread event queue
    └── components/
        ├── drop_target.py      # Drag-and-drop file upload zone
        ├── queue_item.py       # Queue card with progress bar & status badge
        └── settings_view.py    # Conversion settings & format selection panel
```

