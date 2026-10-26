import os
import customtkinter as ctk
from typing import Callable, List
from tkinter import filedialog


class DropTarget(ctk.CTkFrame):
    """Drag-and-drop zone and file browsing card."""

    def __init__(
        self,
        master,
        on_files_added: Callable[[List[str]], None],
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=("#F8FAFC", "#0F172A"),
            border_width=2,
            border_color=("#CBD5E1", "#334155"),
            **kwargs
        )
        self.on_files_added = on_files_added

        self._build_ui()
        self._setup_dnd()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Center Container
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0, pady=24, padx=20)

        # Upload Graphic / Icon Badge
        self.icon_badge = ctk.CTkLabel(
            center,
            text="📁 ⇪",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=32),
            text_color=("#3B82F6", "#60A5FA")
        )
        self.icon_badge.pack(pady=(0, 6))

        # Main instructions
        self.title_label = ctk.CTkLabel(
            center,
            text="Drag & Drop Video or Audio Files Here",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        self.title_label.pack()

        self.subtitle_label = ctk.CTkLabel(
            center,
            text="Supports MP4, MKV, WebM, MOV, AVI, WMV, TS, FLV, GIF & 20+ more",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748B", "#94A3B8")
        )
        self.subtitle_label.pack(pady=(2, 14))

        # Action Buttons row
        btn_row = ctk.CTkFrame(center, fg_color="transparent")
        btn_row.pack()

        self.browse_files_btn = ctk.CTkButton(
            btn_row,
            text="Select Files",
            width=130,
            height=34,
            corner_radius=8,
            fg_color=("#2563EB", "#3B82F6"),
            hover_color=("#1D4ED8", "#2563EB"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_browse_files
        )
        self.browse_files_btn.pack(side="left", padx=6)

        self.browse_dir_btn = ctk.CTkButton(
            btn_row,
            text="Select Folder",
            width=130,
            height=34,
            corner_radius=8,
            fg_color=("#E2E8F0", "#1E293B"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#334155"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_browse_folder
        )
        self.browse_dir_btn.pack(side="left", padx=6)

    def _setup_dnd(self):
        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        except Exception:
            # Fallback if dnd is not registered on this specific widget
            pass

    def _on_drag_enter(self, event):
        self.configure(border_color=("#2563EB", "#60A5FA"), border_width=2)

    def _on_drag_leave(self, event):
        self.configure(border_color=("#CBD5E1", "#334155"), border_width=2)

    def _on_drop(self, event):
        self._on_drag_leave(event)
        data = event.data
        if not data:
            return

        # Parse file paths from TkinterDnD (can be space separated or brace enclosed)
        file_paths = self._parse_dnd_data(data)
        if file_paths:
            self.on_files_added(file_paths)

    def _parse_dnd_data(self, data: str) -> List[str]:
        files = []
        # Handle curly-brace format {path with spaces}
        if "{" in data:
            import re
            pattern = re.compile(r"\{([^}]+)\}|(\S+)")
            for match in pattern.finditer(data):
                p = match.group(1) or match.group(2)
                if p and os.path.exists(p):
                    files.append(os.path.normpath(p))
        else:
            for item in data.split():
                if os.path.exists(item):
                    files.append(os.path.normpath(item))
        return files

    def _on_browse_files(self):
        types = [
            ("All Media Files", "*.mp4 *.mkv *.mov *.avi *.webm *.flv *.wmv *.ts *.mts *.m2ts *.m4v *.3gp *.ogv *.gif *.mp3 *.wav *.aac *.flac *.opus *.ogg"),
            ("Video Files", "*.mp4 *.mkv *.mov *.avi *.webm *.flv *.wmv *.ts *.m4v *.3gp *.gif"),
            ("Audio Files", "*.mp3 *.wav *.aac *.flac *.opus *.ogg *.m4a *.wma"),
            ("All Files", "*.*")
        ]
        chosen = filedialog.askopenfilenames(
            title="Choose Media Files to Convert",
            filetypes=types
        )
        if chosen:
            self.on_files_added(list(chosen))

    def _on_browse_folder(self):
        folder = filedialog.askdirectory(title="Choose Folder Containing Media Files")
        if folder:
            found = []
            for root, _, files in os.walk(folder):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".ts", ".mts", ".m4v", ".3gp", ".gif", ".mp3", ".wav", ".flac", ".aac", ".opus", ".ogg"]:
                        found.append(os.path.join(root, f))
            if found:
                self.on_files_added(found)

