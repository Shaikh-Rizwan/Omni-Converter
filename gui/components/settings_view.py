import os
import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Dict, Any

from core.presets import (
    SUPPORTED_FORMATS,
    RESOLUTIONS,
    QUALITY_PRESETS,
    FRAME_RATES,
    AUDIO_BITRATES,
    HARDWARE_ACCEL_OPTIONS
)
from core.ffmpeg_finder import FFmpegFinder


class SettingsView(ctk.CTkScrollableFrame):
    """Configuration panel for target format, codecs, quality, and hardware acceleration."""

    def __init__(
        self,
        master,
        on_settings_changed: Callable[[], None],
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#CBD5E1", "#334155"),
            **kwargs
        )
        self.on_settings_changed = on_settings_changed
        self._hw_support = FFmpegFinder.get_hardware_acceleration_support()

        # Default output folder: ./Converted_Videos
        self.default_out_dir = os.path.abspath(os.path.join(".", "Converted_Videos"))
        os.makedirs(self.default_out_dir, exist_ok=True)

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header Title
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=14, pady=(14, 10))

        title_lbl = ctk.CTkLabel(
            title_box,
            text="Conversion Settings",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        title_lbl.pack(side="left")

        # Hardware acceleration badge
        hw_text = "HW: CPU"
        hw_color = ("#94A3B8", "#475569")
        if self._hw_support.get("nvenc"):
            hw_text = "⚡ NVENC Ready"
            hw_color = ("#16A34A", "#22C55E")
        elif self._hw_support.get("amf"):
            hw_text = "⚡ AMF Ready"
            hw_color = ("#DC2626", "#EF4444")
        elif self._hw_support.get("qsv"):
            hw_text = "⚡ QSV Ready"
            hw_color = ("#2563EB", "#3B82F6")

        self.hw_badge = ctk.CTkLabel(
            title_box,
            text=hw_text,
            corner_radius=6,
            fg_color=("#F1F5F9", "#0F172A"),
            text_color=hw_color,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold")
        )
        self.hw_badge.pack(side="right")

        # Category Tab Buttons (Video / Audio Extract / Animated GIF)
        self.category_var = ctk.StringVar(value="Video")
        self.cat_segmented = ctk.CTkSegmentedButton(
            self,
            values=["Video", "Audio Extract", "GIF Maker"],
            variable=self.category_var,
            command=self._on_category_changed,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            selected_color=("#2563EB", "#3B82F6")
        )
        self.cat_segmented.pack(fill="x", padx=14, pady=(0, 14))

        # --- Section 1: Output Format ---
        self._build_label("OUTPUT FORMAT")
        self.format_var = ctk.StringVar(value="MP4")
        self.format_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.format_var,
            values=["MP4", "MKV", "WebM", "MOV", "AVI", "WMV", "TS"],
            command=self._on_format_changed,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#2563EB", "#3B82F6"),
            button_color=("#1D4ED8", "#2563EB")
        )
        self.format_dropdown.pack(fill="x", padx=14, pady=(2, 6))

        # Format Description Hint
        self.desc_label = ctk.CTkLabel(
            self,
            text=SUPPORTED_FORMATS["MP4"].description,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=("#64748B", "#94A3B8"),
            wraplength=260,
            justify="left"
        )
        self.desc_label.pack(fill="x", padx=14, pady=(0, 10))

        # --- Section 2: Video & Audio Codecs ---
        self.vcodec_label = self._build_label("VIDEO CODEC")
        self.vcodec_var = ctk.StringVar(value="H.264")
        self.vcodec_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.vcodec_var,
            values=["H.264", "H.265 (HEVC)", "AV1", "Copy (Lossless)"],
            command=self._on_codec_changed,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.vcodec_dropdown.pack(fill="x", padx=14, pady=(2, 10))

        self.acodec_label = self._build_label("AUDIO CODEC")
        self.acodec_var = ctk.StringVar(value="AAC")
        self.acodec_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.acodec_var,
            values=["AAC", "MP3", "AC3", "Copy (Lossless)", "No Audio"],
            command=self._on_codec_changed,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.acodec_dropdown.pack(fill="x", padx=14, pady=(2, 12))

        # Separator line
        self._build_separator()

        # --- Section 3: Quality, Resolution & FPS ---
        self.quality_label = self._build_label("QUALITY / COMPRESSION")
        self.quality_var = ctk.StringVar(value="Balanced (CRF 23 - Recommended)")
        self.quality_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.quality_var,
            values=QUALITY_PRESETS,
            command=self._trigger_change,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.quality_dropdown.pack(fill="x", padx=14, pady=(2, 10))

        self.res_label = self._build_label("RESOLUTION")
        self.res_var = ctk.StringVar(value="Original")
        self.res_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.res_var,
            values=RESOLUTIONS,
            command=self._trigger_change,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.res_dropdown.pack(fill="x", padx=14, pady=(2, 10))

        self.fps_label = self._build_label("FRAME RATE")
        self.fps_var = ctk.StringVar(value="Original")
        self.fps_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.fps_var,
            values=FRAME_RATES,
            command=self._trigger_change,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.fps_dropdown.pack(fill="x", padx=14, pady=(2, 10))

        self.audio_bitrate_label = self._build_label("AUDIO BITRATE")
        self.audio_bitrate_var = ctk.StringVar(value="192 kbps (Standard)")
        self.audio_bitrate_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.audio_bitrate_var,
            values=AUDIO_BITRATES,
            command=self._trigger_change,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.audio_bitrate_dropdown.pack(fill="x", padx=14, pady=(2, 12))

        # Separator line
        self._build_separator()

        # --- Section 4: Hardware Acceleration ---
        self._build_label("HARDWARE ACCELERATION")
        self.hw_var = ctk.StringVar(value="Auto Detect (Fastest Available)")
        self.hw_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.hw_var,
            values=HARDWARE_ACCEL_OPTIONS,
            command=self._trigger_change,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.hw_dropdown.pack(fill="x", padx=14, pady=(2, 12))

        # Separator line
        self._build_separator()

        # --- Section 5: Destination Folder ---
        self._build_label("OUTPUT DESTINATION")
        dest_box = ctk.CTkFrame(self, fg_color="transparent")
        dest_box.pack(fill="x", padx=14, pady=(2, 6))

        self.dest_var = ctk.StringVar(value=self.default_out_dir)
        self.dest_entry = ctk.CTkEntry(
            dest_box,
            textvariable=self.dest_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            height=30
        )
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.browse_dest_btn = ctk.CTkButton(
            dest_box,
            text="📁",
            width=36,
            height=30,
            command=self._on_browse_dest
        )
        self.browse_dest_btn.pack(side="right")

        # Switches
        self.open_folder_var = ctk.BooleanVar(value=True)
        self.open_folder_switch = ctk.CTkCheckBox(
            self,
            text="Open folder when completed",
            variable=self.open_folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.open_folder_switch.pack(anchor="w", padx=14, pady=(6, 16))

    def _build_label(self, text: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=("#64748B", "#94A3B8"),
            anchor="w"
        )
        lbl.pack(fill="x", padx=14, pady=(4, 0))
        return lbl

    def _build_separator(self):
        sep = ctk.CTkFrame(self, height=1, fg_color=("#E2E8F0", "#334155"))
        sep.pack(fill="x", padx=14, pady=8)

    def _on_category_changed(self, cat: str):
        if cat == "Video":
            video_formats = ["MP4", "MKV", "WebM", "MOV", "AVI", "WMV", "TS"]
            self.format_dropdown.configure(values=video_formats)
            self.format_var.set("MP4")
            self._show_video_controls(True)
            self._on_format_changed("MP4")
        elif cat == "Audio Extract":
            audio_formats = ["MP3", "WAV", "AAC", "FLAC", "OPUS", "OGG"]
            self.format_dropdown.configure(values=audio_formats)
            self.format_var.set("MP3")
            self._show_video_controls(False)
            self._on_format_changed("MP3")
        elif cat == "GIF Maker":
            self.format_dropdown.configure(values=["GIF"])
            self.format_var.set("GIF")
            self._show_video_controls(True)
            self._on_format_changed("GIF")

    def _show_video_controls(self, is_video: bool):
        if is_video:
            self.vcodec_dropdown.configure(state="normal")
            self.quality_dropdown.configure(state="normal")
            self.res_dropdown.configure(state="normal")
            self.fps_dropdown.configure(state="normal")
        else:
            self.vcodec_dropdown.configure(state="disabled")
            self.quality_dropdown.configure(state="disabled")
            self.res_dropdown.configure(state="disabled")
            self.fps_dropdown.configure(state="disabled")

    def _on_format_changed(self, fmt: str):
        info = SUPPORTED_FORMATS.get(fmt)
        if not info:
            return

        self.desc_label.configure(text=info.description)

        # Update codecs
        if info.category == "video":
            if fmt == "GIF":
                self.vcodec_dropdown.configure(values=["GIF"])
                self.vcodec_var.set("GIF")
                self.acodec_dropdown.configure(values=["No Audio"])
                self.acodec_var.set("No Audio")
                self.audio_bitrate_dropdown.configure(state="disabled")
            else:
                self.vcodec_dropdown.configure(values=info.supported_vcodecs)
                self.vcodec_var.set(info.default_vcodec)
                self.acodec_dropdown.configure(values=info.supported_acodecs)
                self.acodec_var.set(info.default_acodec)
                self.audio_bitrate_dropdown.configure(state="normal")
        else:
            # Audio mode
            self.vcodec_dropdown.configure(values=["None"])
            self.vcodec_var.set("None")
            self.acodec_dropdown.configure(values=info.supported_acodecs)
            self.acodec_var.set(info.default_acodec)
            self.audio_bitrate_dropdown.configure(state="normal")

        self._trigger_change()

    def _on_codec_changed(self, _=None):
        self._trigger_change()

    def _trigger_change(self, _=None):
        if self.on_settings_changed:
            self.on_settings_changed()

    def _on_browse_dest(self):
        folder = filedialog.askdirectory(title="Choose Output Destination Folder")
        if folder:
            self.dest_var.set(folder)

    def get_settings(self) -> Dict[str, Any]:
        fmt = self.format_var.get()
        info = SUPPORTED_FORMATS.get(fmt)
        ext = info.extension if info else ".mp4"

        return {
            "format": fmt,
            "extension": ext,
            "vcodec": self.vcodec_var.get(),
            "acodec": self.acodec_var.get(),
            "quality": self.quality_var.get(),
            "resolution": self.res_var.get(),
            "fps": self.fps_var.get(),
            "audio_bitrate": self.audio_bitrate_var.get(),
            "hw_accel": self.hw_var.get(),
            "output_dir": self.dest_var.get(),
            "open_folder": self.open_folder_var.get()
        }

    def get_summary_string(self) -> str:
        fmt = self.format_var.get()
        info = SUPPORTED_FORMATS.get(fmt)
        if not info:
            return fmt
        if info.category == "audio":
            return f"{fmt} ({self.acodec_var.get()})"
        if fmt == "GIF":
            return f"GIF ({self.fps_var.get()})"
        return f"{fmt} ({self.vcodec_var.get()})"

