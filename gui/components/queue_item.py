import customtkinter as ctk
from typing import Callable, Optional
from core.media_probe import MediaInfo


class QueueItemCard(ctk.CTkFrame):
    """Visual card for an item in the conversion queue."""

    def __init__(
        self,
        master,
        item_id: str,
        media_info: MediaInfo,
        target_summary: str,
        on_remove: Callable[[str], None],
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=8,
            fg_color=("#F1F5F9", "#1E293B"),
            border_width=1,
            border_color=("#CBD5E1", "#334155"),
            **kwargs
        )
        self.item_id = item_id
        self.media_info = media_info
        self.target_summary = target_summary
        self.on_remove = on_remove

        self._build_ui()

    def _build_ui(self):
        # Configure layout
        self.grid_columnconfigure(1, weight=1)

        # 1. Format Badge
        ext = self.media_info.file_name.split(".")[-1].upper() if "." in self.media_info.file_name else "VID"
        self.badge_label = ctk.CTkLabel(
            self,
            text=ext,
            width=50,
            height=28,
            corner_radius=6,
            fg_color=("#3B82F6", "#2563EB"),
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.badge_label.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10)

        # 2. Main Title and Target
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="w", pady=(8, 2))

        # Truncate filename if long
        fname = self.media_info.file_name
        if len(fname) > 42:
            fname = fname[:39] + "..."

        self.name_label = ctk.CTkLabel(
            info_frame,
            text=fname,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        self.name_label.pack(side="left")

        # Target pill
        self.target_pill = ctk.CTkLabel(
            info_frame,
            text=f"  ➜  {self.target_summary}  ",
            corner_radius=6,
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#2563EB", "#60A5FA"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.target_pill.pack(side="left", padx=8)

        # 3. Subtitle Info (Resolution, Duration, Codecs, Size)
        meta_parts = []
        if self.media_info.resolution_str != "Audio Only":
            meta_parts.append(self.media_info.resolution_str)
        meta_parts.append(self.media_info.duration_str)
        meta_parts.append(self.media_info.file_size_str)
        if self.media_info.video_codec != "None":
            meta_parts.append(self.media_info.video_codec)
        if self.media_info.audio_codec != "None":
            meta_parts.append(self.media_info.audio_codec)

        meta_text = " • ".join(meta_parts)
        self.meta_label = ctk.CTkLabel(
            self,
            text=meta_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748B", "#94A3B8")
        )
        self.meta_label.grid(row=1, column=1, sticky="w", pady=(0, 6))

        # 4. Right Status and Remove Button
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=2, rowspan=2, padx=(10, 12), pady=8, sticky="e")

        self.status_badge = ctk.CTkLabel(
            right_frame,
            text="Ready",
            width=70,
            height=24,
            corner_radius=6,
            fg_color=("#E2E8F0", "#1E293B"),
            text_color=("#475569", "#CBD5E1"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.status_badge.pack(side="left", padx=(0, 8))

        self.remove_btn = ctk.CTkButton(
            right_frame,
            text="✕",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            text_color=("#94A3B8", "#64748B"),
            hover_color=("#FEE2E2", "#7F1D1D"),
            command=lambda: self.on_remove(self.item_id),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.remove_btn.pack(side="right")

        # 5. Progress Bar and Dynamic Status (Row 2, spanning columns)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=6,
            corner_radius=3,
            fg_color=("#E2E8F0", "#334155"),
            progress_color=("#2563EB", "#3B82F6")
        )
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(2, 4))

        self.progress_detail = ctk.CTkLabel(
            self.progress_frame,
            text="Waiting in queue...",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=("#64748B", "#94A3B8")
        )
        self.progress_detail.grid(row=1, column=0, sticky="w")

    def update_target(self, new_summary: str):
        self.target_summary = new_summary
        self.target_pill.configure(text=f"  ➜  {new_summary}  ")

    def set_converting(self, pct: float, speed: str, eta: str):
        self.progress_bar.set(pct / 100.0)
        self.status_badge.configure(
            text=f"{int(pct)}%",
            fg_color=("#DBEAFE", "#1E3A8A"),
            text_color=("#1D4ED8", "#93C5FD")
        )
        detail = f"{pct:.1f}%"
        if speed:
            detail += f" • Speed: {speed}"
        if eta and eta != "--:--":
            detail += f" • ETA: {eta}"
        self.progress_detail.configure(text=detail, text_color=("#2563EB", "#60A5FA"))
        self.remove_btn.configure(state="disabled")

    def set_completed(self):
        self.progress_bar.set(1.0)
        self.progress_bar.configure(progress_color=("#16A34A", "#22C55E"))
        self.status_badge.configure(
            text="Done ✓",
            fg_color=("#DCFCE7", "#14532D"),
            text_color=("#15803D", "#86EFAC")
        )
        self.progress_detail.configure(
            text="Conversion completed successfully",
            text_color=("#15803D", "#86EFAC")
        )
        self.remove_btn.configure(state="normal")

    def set_error(self, message: str):
        self.progress_bar.configure(progress_color=("#DC2626", "#EF4444"))
        self.status_badge.configure(
            text="Failed",
            fg_color=("#FEE2E2", "#7F1D1D"),
            text_color=("#B91C1C", "#FCA5A5")
        )
        first_line = message.split("\n")[-1] if message else "Conversion failed"
        if len(first_line) > 60:
            first_line = first_line[:57] + "..."
        self.progress_detail.configure(
            text=first_line,
            text_color=("#B91C1C", "#FCA5A5")
        )
        self.remove_btn.configure(state="normal")

    def set_cancelled(self):
        self.status_badge.configure(
            text="Stopped",
            fg_color=("#FEF3C7", "#78350F"),
            text_color=("#B45309", "#FDE68A")
        )
        self.progress_detail.configure(
            text="Conversion cancelled",
            text_color=("#B45309", "#FDE68A")
        )
        self.remove_btn.configure(state="normal")

