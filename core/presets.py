"""Presets, format definitions, and encoder mappings."""
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class FormatDef:
    name: str
    extension: str
    category: str  # "video" or "audio"
    description: str
    default_vcodec: str
    default_acodec: str
    supported_vcodecs: List[str]
    supported_acodecs: List[str]


SUPPORTED_FORMATS: Dict[str, FormatDef] = {
    # Video Formats
    "MP4": FormatDef(
        name="MP4",
        extension=".mp4",
        category="video",
        description="Universal compatibility (Phones, Browsers, TVs, Web)",
        default_vcodec="H.264",
        default_acodec="AAC",
        supported_vcodecs=["H.264", "H.265 (HEVC)", "AV1", "Copy (Lossless)"],
        supported_acodecs=["AAC", "MP3", "AC3", "Copy (Lossless)", "No Audio"]
    ),
    "MKV": FormatDef(
        name="MKV",
        extension=".mkv",
        category="video",
        description="Matroska (Enthusiast, Multi-audio, Subtitles, Archiving)",
        default_vcodec="H.264",
        default_acodec="AAC",
        supported_vcodecs=["H.264", "H.265 (HEVC)", "AV1", "VP9", "Copy (Lossless)"],
        supported_acodecs=["AAC", "Opus", "FLAC", "AC3", "MP3", "Copy (Lossless)", "No Audio"]
    ),
    "WebM": FormatDef(
        name="WebM",
        extension=".webm",
        category="video",
        description="Modern Web Standard (Lightweight, HTML5 video)",
        default_vcodec="VP9",
        default_acodec="Opus",
        supported_vcodecs=["VP9", "AV1", "VP8", "Copy (Lossless)"],
        supported_acodecs=["Opus", "Vorbis", "Copy (Lossless)", "No Audio"]
    ),
    "MOV": FormatDef(
        name="MOV",
        extension=".mov",
        category="video",
        description="Apple QuickTime (macOS, iOS, ProRes editing)",
        default_vcodec="H.264",
        default_acodec="AAC",
        supported_vcodecs=["H.264", "H.265 (HEVC)", "ProRes", "Copy (Lossless)"],
        supported_acodecs=["AAC", "PCM (Lossless)", "Copy (Lossless)", "No Audio"]
    ),
    "AVI": FormatDef(
        name="AVI",
        extension=".avi",
        category="video",
        description="Audio Video Interleave (Legacy players, Car stereos)",
        default_vcodec="H.264",
        default_acodec="MP3",
        supported_vcodecs=["H.264", "MPEG-4", "Xvid", "Copy (Lossless)"],
        supported_acodecs=["MP3", "AC3", "Copy (Lossless)", "No Audio"]
    ),
    "WMV": FormatDef(
        name="WMV",
        extension=".wmv",
        category="video",
        description="Windows Media Video (Legacy Windows PCs)",
        default_vcodec="WMV2",
        default_acodec="WMA2",
        supported_vcodecs=["WMV2", "WMV1"],
        supported_acodecs=["WMA2", "No Audio"]
    ),
    "TS": FormatDef(
        name="TS",
        extension=".ts",
        category="video",
        description="MPEG Transport Stream (Broadcast & IPTV)",
        default_vcodec="H.264",
        default_acodec="AAC",
        supported_vcodecs=["H.264", "H.265 (HEVC)", "MPEG-2", "Copy (Lossless)"],
        supported_acodecs=["AAC", "AC3", "MP3", "Copy (Lossless)", "No Audio"]
    ),
    "GIF": FormatDef(
        name="GIF",
        extension=".gif",
        category="video",
        description="High-Quality Animated GIF (Color palette optimized)",
        default_vcodec="GIF",
        default_acodec="No Audio",
        supported_vcodecs=["GIF"],
        supported_acodecs=["No Audio"]
    ),

    # Audio Extraction Formats
    "MP3": FormatDef(
        name="MP3",
        extension=".mp3",
        category="audio",
        description="Universal Audio (Plays on all devices)",
        default_vcodec="None",
        default_acodec="MP3",
        supported_vcodecs=[],
        supported_acodecs=["MP3"]
    ),
    "WAV": FormatDef(
        name="WAV",
        extension=".wav",
        category="audio",
        description="Uncompressed Studio Master Audio (Lossless PCM)",
        default_vcodec="None",
        default_acodec="PCM (16-bit)",
        supported_vcodecs=[],
        supported_acodecs=["PCM (16-bit)", "PCM (24-bit)"]
    ),
    "AAC": FormatDef(
        name="AAC",
        extension=".m4a",
        category="audio",
        description="Advanced Audio Coding (M4A container, high efficiency)",
        default_vcodec="None",
        default_acodec="AAC",
        supported_vcodecs=[],
        supported_acodecs=["AAC", "Copy (Lossless)"]
    ),
    "FLAC": FormatDef(
        name="FLAC",
        extension=".flac",
        category="audio",
        description="Free Lossless Audio Codec (Compressed Lossless)",
        default_vcodec="None",
        default_acodec="FLAC",
        supported_vcodecs=[],
        supported_acodecs=["FLAC"]
    ),
    "OPUS": FormatDef(
        name="OPUS",
        extension=".opus",
        category="audio",
        description="Opus Interactive Audio (State-of-the-art compression)",
        default_vcodec="None",
        default_acodec="Opus",
        supported_vcodecs=[],
        supported_acodecs=["Opus"]
    ),
    "OGG": FormatDef(
        name="OGG",
        extension=".ogg",
        category="audio",
        description="Ogg Vorbis Audio (Open source)",
        default_vcodec="None",
        default_acodec="Vorbis",
        supported_vcodecs=[],
        supported_acodecs=["Vorbis"]
    ),
}

RESOLUTIONS = [
    "Original",
    "4K UHD (3840x2160)",
    "2K QHD (2560x1440)",
    "1080p FHD (1920x1080)",
    "720p HD (1280x720)",
    "480p SD (854x480)",
    "360p (640x360)"
]

RESOLUTION_MAP = {
    "4K UHD (3840x2160)": (3840, 2160),
    "2K QHD (2560x1440)": (2560, 1440),
    "1080p FHD (1920x1080)": (1920, 1080),
    "720p HD (1280x720)": (1280, 720),
    "480p SD (854x480)": (854, 480),
    "360p (640x360)": (640, 360)
}

QUALITY_PRESETS = [
    "High Quality (CRF 18 - Visually Lossless)",
    "Balanced (CRF 23 - Recommended)",
    "Compact Size (CRF 28 - Small File)",
    "Ultra Compact (CRF 32 - Minimum File Size)"
]

CRF_VALUES = {
    "High Quality (CRF 18 - Visually Lossless)": 18,
    "Balanced (CRF 23 - Recommended)": 23,
    "Compact Size (CRF 28 - Small File)": 28,
    "Ultra Compact (CRF 32 - Minimum File Size)": 32
}

FRAME_RATES = [
    "Original",
    "60 FPS",
    "30 FPS",
    "25 FPS (PAL)",
    "24 FPS (Cinematic)"
]

FPS_MAP = {
    "60 FPS": 60,
    "30 FPS": 30,
    "25 FPS (PAL)": 25,
    "24 FPS (Cinematic)": 24
}

AUDIO_BITRATES = [
    "Original",
    "320 kbps (High Fidelity)",
    "256 kbps",
    "192 kbps (Standard)",
    "128 kbps (Compact)",
    "96 kbps (Voice / Low Size)",
    "Mute (Remove Audio)"
]

AUDIO_BITRATE_MAP = {
    "320 kbps (High Fidelity)": "320k",
    "256 kbps": "256k",
    "192 kbps (Standard)": "192k",
    "128 kbps (Compact)": "128k",
    "96 kbps (Voice / Low Size)": "96k"
}

HARDWARE_ACCEL_OPTIONS = [
    "Auto Detect (Fastest Available)",
    "NVIDIA NVENC (GeForce / Quadro)",
    "AMD AMF (Radeon)",
    "Intel QSV (Quick Sync)",
    "Software (CPU - Highest Compatibility)"
]

INPUT_VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv",
    ".ts", ".mts", ".m2ts", ".m4v", ".3gp", ".ogv", ".vob",
    ".mpg", ".mpeg", ".divx", ".xvid", ".asf", ".rmvb", ".gif"
}

