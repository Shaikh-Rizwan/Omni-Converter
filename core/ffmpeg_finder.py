import os
import shutil
import subprocess
import sys
import winreg
from pathlib import Path
from typing import Optional, Tuple, Dict, Set


class FFmpegFinder:
    """Discovers FFmpeg and FFprobe binaries and probes hardware encoder capabilities."""

    _cached_ffmpeg: Optional[str] = None
    _cached_ffprobe: Optional[str] = None
    _cached_hw_accels: Optional[Dict[str, bool]] = None

    @classmethod
    def get_paths(cls) -> Tuple[Optional[str], Optional[str]]:
        """Finds both ffmpeg and ffprobe paths."""
        ffmpeg = cls.find_ffmpeg()
        ffprobe = cls.find_ffprobe()
        return ffmpeg, ffprobe

    @classmethod
    def find_ffmpeg(cls) -> Optional[str]:
        if cls._cached_ffmpeg and os.path.exists(cls._cached_ffmpeg):
            return cls._cached_ffmpeg

        # 1. Bundled / App Directory (Primary for standalone release)
        candidates = []
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
            candidates.extend([
                app_dir / "bin" / "ffmpeg.exe",
                app_dir / "ffmpeg.exe"
            ])
            if hasattr(sys, '_MEIPASS'):
                candidates.extend([
                    Path(sys._MEIPASS) / "bin" / "ffmpeg.exe",
                    Path(sys._MEIPASS) / "ffmpeg.exe"
                ])

        candidates.extend([
            Path("bin/ffmpeg.exe"),
            Path("ffmpeg.exe"),
            Path(__file__).parent.parent / "bin" / "ffmpeg.exe",
        ])

        for c in candidates:
            if c.exists():
                cls._cached_ffmpeg = str(c.resolve())
                return cls._cached_ffmpeg

        # 2. System PATH
        path = shutil.which("ffmpeg")
        if path and os.path.exists(path):
            cls._cached_ffmpeg = path
            return path

        # 3. Check WinGet Packages
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            winget_dir = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
            if winget_dir.exists():
                for found in winget_dir.glob("**/ffmpeg.exe"):
                    if found.is_file():
                        cls._cached_ffmpeg = str(found.resolve())
                        return cls._cached_ffmpeg

        # 4. Check registry User/Machine PATH
        reg_paths = cls._get_registry_paths()
        for p in reg_paths:
            candidate = Path(p) / "ffmpeg.exe"
            if candidate.exists():
                cls._cached_ffmpeg = str(candidate.resolve())
                return cls._cached_ffmpeg

        # 5. Common installation directories
        common_dirs = [
            Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
            Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
            Path(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"),
            Path(os.environ.get("USERPROFILE", "")) / "scoop" / "shims" / "ffmpeg.exe",
        ]
        for c in common_dirs:
            if c.exists():
                cls._cached_ffmpeg = str(c.resolve())
                return cls._cached_ffmpeg

        return None

    @classmethod
    def find_ffprobe(cls) -> Optional[str]:
        if cls._cached_ffprobe and os.path.exists(cls._cached_ffprobe):
            return cls._cached_ffprobe

        # 1. Same folder as ffmpeg
        ffmpeg = cls.find_ffmpeg()
        if ffmpeg:
            sibling = Path(ffmpeg).parent / "ffprobe.exe"
            if sibling.exists():
                cls._cached_ffprobe = str(sibling.resolve())
                return cls._cached_ffprobe

        # 2. Bundled / App Directory candidates
        candidates = []
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
            candidates.extend([
                app_dir / "bin" / "ffprobe.exe",
                app_dir / "ffprobe.exe"
            ])
            if hasattr(sys, '_MEIPASS'):
                candidates.extend([
                    Path(sys._MEIPASS) / "bin" / "ffprobe.exe",
                    Path(sys._MEIPASS) / "ffprobe.exe"
                ])

        candidates.extend([
            Path("bin/ffprobe.exe"),
            Path("ffprobe.exe"),
            Path(__file__).parent.parent / "bin" / "ffprobe.exe",
        ])

        for c in candidates:
            if c.exists():
                cls._cached_ffprobe = str(c.resolve())
                return cls._cached_ffprobe

        # 3. System PATH
        path = shutil.which("ffprobe")
        if path and os.path.exists(path):
            cls._cached_ffprobe = path
            return path

        # 3. Check WinGet Packages
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            winget_dir = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
            if winget_dir.exists():
                for found in winget_dir.glob("**/ffprobe.exe"):
                    if found.is_file():
                        cls._cached_ffprobe = str(found.resolve())
                        return cls._cached_ffprobe

        return None

    @classmethod
    def _get_registry_paths(cls) -> list[str]:
        results = []
        # HKCU Environment
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                user_path, _ = winreg.QueryValueEx(key, "Path")
                results.extend(user_path.split(";"))
        except Exception:
            pass

        # HKLM Environment
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
            ) as key:
                sys_path, _ = winreg.QueryValueEx(key, "Path")
                results.extend(sys_path.split(";"))
        except Exception:
            pass

        return [p.strip() for p in results if p.strip()]

    @classmethod
    def get_hardware_acceleration_support(cls) -> Dict[str, bool]:
        """Probes for NVIDIA NVENC, AMD AMF, and Intel QSV encoder support."""
        if cls._cached_hw_accels is not None:
            return cls._cached_hw_accels

        ffmpeg = cls.find_ffmpeg()
        results = {"nvenc": False, "amf": False, "qsv": False}
        if not ffmpeg:
            cls._cached_hw_accels = results
            return results

        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            out = subprocess.check_output(
                [ffmpeg, "-encoders"],
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            # Test actual presence of encoders in output
            if "h264_nvenc" in out or "hevc_nvenc" in out:
                results["nvenc"] = True
            if "h264_amf" in out or "hevc_amf" in out:
                results["amf"] = True
            if "h264_qsv" in out or "hevc_qsv" in out:
                results["qsv"] = True

        except Exception:
            pass

        cls._cached_hw_accels = results
        return results

