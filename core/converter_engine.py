import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any

from .ffmpeg_finder import FFmpegFinder
from .presets import (
    SUPPORTED_FORMATS,
    RESOLUTION_MAP,
    CRF_VALUES,
    FPS_MAP,
    AUDIO_BITRATE_MAP,
)


@dataclass
class ConversionJob:
    job_id: str
    input_path: str
    output_path: str
    target_format: str
    vcodec: str
    acodec: str
    resolution: str
    quality: str
    fps: str
    audio_bitrate: str
    hw_accel: str
    duration_seconds: float


@dataclass
class ProgressUpdate:
    job_id: str
    percentage: float
    time_str: str
    speed_str: str
    eta_str: str
    bitrate_str: str
    fps_val: float
    is_finished: bool = False
    is_error: bool = False
    error_message: str = ""


class ConversionEngine:
    """Manages FFmpeg conversion processes with real-time feedback and cancellation."""

    def __init__(self):
        self._current_process: Optional[subprocess.Popen] = None
        self._is_cancelled = False
        self._lock = threading.Lock()

    def cancel(self):
        """Cancels current running conversion process."""
        with self._lock:
            self._is_cancelled = True
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                    # Wait briefly, then kill if still alive
                    threading.Timer(2.0, self._force_kill).start()
                except Exception:
                    pass

    def _force_kill(self):
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.kill()
                except Exception:
                    pass

    def execute(self, job: ConversionJob, progress_callback: Callable[[ProgressUpdate], None]) -> bool:
        """Executes a conversion job synchronously (intended to be called from a worker thread)."""
        with self._lock:
            self._is_cancelled = False

        ffmpeg, _ = FFmpegFinder.get_paths()
        if not ffmpeg:
            progress_callback(
                ProgressUpdate(
                    job_id=job.job_id,
                    percentage=0.0,
                    time_str="00:00",
                    speed_str="",
                    eta_str="",
                    bitrate_str="",
                    fps_val=0.0,
                    is_error=True,
                    error_message="FFmpeg executable was not found."
                )
            )
            return False

        # Build FFmpeg command
        cmd = self._build_command(ffmpeg, job)

        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            os.makedirs(os.path.dirname(os.path.abspath(job.output_path)), exist_ok=True)

            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                startupinfo=startupinfo,
                creationflags=creationflags,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            last_time_us = 0
            start_wall_time = time.time()
            full_log = []

            for line in self._current_process.stdout:
                line = line.strip()
                if not line:
                    continue
                full_log.append(line)
                if len(full_log) > 200:
                    full_log.pop(0)

                # Parse progress lines
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()

                    if key == "out_time_us":
                        try:
                            last_time_us = int(val)
                        except ValueError:
                            pass
                    elif key == "progress" and val == "end":
                        last_time_us = int(job.duration_seconds * 1_000_000)
                    elif key == "speed":
                        speed_str = val
                        current_sec = last_time_us / 1_000_000.0
                        duration = job.duration_seconds

                        percentage = 0.0
                        eta_str = "--:--"
                        if duration > 0:
                            percentage = min(99.9, (current_sec / duration) * 100.0)
                            # Calculate ETA using speed
                            try:
                                num_speed = float(val.replace("x", "").strip())
                                if num_speed > 0.05:
                                    rem_time = (duration - current_sec) / num_speed
                                    if rem_time > 0:
                                        rem_m, rem_s = divmod(int(rem_time), 60)
                                        rem_h, rem_m = divmod(rem_m, 60)
                                        if rem_h > 0:
                                            eta_str = f"{rem_h:02d}:{rem_m:02d}:{rem_s:02d}"
                                        else:
                                            eta_str = f"{rem_m:02d}:{rem_s:02d}"
                            except ValueError:
                                pass

                        m, s = divmod(int(current_sec), 60)
                        h, m = divmod(m, 60)
                        time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

                        progress_callback(
                            ProgressUpdate(
                                job_id=job.job_id,
                                percentage=percentage,
                                time_str=time_str,
                                speed_str=speed_str,
                                eta_str=eta_str,
                                bitrate_str="",
                                fps_val=0.0
                            )
                        )

            self._current_process.wait()
            ret_code = self._current_process.returncode

            if self._is_cancelled:
                # Clean up partial output
                if os.path.exists(job.output_path):
                    try:
                        os.remove(job.output_path)
                    except Exception:
                        pass
                progress_callback(
                    ProgressUpdate(
                        job_id=job.job_id,
                        percentage=0.0,
                        time_str="Cancelled",
                        speed_str="",
                        eta_str="",
                        bitrate_str="",
                        fps_val=0.0,
                        is_error=True,
                        error_message="Conversion was cancelled by user."
                    )
                )
                return False

            if ret_code != 0:
                error_msg = "\n".join(full_log[-10:])
                # Clean up partial file
                if os.path.exists(job.output_path):
                    try:
                        os.remove(job.output_path)
                    except Exception:
                        pass
                progress_callback(
                    ProgressUpdate(
                        job_id=job.job_id,
                        percentage=0.0,
                        time_str="Failed",
                        speed_str="",
                        eta_str="",
                        bitrate_str="",
                        fps_val=0.0,
                        is_error=True,
                        error_message=f"FFmpeg error (code {ret_code}):\n{error_msg}"
                    )
                )
                return False

            # Success
            progress_callback(
                ProgressUpdate(
                    job_id=job.job_id,
                    percentage=100.0,
                    time_str="Done",
                    speed_str="",
                    eta_str="",
                    bitrate_str="",
                    fps_val=0.0,
                    is_finished=True
                )
            )
            return True

        except Exception as e:
            progress_callback(
                ProgressUpdate(
                    job_id=job.job_id,
                    percentage=0.0,
                    time_str="Error",
                    speed_str="",
                    eta_str="",
                    bitrate_str="",
                    fps_val=0.0,
                    is_error=True,
                    error_message=str(e)
                )
            )
            return False
        finally:
            self._current_process = None

    def _build_command(self, ffmpeg: str, job: ConversionJob) -> list[str]:
        fmt_info = SUPPORTED_FORMATS.get(job.target_format)
        is_audio_only = fmt_info and fmt_info.category == "audio"

        cmd = [ffmpeg, "-y", "-i", job.input_path]

        # GIF mode
        if job.target_format == "GIF":
            fps = FPS_MAP.get(job.fps, 15)
            # Default GIF max width 640 or from resolution
            scale_filter = "scale=min(640\\,iw):-2:flags=lanczos"
            if job.resolution in RESOLUTION_MAP:
                w, _ = RESOLUTION_MAP[job.resolution]
                scale_filter = f"scale=min({w}\\,iw):-2:flags=lanczos"

            cmd.extend([
                "-vf", f"fps={fps},{scale_filter},split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
                "-an"
            ])
            cmd.extend(["-progress", "pipe:1", job.output_path])
            return cmd

        # Audio Only Extraction
        if is_audio_only:
            cmd.append("-vn")
            self._append_audio_args(cmd, job)
            cmd.extend(["-progress", "pipe:1", job.output_path])
            return cmd

        # Video stream copy check
        if job.vcodec == "Copy (Lossless)":
            cmd.extend(["-c:v", "copy"])
        else:
            self._append_video_args(cmd, job)

        # Audio stream handling
        self._append_audio_args(cmd, job)

        # Video container optimizations
        if job.target_format in ["MP4", "MOV"]:
            cmd.extend(["-movflags", "+faststart"])

        cmd.extend(["-progress", "pipe:1", job.output_path])
        return cmd

    def _append_video_args(self, cmd: list[str], job: ConversionJob):
        # Determine hardware acceleration
        hw_choice = job.hw_accel
        hw_support = FFmpegFinder.get_hardware_acceleration_support()

        use_nvenc = False
        use_amf = False
        use_qsv = False

        if "Auto Detect" in hw_choice:
            if hw_support.get("nvenc"):
                use_nvenc = True
            elif hw_support.get("amf"):
                use_amf = True
            elif hw_support.get("qsv"):
                use_qsv = True
        elif "NVENC" in hw_choice and hw_support.get("nvenc"):
            use_nvenc = True
        elif "AMF" in hw_choice and hw_support.get("amf"):
            use_amf = True
        elif "QSV" in hw_choice and hw_support.get("qsv"):
            use_qsv = True

        crf = CRF_VALUES.get(job.quality, 23)

        # Codec mappings
        if job.vcodec == "H.264":
            if use_nvenc:
                cmd.extend(["-c:v", "h264_nvenc", "-preset", "p4", "-cq", str(crf)])
            elif use_amf:
                cmd.extend(["-c:v", "h264_amf", "-quality", "balanced"])
            elif use_qsv:
                cmd.extend(["-c:v", "h264_qsv", "-global_quality", str(crf)])
            else:
                cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", str(crf)])
            cmd.extend(["-pix_fmt", "yuv420p"])

        elif "H.265" in job.vcodec or "HEVC" in job.vcodec:
            hevc_crf = crf + 4
            if use_nvenc:
                cmd.extend(["-c:v", "hevc_nvenc", "-preset", "p4", "-cq", str(hevc_crf)])
            elif use_amf:
                cmd.extend(["-c:v", "hevc_amf", "-quality", "balanced"])
            elif use_qsv:
                cmd.extend(["-c:v", "hevc_qsv", "-global_quality", str(hevc_crf)])
            else:
                cmd.extend(["-c:v", "libx265", "-preset", "medium", "-crf", str(hevc_crf)])
            cmd.extend(["-pix_fmt", "yuv420p"])

        elif job.vcodec == "AV1":
            av1_crf = crf + 4
            if use_nvenc:
                cmd.extend(["-c:v", "av1_nvenc", "-preset", "p4", "-cq", str(av1_crf)])
            elif use_amf:
                cmd.extend(["-c:v", "av1_amf"])
            elif use_qsv:
                cmd.extend(["-c:v", "av1_qsv"])
            else:
                cmd.extend(["-c:v", "libaom-av1", "-crf", str(av1_crf), "-b:v", "0", "-cpu-used", "4"])
            cmd.extend(["-pix_fmt", "yuv420p"])

        elif job.vcodec == "VP9":
            vp9_crf = crf + 7
            if use_qsv:
                cmd.extend(["-c:v", "vp9_qsv"])
            else:
                cmd.extend(["-c:v", "libvpx-vp9", "-crf", str(vp9_crf), "-b:v", "0"])

        elif job.vcodec == "VP8":
            cmd.extend(["-c:v", "libvpx", "-b:v", "2M"])

        elif job.vcodec == "ProRes":
            cmd.extend(["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"])

        elif job.vcodec in ["MPEG-4", "Xvid"]:
            cmd.extend(["-c:v", "mpeg4", "-q:v", "3"])

        elif job.vcodec == "WMV2":
            cmd.extend(["-c:v", "wmv2", "-b:v", "4M"])

        elif job.vcodec == "WMV1":
            cmd.extend(["-c:v", "wmv1", "-b:v", "3M"])

        elif job.vcodec == "MPEG-2":
            cmd.extend(["-c:v", "mpeg2video", "-q:v", "2"])

        else:
            cmd.extend(["-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p"])

        # Filters: Resolution Scaling
        filters = []
        if job.resolution in RESOLUTION_MAP:
            target_w, target_h = RESOLUTION_MAP[job.resolution]
            # Maintain aspect ratio and round down to even dimensions
            filters.append(f"scale='min({target_w},iw)':-2")

        # Frame rate
        if job.fps in FPS_MAP:
            cmd.extend(["-r", str(FPS_MAP[job.fps])])

        if filters:
            cmd.extend(["-vf", ",".join(filters)])

    def _append_audio_args(self, cmd: list[str], job: ConversionJob):
        if job.acodec == "No Audio" or job.audio_bitrate == "Mute (Remove Audio)":
            cmd.append("-an")
            return

        if job.acodec == "Copy (Lossless)":
            cmd.extend(["-c:a", "copy"])
            return

        bitrate = AUDIO_BITRATE_MAP.get(job.audio_bitrate, "192k")

        if job.acodec == "AAC":
            cmd.extend(["-c:a", "aac", "-b:a", bitrate])
        elif job.acodec == "MP3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
        elif job.acodec == "Opus":
            cmd.extend(["-c:a", "libopus", "-b:a", bitrate])
        elif job.acodec == "Vorbis":
            cmd.extend(["-c:a", "libvorbis", "-b:a", bitrate])
        elif job.acodec == "FLAC":
            cmd.extend(["-c:a", "flac"])
        elif job.acodec == "PCM (16-bit)":
            cmd.extend(["-c:a", "pcm_s16le"])
        elif job.acodec == "PCM (24-bit)":
            cmd.extend(["-c:a", "pcm_s24le"])
        elif job.acodec == "AC3":
            cmd.extend(["-c:a", "ac3", "-b:a", bitrate])
        elif job.acodec == "WMA2":
            cmd.extend(["-c:a", "wma2", "-b:a", bitrate])
        else:
            cmd.extend(["-c:a", "aac", "-b:a", bitrate])

