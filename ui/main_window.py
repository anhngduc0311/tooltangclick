import os
import json
import threading
import customtkinter as ctk
from typing import Dict

from core.proxy_manager import ProxyManager
from core.task_manager import TaskManager
from ui.theme import THEME, FONTS
from ui.components.log_view import LogView
from utils.logger import logger
from utils.helpers import extract_domain

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Thiết lập giao diện tổng quan
        self.title("AutoTraffic & SEO CTR Master - Tăng Lượt Xem & Thứ Hạng Website")
        self.geometry("1160 x 800")
        self.minsize(980, 680)
        self.configure(fg_color=THEME["bg_main"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Khởi tạo các module lõi
        self.proxy_manager = ProxyManager()
        self.task_manager = TaskManager(self.proxy_manager)

        self._build_ui()
        self._load_config()

        # Đăng ký nhận log và thống kê
        logger.add_listener(self.log_view.add_log_entry)
        self.task_manager.register_stats_callback(self._on_stats_update)

        # Log lời chào ban đầu
        logger.info("Khởi động hệ thống AutoTraffic & SEO CTR Master thành công.", "Hệ thống")
        logger.info("Sẵn sàng khởi chạy chiến dịch tăng tương tác cho website.", "Hệ thống")

    def _build_ui(self):
        # 1. TOP HEADER BAR
        header = ctk.CTkFrame(self, fg_color=THEME["bg_card"], height=64, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=10)

        lbl_app_title = ctk.CTkLabel(
            title_box,
            text="🚀 AUTOTRAFFIC & SEO CTR MASTER",
            font=FONTS["title"],
            text_color=THEME["text_primary"]
        )
        lbl_app_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            title_box,
            text="Mô phỏng hành vi người dùng thật • Vượt rào cản bot • Tăng Click & Dwell Time",
            font=FONTS["small"],
            text_color=THEME["text_muted"]
        )
        lbl_sub.pack(anchor="w")

        # Trạng thái hệ thống (Badge)
        self.badge_status = ctk.CTkLabel(
            header,
            text="● SẴN SÀNG",
            font=FONTS["body_bold"],
            text_color=THEME["accent_success"],
            fg_color=THEME["bg_main"],
            corner_radius=8,
            padx=16,
            pady=6
        )
        self.badge_status.pack(side="right", padx=20)

        # 2. STATS CARDS BAR
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=16, pady=(12, 6))

        self.stat_cards = {}
        items = [
            ("total", "TỔNG LƯỢT CHẠY", "0", THEME["text_primary"]),
            ("success", "THÀNH CÔNG", "0", THEME["accent_success"]),
            ("failed", "THẤT BẠI", "0", THEME["accent_danger"]),
            ("rank", "THỨ HẠNG TB", "Top --", THEME["text_accent"])
        ]

        for key, label, default_val, text_col in items:
            card = ctk.CTkFrame(
                stats_frame,
                fg_color=THEME["bg_card"],
                corner_radius=8,
                border_width=1,
                border_color=THEME["border_color"]
            )
            card.pack(side="left", fill="both", expand=True, padx=4)

            lbl_title = ctk.CTkLabel(card, text=label, font=FONTS["stat_label"], text_color=THEME["text_muted"])
            lbl_title.pack(anchor="center", pady=(8, 0))

            lbl_val = ctk.CTkLabel(card, text=default_val, font=FONTS["stat_number"], text_color=text_col)
            lbl_val.pack(anchor="center", pady=(0, 8))

            self.stat_cards[key] = lbl_val

        # 3. MAIN WORKSPACE (Chia trái / phải)
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.pack(fill="both", expand=True, padx=16, pady=8)

        # Panel Trái: Cấu hình Tabs (Rộng 530px)
        left_panel = ctk.CTkFrame(workspace, fg_color="transparent", width=530)
        left_panel.pack(side="left", fill="both", padx=(0, 8))
        left_panel.pack_propagate(False)

        # Panel Phải: Điều khiển & Log View
        right_panel = ctk.CTkFrame(workspace, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # --- XÂY DỰNG PANEL TRÁI (TABVIEW) ---
        self.tabview = ctk.CTkTabview(
            left_panel,
            fg_color=THEME["bg_card"],
            segmented_button_fg_color=THEME["bg_main"],
            segmented_button_selected_color=THEME["accent_primary"],
            border_width=1,
            border_color=THEME["border_color"],
            corner_radius=10
        )
        self.tabview.pack(fill="both", expand=True)

        tab_campaign = self.tabview.add("Chiến Dịch SEO")
        tab_proxy = self.tabview.add("Cấu Hình Proxy")
        tab_settings = self.tabview.add("Cài Đặt Nâng Cao")

        self._build_campaign_tab(tab_campaign)
        self._build_proxy_tab(tab_proxy)
        self._build_settings_tab(tab_settings)

        # --- XÂY DỰNG PANEL PHẢI (ACTION BUTTONS & LOGS) ---
        # Action Bar (Nút Bắt Đầu / Dừng)
        action_bar = ctk.CTkFrame(right_panel, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border_color"])
        action_bar.pack(fill="x", pady=(0, 10))

        self.btn_start = ctk.CTkButton(
            action_bar,
            text="▶  BẮT ĐẦU CHẠY",
            font=FONTS["body_bold"],
            fg_color=THEME["accent_success"],
            hover_color=THEME["accent_success_hover"],
            height=46,
            corner_radius=8,
            command=self._on_start_clicked
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=12, pady=12)

        self.btn_stop = ctk.CTkButton(
            action_bar,
            text="⏹  DỪNG LẠI",
            font=FONTS["body_bold"],
            fg_color=THEME["accent_danger"],
            hover_color=THEME["accent_danger_hover"],
            height=46,
            corner_radius=8,
            state="disabled",
            command=self._on_stop_clicked
        )
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(0, 12), pady=12)

        # Log View
        self.log_view = LogView(right_panel)
        self.log_view.pack(fill="both", expand=True)

    def _build_campaign_tab(self, parent):
        # 1. Domain mục tiêu
        lbl_domain = ctk.CTkLabel(parent, text="Website Mục Tiêu (URL hoặc Domain):", font=FONTS["body_bold"], text_color=THEME["text_primary"])
        lbl_domain.pack(anchor="w", padx=10, pady=(6, 2))

        self.entry_domain = ctk.CTkEntry(
            parent,
            placeholder_text="https://yourwebsite.com hoặc yourwebsite.com",
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border_color"],
            height=34
        )
        self.entry_domain.pack(fill="x", padx=10, pady=(0, 8))

        # 2. Chế độ chạy & Nguồn
        mode_row = ctk.CTkFrame(parent, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=(0, 8))

        lbl_mode = ctk.CTkLabel(mode_row, text="Chế độ:", font=FONTS["body_bold"], text_color=THEME["text_primary"])
        lbl_mode.pack(side="left", padx=(0, 8))

        self.combo_mode = ctk.CTkComboBox(
            mode_row,
            values=["SEO Google CTR", "Direct Visit", "Referral (Mạng Xã Hội)"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border_color"],
            width=200,
            command=self._on_mode_changed
        )
        self.combo_mode.pack(side="left")

        self.combo_referral = ctk.CTkComboBox(
            mode_row,
            values=["Facebook", "YouTube", "X (Twitter)", "Reddit"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border_color"],
            width=130
        )
        self.combo_referral.set("Facebook")

        # 3. Danh sách từ khóa
        lbl_kw = ctk.CTkLabel(parent, text="Danh Sách Từ Khóa SEO (Mỗi dòng 1 từ khóa):", font=FONTS["body_bold"], text_color=THEME["text_primary"])
        lbl_kw.pack(anchor="w", padx=10, pady=(4, 2))

        self.txt_keywords = ctk.CTkTextbox(
            parent,
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_color"],
            height=130
        )
        self.txt_keywords.pack(fill="x", padx=10, pady=(0, 8))

        # 4. Thời gian lưu lại trang (Dwell Time)
        dwell_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dwell_frame.pack(fill="x", padx=10, pady=(0, 8))

        lbl_dwell = ctk.CTkLabel(dwell_frame, text="Thời gian xem trang (giây):", font=FONTS["body"], text_color=THEME["text_muted"])
        lbl_dwell.pack(side="left")

        self.entry_dwell_min = ctk.CTkEntry(dwell_frame, width=55, height=28, fg_color=THEME["bg_input"], border_color=THEME["border_color"])
        self.entry_dwell_min.insert(0, "40")
        self.entry_dwell_min.pack(side="left", padx=4)

        lbl_dash = ctk.CTkLabel(dwell_frame, text="đến", font=FONTS["body"], text_color=THEME["text_muted"])
        lbl_dash.pack(side="left", padx=2)

        self.entry_dwell_max = ctk.CTkEntry(dwell_frame, width=55, height=28, fg_color=THEME["bg_input"], border_color=THEME["border_color"])
        self.entry_dwell_max.insert(0, "80")
        self.entry_dwell_max.pack(side="left", padx=4)

        # Duyệt trang con & Số trang Google
        opt_row = ctk.CTkFrame(parent, fg_color="transparent")
        opt_row.pack(fill="x", padx=10, pady=(0, 8))

        lbl_pages = ctk.CTkLabel(opt_row, text="Duyệt trang con:", font=FONTS["body"], text_color=THEME["text_muted"])
        lbl_pages.pack(side="left")

        self.entry_internal_pages = ctk.CTkEntry(opt_row, width=45, height=28, fg_color=THEME["bg_input"], border_color=THEME["border_color"])
        self.entry_internal_pages.insert(0, "2")
        self.entry_internal_pages.pack(side="left", padx=4)

        lbl_max_g = ctk.CTkLabel(opt_row, text="Quét tối đa:", font=FONTS["body"], text_color=THEME["text_muted"])
        lbl_max_g.pack(side="left", padx=(12, 0))

        self.entry_max_search_pages = ctk.CTkEntry(opt_row, width=45, height=28, fg_color=THEME["bg_input"], border_color=THEME["border_color"])
        self.entry_max_search_pages.insert(0, "5")
        self.entry_max_search_pages.pack(side="left", padx=4)

        lbl_g_unit = ctk.CTkLabel(opt_row, text="trang Google", font=FONTS["body"], text_color=THEME["text_muted"])
        lbl_g_unit.pack(side="left", padx=2)

        # Checkboxes
        chk_row = ctk.CTkFrame(parent, fg_color="transparent")
        chk_row.pack(fill="x", padx=10, pady=(4, 6))

        self.chk_headless = ctk.CTkCheckBox(
            chk_row,
            text="Ẩn trình duyệt (Headless)",
            font=FONTS["body"],
            text_color=THEME["text_primary"]
        )
        self.chk_headless.pack(side="left", padx=(0, 16))

        self.chk_fallback = ctk.CTkCheckBox(
            chk_row,
            text="Vào thẳng web nếu không thấy trên Google",
            font=FONTS["body"],
            text_color=THEME["text_primary"]
        )
        self.chk_fallback.select()
        self.chk_fallback.pack(side="left")

    def _build_proxy_tab(self, parent):
        # 1. Danh sách Proxy tĩnh
        lbl_p = ctk.CTkLabel(
            parent,
            text="Danh Sách Proxy Tĩnh (Mỗi dòng 1 proxy - ip:port hoặc ip:port:user:pass):",
            font=FONTS["body_bold"],
            text_color=THEME["text_primary"]
        )
        lbl_p.pack(anchor="w", padx=10, pady=(6, 2))

        self.txt_proxies = ctk.CTkTextbox(
            parent,
            font=FONTS["code"],
            fg_color=THEME["bg_input"],
            border_width=1,
            border_color=THEME["border_color"],
            height=120
        )
        self.txt_proxies.pack(fill="x", padx=10, pady=(0, 6))

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_test_proxy = ctk.CTkButton(
            btn_row,
            text="⚡ Test Proxy tĩnh",
            font=FONTS["small"],
            fg_color=THEME["border_color"],
            hover_color="#475569",
            width=130,
            command=self._on_test_proxy_clicked
        )
        self.btn_test_proxy.pack(side="left")

        self.lbl_proxy_test_res = ctk.CTkLabel(
            btn_row,
            text="",
            font=FONTS["small"],
            text_color=THEME["text_muted"]
        )
        self.lbl_proxy_test_res.pack(side="left", padx=10)

        # 2. API Xoay IP (Proxy.vn)
        lbl_api = ctk.CTkLabel(
            parent,
            text="Hoặc API Xoay IP (Proxy.vn / Proxyxoay.shop / TMProxy...):",
            font=FONTS["body_bold"],
            text_color=THEME["text_primary"]
        )
        lbl_api.pack(anchor="w", padx=10, pady=(6, 2))

        lbl_hint = ctk.CTkLabel(
            parent,
            text="Dán link get API hoặc chỉ cần dán Mã Key xoay của Proxy.vn:",
            font=FONTS["small"],
            text_color=THEME["text_muted"]
        )
        lbl_hint.pack(anchor="w", padx=10, pady=(0, 2))

        self.entry_proxy_api = ctk.CTkEntry(
            parent,
            placeholder_text="VD: https://proxyxoay.shop/api/get.php?key=KEY_XOAY (hoặc dán nguyên KEY)",
            font=FONTS["code"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border_color"],
            height=34
        )
        self.entry_proxy_api.pack(fill="x", padx=10, pady=(0, 6))

        btn_row_api = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row_api.pack(fill="x", padx=10, pady=(0, 6))

        self.btn_test_api = ctk.CTkButton(
            btn_row_api,
            text="🔄 Test API Xoay (Proxy.vn)",
            font=FONTS["small"],
            fg_color=THEME["accent_primary"],
            hover_color=THEME["accent_hover"],
            width=170,
            command=self._on_test_api_clicked
        )
        self.btn_test_api.pack(side="left")

        self.lbl_api_test_res = ctk.CTkLabel(
            btn_row_api,
            text="",
            font=FONTS["small"],
            text_color=THEME["text_muted"]
        )
        self.lbl_api_test_res.pack(side="left", padx=10)

    def _build_settings_tab(self, parent):
        # 1. Số luồng & Số lượt chạy
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(8, 8))

        lbl_threads = ctk.CTkLabel(row1, text="Số luồng chạy (Threads):", font=FONTS["body_bold"], text_color=THEME["text_primary"])
        lbl_threads.pack(side="left")

        self.entry_threads = ctk.CTkEntry(row1, width=50, height=28, fg_color=THEME["bg_input"], border_color=THEME["border_color"])
        self.entry_threads.insert(0, "1")
        self.entry_threads.pack(side="left", padx=8)

        lbl_runs = ctk.CTkLabel(row1, text="Tổng lượt chạy mục tiêu (0 = vô tận):", font=FONTS["body_bold"], text_color=THEME["text_primary"])
        lbl_runs.pack(side="left", padx=(20, 0))

        self.entry_total_runs = ctk.CTkEntry(row1, width=60, height=28, fg_color=THEME["bg_input"], border_color=THEME["border_color"])
        self.entry_total_runs.insert(0, "20")
        self.entry_total_runs.pack(side="left", padx=8)

        # 2. Giả lập thiết bị
        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 8))

        lbl_dev = ctk.CTkLabel(row2, text="Giả lập thiết bị:", font=FONTS["body_bold"], text_color=THEME["text_primary"])
        lbl_dev.pack(side="left")

        self.combo_device = ctk.CTkComboBox(
            row2,
            values=["Desktop (Máy tính)", "Mobile (Điện thoại)", "Ngẫu nhiên (Mixed)"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border_color"],
            width=190
        )
        self.combo_device.set("Desktop (Máy tính)")
        self.combo_device.pack(side="left", padx=8)

        # 3. Google domain
        row3 = ctk.CTkFrame(parent, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=(0, 12))

        lbl_g_dom = ctk.CTkLabel(row3, text="Tên miền Google:", font=FONTS["body_bold"], text_color=THEME["text_primary"])
        lbl_g_dom.pack(side="left")

        self.combo_google_domain = ctk.CTkComboBox(
            row3,
            values=["https://www.google.com", "https://www.google.com.vn"],
            font=FONTS["body"],
            fg_color=THEME["bg_input"],
            border_color=THEME["border_color"],
            width=220
        )
        self.combo_google_domain.set("https://www.google.com")
        self.combo_google_domain.pack(side="left", padx=8)

        # 4. Nút lưu cấu hình
        btn_save = ctk.CTkButton(
            parent,
            text="💾 Lưu Cấu Hình Hiện Tại",
            font=FONTS["body_bold"],
            fg_color=THEME["accent_primary"],
            hover_color=THEME["accent_hover"],
            height=36,
            command=self._save_config
        )
        btn_save.pack(anchor="w", padx=10, pady=10)

    def _on_mode_changed(self, choice):
        if "Referral" in choice:
            self.combo_referral.pack(side="left", padx=8)
        else:
            self.combo_referral.pack_forget()

    def _get_current_config(self) -> Dict:
        kw_text = self.txt_keywords.get("1.0", "end").strip()
        keywords = [k.strip() for k in kw_text.splitlines() if k.strip()]

        dev_val = self.combo_device.get()
        if "Mobile" in dev_val:
            dev_mode = "mobile"
        elif "Ngẫu nhiên" in dev_val:
            dev_mode = "mixed"
        else:
            dev_mode = "desktop"

        try:
            dwell_min = int(self.entry_dwell_min.get().strip() or "40")
            dwell_max = int(self.entry_dwell_max.get().strip() or "80")
            internal_pages = int(self.entry_internal_pages.get().strip() or "2")
            max_search_pages = int(self.entry_max_search_pages.get().strip() or "5")
            threads = int(self.entry_threads.get().strip() or "1")
            total_runs = int(self.entry_total_runs.get().strip() or "0")
        except ValueError:
            dwell_min, dwell_max, internal_pages, max_search_pages, threads, total_runs = 40, 80, 2, 5, 1, 0

        mode_choice = self.combo_mode.get()
        if "SEO" in mode_choice:
            mode = "SEO Google CTR"
        elif "Direct" in mode_choice:
            mode = "Direct Visit"
        else:
            mode = "Referral"

        return {
            "target_domain": self.entry_domain.get().strip(),
            "mode": mode,
            "referral_source": self.combo_referral.get(),
            "keywords": keywords,
            "dwell_min": dwell_min,
            "dwell_max": dwell_max,
            "internal_pages": internal_pages,
            "max_search_pages": max_search_pages,
            "threads_count": threads,
            "total_runs": total_runs,
            "headless": bool(self.chk_headless.get()),
            "device_mode": dev_mode,
            "fallback_direct": bool(self.chk_fallback.get()),
            "google_domain": self.combo_google_domain.get(),
            "proxies": self.txt_proxies.get("1.0", "end").strip(),
            "proxy_api_url": self.entry_proxy_api.get().strip()
        }

    def _save_config(self):
        cfg = self._get_current_config()
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            logger.success("Đã lưu cấu hình thành công vào config.json", "Hệ thống")
        except Exception as e:
            logger.error(f"Lỗi khi lưu cấu hình: {e}", "Hệ thống")

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            # Tạo cấu hình mẫu
            default_cfg = {
                "target_domain": "https://example.com",
                "mode": "SEO Google CTR",
                "referral_source": "Facebook",
                "keywords": ["dịch vụ seo uy tín", "thiết kế web chuyên nghiệp", "tin tức công nghệ mới"],
                "dwell_min": 40,
                "dwell_max": 80,
                "internal_pages": 2,
                "max_search_pages": 5,
                "threads_count": 1,
                "total_runs": 20,
                "headless": False,
                "device_mode": "desktop",
                "fallback_direct": True,
                "google_domain": "https://www.google.com",
                "proxies": "",
                "proxy_api_url": ""
            }
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(default_cfg, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            cfg = default_cfg
        else:
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                return

        # Nạp dữ liệu vào UI
        self.entry_domain.delete(0, "end")
        self.entry_domain.insert(0, cfg.get("target_domain", ""))

        mode = cfg.get("mode", "SEO Google CTR")
        if mode == "SEO Google CTR":
            self.combo_mode.set("SEO Google CTR")
        elif mode == "Direct Visit":
            self.combo_mode.set("Direct Visit")
        else:
            self.combo_mode.set("Referral (Mạng Xã Hội)")
        self._on_mode_changed(self.combo_mode.get())

        kws = cfg.get("keywords", [])
        if isinstance(kws, list):
            self.txt_keywords.delete("1.0", "end")
            self.txt_keywords.insert("1.0", "\n".join(kws))

        self.entry_dwell_min.delete(0, "end")
        self.entry_dwell_min.insert(0, str(cfg.get("dwell_min", 40)))

        self.entry_dwell_max.delete(0, "end")
        self.entry_dwell_max.insert(0, str(cfg.get("dwell_max", 80)))

        self.entry_internal_pages.delete(0, "end")
        self.entry_internal_pages.insert(0, str(cfg.get("internal_pages", 2)))

        self.entry_max_search_pages.delete(0, "end")
        self.entry_max_search_pages.insert(0, str(cfg.get("max_search_pages", 5)))

        self.entry_threads.delete(0, "end")
        self.entry_threads.insert(0, str(cfg.get("threads_count", 1)))

        self.entry_total_runs.delete(0, "end")
        self.entry_total_runs.insert(0, str(cfg.get("total_runs", 20)))

        if cfg.get("headless", False):
            self.chk_headless.select()
        else:
            self.chk_headless.deselect()

        if cfg.get("fallback_direct", True):
            self.chk_fallback.select()
        else:
            self.chk_fallback.deselect()

        dev_mode = cfg.get("device_mode", "desktop")
        if dev_mode == "mobile":
            self.combo_device.set("Mobile (Điện thoại)")
        elif dev_mode == "mixed":
            self.combo_device.set("Ngẫu nhiên (Mixed)")
        else:
            self.combo_device.set("Desktop (Máy tính)")

        if cfg.get("google_domain"):
            self.combo_google_domain.set(cfg.get("google_domain"))

        self.txt_proxies.delete("1.0", "end")
        self.txt_proxies.insert("1.0", cfg.get("proxies", ""))

        self.entry_proxy_api.delete(0, "end")
        self.entry_proxy_api.insert(0, cfg.get("proxy_api_url", ""))

    def _on_start_clicked(self):
        cfg = self._get_current_config()
        if not cfg["target_domain"]:
            logger.error("Vui lòng nhập Website mục tiêu trước khi bắt đầu!", "Hệ thống")
            return

        if cfg["mode"] == "SEO Google CTR" and not cfg["keywords"]:
            logger.error("Chế độ SEO CTR yêu cầu ít nhất 1 từ khóa!", "Hệ thống")
            return

        # Nạp proxy vào ProxyManager
        self.proxy_manager.set_proxies_from_text(cfg["proxies"])
        self.proxy_manager.set_api_url(cfg["proxy_api_url"])

        # Tự động lưu cấu hình
        self._save_config()

        # Cập nhật nút bấm
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.badge_status.configure(
            text="● ĐANG CHẠY",
            text_color=THEME["accent_warning"]
        )

        # Bắt đầu chạy
        self.task_manager.start(cfg)

    def _on_stop_clicked(self):
        self.task_manager.stop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.badge_status.configure(
            text="● ĐÃ DỪNG",
            text_color=THEME["accent_danger"]
        )

    def _on_stats_update(self, stats: Dict):
        """Cập nhật các thẻ số liệu thống kê (chạy an toàn trên luồng giao diện)"""
        def _update():
            self.stat_cards["total"].configure(text=str(stats["total"]))
            self.stat_cards["success"].configure(text=str(stats["success"]))
            self.stat_cards["failed"].configure(text=str(stats["failed"]))
            rank_txt = f"Top {stats['avg_rank']}" if stats["avg_rank"] > 0 else "Top --"
            self.stat_cards["rank"].configure(text=rank_txt)

            if not stats["is_running"]:
                self.btn_start.configure(state="normal")
                self.btn_stop.configure(state="disabled")
                self.badge_status.configure(
                    text="● SẴN SÀNG",
                    text_color=THEME["accent_success"]
                )

        self.after(0, _update)

    def _on_test_proxy_clicked(self):
        """Kiểm tra proxy đầu tiên trong danh sách"""
        lines = [l.strip() for l in self.txt_proxies.get("1.0", "end").splitlines() if l.strip()]
        if not lines:
            self.lbl_proxy_test_res.configure(text="Chưa có proxy nào để kiểm tra!", text_color=THEME["log_warning"])
            return

        target_proxy = lines[0]
        self.lbl_proxy_test_res.configure(text="Đang kết nối thử...", text_color=THEME["text_muted"])

        def _worker():
            res = ProxyManager.test_proxy(target_proxy)
            def _show():
                if res["success"]:
                    self.lbl_proxy_test_res.configure(
                        text=f"Hoạt động tốt! IP: {res['ip']} ({res['latency_ms']}ms)",
                        text_color=THEME["log_success"]
                    )
                else:
                    self.lbl_proxy_test_res.configure(
                        text=f"Lỗi: {res['error']}",
                        text_color=THEME["log_error"]
                    )
            self.after(0, _show)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_test_api_clicked(self):
        """Kiểm tra gọi API xoay IP Proxy.vn / Proxyxoay.shop"""
        api_input = self.entry_proxy_api.get().strip()
        if not api_input:
            self.lbl_api_test_res.configure(text="Vui lòng nhập Link API hoặc Key xoay Proxy.vn!", text_color=THEME["log_warning"])
            return

        self.lbl_api_test_res.configure(text="Đang gọi API kiểm tra...", text_color=THEME["text_muted"])

        def _worker():
            res = ProxyManager.test_api_xoay(api_input)
            def _show():
                if res["success"]:
                    self.lbl_api_test_res.configure(
                        text=f"Thành công! {res['detail']} ({res['latency_ms']}ms)",
                        text_color=THEME["log_success"]
                    )
                    logger.success(f"[Proxy.vn API] {res['detail']}", "Proxy")
                else:
                    self.lbl_api_test_res.configure(
                        text=f"Lỗi: {res['detail']}",
                        text_color=THEME["log_error"]
                    )
                    logger.error(f"[Proxy.vn API] {res['detail']}", "Proxy")
            self.after(0, _show)

        threading.Thread(target=_worker, daemon=True).start()
