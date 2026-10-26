import os
import queue
import subprocess
import threading
import uuid
from typing import Dict, List, Optional
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from core.ffmpeg_finder import FFmpegFinder
from core.media_probe import MediaProbe, MediaInfo
from core.converter_engine import ConversionEngine, ConversionJob, ProgressUpdate
from .components.drop_target import DropTarget
from .components.queue_item import QueueItemCard
from .components.settings_view import SettingsView


class QueuedFile:
    def __init__(self, item_id: str, media_info: MediaInfo, card_widget: QueueItemCard):
        self.item_id = item_id
        self.media_info = media_info
        self.card_widget = card_widget
        self.status = "ready"  # ready, converting, done, error, cancelled
        self.output_path = ""


class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    """Main Application Window for OmniConvert Video Converter."""

    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # Window Configuration
        self.title("OmniConvert - Modern Universal Video Converter")
        self.geometry("1160x780")
        self.minsize(980, 640)

        # Set window icon if available
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Apply dark theme by default
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State
        self.queue_items: Dict[str, QueuedFile] = {}
        self.engine = ConversionEngine()
        self.is_converting = False
        self.worker_thread: Optional[threading.Thread] = None
        self.event_queue = queue.Queue()

        self._build_ui()
        self._check_dependencies()
        self.after(30, self._poll_event_queue)

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Top Header Bar
        self._build_header()

        # 2. Main Body Split Area (Left: Queue & Drop; Right: Settings)
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(10, 10))
        self.body_frame.grid_columnconfigure(0, weight=6)
        self.body_frame.grid_columnconfigure(1, weight=4)
        self.body_frame.grid_rowconfigure(0, weight=1)

        # Left Container (Drop target + Queue)
        self.left_container = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self.left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_container.grid_rowconfigure(2, weight=1)
        self.left_container.grid_columnconfigure(0, weight=1)

        # Drop Zone Card
        self.drop_target = DropTarget(self.left_container, on_files_added=self.add_files)
        self.drop_target.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Queue Header Row
        queue_header = ctk.CTkFrame(self.left_container, fg_color="transparent")
        queue_header.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        self.queue_title = ctk.CTkLabel(
            queue_header,
            text="Conversion Queue (0 files)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        self.queue_title.pack(side="left")

        self.clear_all_btn = ctk.CTkButton(
            queue_header,
            text="Clear All",
            width=80,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            text_color=("#EF4444", "#F87171"),
            hover_color=("#FEE2E2", "#450A0A"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.clear_all_queue
        )
        self.clear_all_btn.pack(side="right")

        self.clear_done_btn = ctk.CTkButton(
            queue_header,
            text="Clear Done",
            width=80,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            text_color=("#64748B", "#94A3B8"),
            hover_color=("#E2E8F0", "#334155"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self.clear_completed_queue
        )
        self.clear_done_btn.pack(side="right", padx=6)

        # Scrollable Queue List
        self.queue_scroll = ctk.CTkScrollableFrame(
            self.left_container,
            corner_radius=12,
            fg_color=("#F8FAFC", "#0F172A"),
            border_width=1,
            border_color=("#CBD5E1", "#1E293B")
        )
        self.queue_scroll.grid(row=2, column=0, sticky="nsew")

        # Empty Queue Placeholder
        self.empty_label = ctk.CTkLabel(
            self.queue_scroll,
            text="No files in conversion queue yet.\nDrag & drop video/audio files above or click 'Select Files'.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#94A3B8", "#64748B")
        )
        self.empty_label.pack(pady=60)

        # Right Container (Settings View)
        self.settings_view = SettingsView(
            self.body_frame,
            on_settings_changed=self._on_settings_changed
        )
        self.settings_view.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # 3. Bottom Control & Batch Progress Bar
        self._build_bottom_bar()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E293B"), height=60, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Logo / Title
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=18, pady=10, sticky="w")

        title = ctk.CTkLabel(
            logo_frame,
            text="⚡ OmniConvert",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=("#2563EB", "#60A5FA")
        )
        title.pack(side="left")

        version_pill = ctk.CTkLabel(
            logo_frame,
            text="v2.0 • Ultra Fast",
            corner_radius=6,
            fg_color=("#DBEAFE", "#1E3A8A"),
            text_color=("#1E40AF", "#93C5FD"),
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold")
        )
        version_pill.pack(side="left", padx=8)

        # Right header controls
        right_header = ctk.CTkFrame(header, fg_color="transparent")
        right_header.grid(row=0, column=2, padx=18, pady=10, sticky="e")

        self.theme_switch = ctk.CTkSwitch(
            right_header,
            text="Dark Mode",
            command=self._toggle_theme,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="right")

    def _build_bottom_bar(self):
        bottom = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E293B"), height=72, corner_radius=0)
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        # Progress row
        prog_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        prog_frame.grid(row=0, column=0, padx=18, pady=12, sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        # Batch status text
        status_box = ctk.CTkFrame(prog_frame, fg_color="transparent")
        status_box.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self.batch_status_label = ctk.CTkLabel(
            status_box,
            text="Ready to convert",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#475569", "#CBD5E1")
        )
        self.batch_status_label.pack(side="left")

        self.batch_counter_label = ctk.CTkLabel(
            status_box,
            text="0 / 0 completed",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748B", "#94A3B8")
        )
        self.batch_counter_label.pack(side="right")

        # Total Progress Bar
        self.batch_progress_bar = ctk.CTkProgressBar(
            prog_frame,
            height=8,
            corner_radius=4,
            fg_color=("#E2E8F0", "#334155"),
            progress_color=("#2563EB", "#3B82F6")
        )
        self.batch_progress_bar.set(0.0)
        self.batch_progress_bar.grid(row=1, column=0, sticky="ew")

        # Action Buttons on Right
        btn_box = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_box.grid(row=0, column=1, padx=(0, 18), pady=12, sticky="e")

        self.open_dest_btn = ctk.CTkButton(
            btn_box,
            text="📂 Open Folder",
            width=120,
            height=38,
            corner_radius=8,
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#475569"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._open_output_folder
        )
        self.open_dest_btn.pack(side="left", padx=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            btn_box,
            text="Stop",
            width=90,
            height=38,
            corner_radius=8,
            fg_color=("#EF4444", "#DC2626"),
            hover_color=("#DC2626", "#B91C1C"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            state="disabled",
            command=self.cancel_conversion
        )
        self.cancel_btn.pack(side="left", padx=(0, 8))

        self.convert_btn = ctk.CTkButton(
            btn_box,
            text="▶ Start Conversion",
            width=160,
            height=38,
            corner_radius=8,
            fg_color=("#2563EB", "#3B82F6"),
            hover_color=("#1D4ED8", "#2563EB"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.start_conversion
        )
        self.convert_btn.pack(side="left")

    def _check_dependencies(self):
        ffmpeg, ffprobe = FFmpegFinder.get_paths()
        if not ffmpeg or not ffprobe:
            self.batch_status_label.configure(
                text="⚠️ Warning: FFmpeg binaries not detected!",
                text_color=("#DC2626", "#EF4444")
            )

    def _toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def add_files(self, paths: List[str]):
        """Inspects and adds valid media files to the queue."""
        added_count = 0
        current_summary = self.settings_view.get_summary_string()

        for p in paths:
            if not os.path.isfile(p):
                continue
            # Avoid duplicate paths in queue
            if any(item.media_info.file_path == p for item in self.queue_items.values()):
                continue

            info = MediaProbe.probe(p)
            if not info:
                continue

            item_id = str(uuid.uuid4())
            card = QueueItemCard(
                master=self.queue_scroll,
                item_id=item_id,
                media_info=info,
                target_summary=current_summary,
                on_remove=self.remove_item
            )
            card.pack(fill="x", pady=4, padx=4)

            self.queue_items[item_id] = QueuedFile(item_id, info, card)
            added_count += 1

        if self.queue_items:
            self.empty_label.pack_forget()

        self._update_queue_counts()

    def remove_item(self, item_id: str):
        if item_id in self.queue_items:
            self.queue_items[item_id].card_widget.destroy()
            del self.queue_items[item_id]

        if not self.queue_items:
            self.empty_label.pack(pady=60)

        self._update_queue_counts()

    def clear_all_queue(self):
        if self.is_converting:
            return
        for item in list(self.queue_items.values()):
            item.card_widget.destroy()
        self.queue_items.clear()
        self.empty_label.pack(pady=60)
        self._update_queue_counts()

    def clear_completed_queue(self):
        if self.is_converting:
            return
        to_del = [iid for iid, q in self.queue_items.items() if q.status == "done"]
        for iid in to_del:
            self.remove_item(iid)

    def _on_settings_changed(self):
        summary = self.settings_view.get_summary_string()
        for item in self.queue_items.values():
            if item.status in ["ready", "error", "cancelled"]:
                item.card_widget.update_target(summary)

    def _update_queue_counts(self):
        total = len(self.queue_items)
        done = sum(1 for q in self.queue_items.values() if q.status == "done")
        self.queue_title.configure(text=f"Conversion Queue ({total} file{'s' if total != 1 else ''})")
        self.batch_counter_label.configure(text=f"{done} / {total} completed")
        if total > 0:
            self.batch_progress_bar.set(done / total)
        else:
            self.batch_progress_bar.set(0.0)

    def start_conversion(self):
        if self.is_converting:
            return

        pending = [q for q in self.queue_items.values() if q.status in ["ready", "error", "cancelled"]]
        if not pending:
            self.batch_status_label.configure(
                text="No pending files in queue to convert.",
                text_color=("#F59E0B", "#FBBF24")
            )
            return

        self.is_converting = True
        self.convert_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.clear_all_btn.configure(state="disabled")
        self.clear_done_btn.configure(state="disabled")

        settings = self.settings_view.get_settings()
        self.worker_thread = threading.Thread(
            target=self._process_queue_worker,
            args=(settings,),
            daemon=True
        )
        self.worker_thread.start()

    def cancel_conversion(self):
        if not self.is_converting:
            return
        self.batch_status_label.configure(text="Cancelling conversion...", text_color=("#EF4444", "#F87171"))
        self.engine.cancel()

    def _poll_event_queue(self):
        try:
            while True:
                msg = self.event_queue.get_nowait()
                ev_type = msg[0]
                if ev_type == "progress":
                    self._handle_progress_update(msg[1])
                elif ev_type == "batch_status":
                    text, color = msg[1], msg[2]
                    self.batch_status_label.configure(text=text, text_color=color)
                elif ev_type == "item_status":
                    item_id, status = msg[1], msg[2]
                    if item_id in self.queue_items:
                        self.queue_items[item_id].status = status
                    self._update_queue_counts()
                elif ev_type == "batch_finished":
                    self._on_batch_finished()
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error handling queue event: {e}")
        finally:
            self.after(30, self._poll_event_queue)

    def _process_queue_worker(self, settings: dict):
        out_dir = settings["output_dir"]
        os.makedirs(out_dir, exist_ok=True)

        items_to_convert = [q for q in self.queue_items.values() if q.status in ["ready", "error", "cancelled"]]
        total_count = len(items_to_convert)

        for idx, item in enumerate(items_to_convert, 1):
            if not self.is_converting:
                break

            self.event_queue.put(("item_status", item.item_id, "converting"))
            base_name = os.path.splitext(item.media_info.file_name)[0]
            out_filename = f"{base_name}_converted{settings['extension']}"
            out_path = os.path.join(out_dir, out_filename)

            # Ensure unique filename
            counter = 1
            while os.path.exists(out_path):
                out_path = os.path.join(out_dir, f"{base_name}_converted_{counter}{settings['extension']}")
                counter += 1

            item.output_path = out_path

            # Update batch status
            self.event_queue.put((
                "batch_status",
                f"Converting ({idx}/{total_count}): {item.media_info.file_name}",
                ("#2563EB", "#60A5FA")
            ))

            job = ConversionJob(
                job_id=item.item_id,
                input_path=item.media_info.file_path,
                output_path=out_path,
                target_format=settings["format"],
                vcodec=settings["vcodec"],
                acodec=settings["acodec"],
                resolution=settings["resolution"],
                quality=settings["quality"],
                fps=settings["fps"],
                audio_bitrate=settings["audio_bitrate"],
                hw_accel=settings["hw_accel"],
                duration_seconds=item.media_info.duration_seconds
            )

            def on_progress(update: ProgressUpdate):
                self.event_queue.put(("progress", update))

            success = self.engine.execute(job, on_progress)

            if success:
                self.event_queue.put(("item_status", item.item_id, "done"))
            else:
                if self.engine._is_cancelled:
                    self.event_queue.put(("item_status", item.item_id, "cancelled"))
                    break
                else:
                    self.event_queue.put(("item_status", item.item_id, "error"))

        # Batch finished
        self.event_queue.put(("batch_finished", None))

    def _handle_progress_update(self, update: ProgressUpdate):
        item = self.queue_items.get(update.job_id)
        if not item:
            return

        if update.is_finished:
            item.card_widget.set_completed()
        elif update.is_error:
            if "cancelled" in update.error_message.lower():
                item.card_widget.set_cancelled()
            else:
                item.card_widget.set_error(update.error_message)
        else:
            item.card_widget.set_converting(update.percentage, update.speed_str, update.eta_str)

    def _on_batch_finished(self):
        self.is_converting = False
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.clear_all_btn.configure(state="normal")
        self.clear_done_btn.configure(state="normal")

        done_count = sum(1 for q in self.queue_items.values() if q.status == "done")
        self.batch_status_label.configure(
            text=f"Batch complete: {done_count} files converted successfully!",
            text_color=("#16A34A", "#22C55E")
        )
        self._update_queue_counts()

        # Open destination folder if selected
        if self.settings_view.open_folder_var.get():
            self._open_output_folder()

    def _open_output_folder(self):
        folder = self.settings_view.dest_var.get()
        if os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception:
                pass
