import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .ffmpeg_finder import FFmpegFinder


@dataclass
class MediaInfo:
    file_path: str
    file_name: str
    file_size_bytes: int
    file_size_str: str
    duration_seconds: float
    duration_str: str
    width: int
    height: int
    resolution_str: str
    video_codec: str
    audio_codec: str
    fps: float
    bitrate_kbps: int
    has_video: bool
    has_audio: bool
    raw_info: Dict[str, Any]


class MediaProbe:
    """Uses ffprobe to extract rich metadata about media files."""

    @staticmethod
    def format_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def format_duration(seconds: float) -> str:
        if seconds <= 0:
            return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @classmethod
    def probe(cls, file_path: str) -> Optional[MediaInfo]:
        if not os.path.exists(file_path):
            return None

        _, ffprobe = FFmpegFinder.get_paths()
        if not ffprobe:
            return None

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                encoding="utf-8",
                errors="ignore"
            )
            if result.returncode != 0 or not result.stdout:
                return None

            data = json.loads(result.stdout)
            format_info = data.get("format", {})
            streams = data.get("streams", [])

            file_size_bytes = int(format_info.get("size", os.path.getsize(file_path)))
            duration = float(format_info.get("duration", 0.0))

            video_stream = None
            audio_stream = None

            for stream in streams:
                codec_type = stream.get("codec_type")
                if codec_type == "video" and not video_stream:
                    # Filter out attached picture thumbnails if any
                    disposition = stream.get("disposition", {})
                    if disposition.get("attached_pic", 0) != 1:
                        video_stream = stream
                elif codec_type == "audio" and not audio_stream:
                    audio_stream = stream

            width = 0
            height = 0
            video_codec = "None"
            fps = 0.0

            if video_stream:
                width = int(video_stream.get("width", 0))
                height = int(video_stream.get("height", 0))
                video_codec = video_stream.get("codec_name", "unknown")

                # Frame rate parsing
                r_fps = video_stream.get("r_frame_rate", "0/0")
                if "/" in r_fps:
                    num, den = r_fps.split("/")
                    if float(den) > 0:
                        fps = round(float(num) / float(den), 2)
                elif r_fps:
                    fps = round(float(r_fps), 2)

                if duration == 0.0:
                    stream_dur = video_stream.get("duration")
                    if stream_dur:
                        duration = float(stream_dur)

            audio_codec = "None"
            if audio_stream:
                audio_codec = audio_stream.get("codec_name", "unknown")
                if duration == 0.0:
                    stream_dur = audio_stream.get("duration")
                    if stream_dur:
                        duration = float(stream_dur)

            bitrate = int(format_info.get("bit_rate", 0)) // 1000

            res_str = f"{width}x{height}" if width and height else "Audio Only"

            return MediaInfo(
                file_path=file_path,
                file_name=os.path.basename(file_path),
                file_size_bytes=file_size_bytes,
                file_size_str=cls.format_size(file_size_bytes),
                duration_seconds=duration,
                duration_str=cls.format_duration(duration),
                width=width,
                height=height,
                resolution_str=res_str,
                video_codec=video_codec.upper(),
                audio_codec=audio_codec.upper(),
                fps=fps,
                bitrate_kbps=bitrate,
                has_video=video_stream is not None,
                has_audio=audio_stream is not None,
                raw_info=data
            )

        except Exception as e:
            print(f"Error probing {file_path}: {e}")
            return None

