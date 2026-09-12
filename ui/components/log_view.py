import queue
import customtkinter as ctk
from typing import Dict
from ui.theme import THEME, FONTS

class LogView(ctk.CTkFrame):
    """
    Widget hiển thị nhật ký chạy với màu sắc phân loại, thread-safe, tự động cuộn.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border_color"], **kwargs)

        self._queue = queue.Queue()
        self.auto_scroll = True

        self._setup_ui()
        self._configure_tags()
        self._check_queue()

    def _setup_ui(self):
        # Header bar của log
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 6))

        title = ctk.CTkLabel(
            header_frame,
            text="NHẬT KÝ HOẠT ĐỘNG (LIVE LOGS)",
            font=FONTS["subtitle"],
            text_color=THEME["text_primary"]
        )
        title.pack(side="left")

        # Nút xóa log
        btn_clear = ctk.CTkButton(
            header_frame,
            text="Xóa log",
            width=70,
            height=26,
            font=FONTS["small"],
            fg_color=THEME["border_color"],
            hover_color="#475569",
            command=self.clear_logs
        )
        btn_clear.pack(side="right")

        # Checkbox tự cuộn
        self.chk_autoscroll = ctk.CTkCheckBox(
            header_frame,
            text="Tự động cuộn",
            font=FONTS["small"],
            text_color=THEME["text_muted"],
            checkbox_width=18,
            checkbox_height=18,
            command=self._toggle_autoscroll
        )
        self.chk_autoscroll.select()
        self.chk_autoscroll.pack(side="right", padx=10)

        # Khung Textbox chứa log
        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=THEME["bg_input"],
            font=FONTS["code"],
            wrap="word",
            border_width=1,
            border_color=THEME["border_color"]
        )
        self.textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _configure_tags(self):
        """Định dạng màu sắc cho từng loại log"""
        self.textbox.tag_config("TIME", foreground="#64748b")
        self.textbox.tag_config("THREAD", foreground="#38bdf8")
        self.textbox.tag_config("INFO", foreground=THEME["log_info"])
        self.textbox.tag_config("SUCCESS", foreground=THEME["log_success"])
        self.textbox.tag_config("WARNING", foreground=THEME["log_warning"])
        self.textbox.tag_config("ERROR", foreground=THEME["log_error"])

    def add_log_entry(self, entry: Dict):
        """Được gọi từ logger callback (thread-safe đưa vào queue)"""
        self._queue.put(entry)

    def _check_queue(self):
        """Hút log từ queue và render lên Textbox (chạy trên luồng UI chính)"""
        try:
            while not self._queue.empty():
                entry = self._queue.get_nowait()
                self._insert_entry(entry)
        except Exception:
            pass
        finally:
            self.after(100, self._check_queue)

    def _insert_entry(self, entry: Dict):
        time_str = f"[{entry['timestamp']}] "
        thread_str = f"[{entry['thread']}] " if entry.get("thread") else ""
        level_str = f"[{entry['level']}] "
        msg_str = f"{entry['message']}\n"

        self.textbox.insert("end", time_str, "TIME")
        if thread_str:
            self.textbox.insert("end", thread_str, "THREAD")
        self.textbox.insert("end", level_str, entry["level"])
        self.textbox.insert("end", msg_str, entry["level"])

        if self.auto_scroll:
            self.textbox.see("end")

    def _toggle_autoscroll(self):
        self.auto_scroll = bool(self.chk_autoscroll.get())

    def clear_logs(self):
        self.textbox.delete("1.0", "end")
