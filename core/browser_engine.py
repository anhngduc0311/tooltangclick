import os
import time
import random
import shutil
import tempfile
from typing import Optional, List
from DrissionPage import ChromiumPage, ChromiumOptions
from core.proxy_manager import ProxyItem, ProxyManager
from core.user_agents import get_random_profile
from utils.helpers import domain_matches, human_sleep
from utils.logger import logger

import socket

def find_free_port() -> int:
    """Tìm một cổng TCP khả dụng trên localhost"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class BrowserSession:
    def __init__(
        self,
        headless: bool = False,
        proxy: Optional[ProxyItem] = None,
        proxy_manager: Optional[ProxyManager] = None,
        device_mode: str = "desktop",
        worker_id: str = "Worker-1"
    ):
        self.worker_id = worker_id
        self.headless = headless
        self.proxy = proxy
        self.proxy_manager = proxy_manager
        self.device_mode = device_mode
        self.page: Optional[ChromiumPage] = None
        self._temp_profile_dir: Optional[str] = None
        self._ext_dir: Optional[str] = None

    def start(self) -> ChromiumPage:
        """Khởi tạo trình duyệt Chromium với đầy đủ cấu hình chống bot và proxy"""
        co = ChromiumOptions()
        # Cấp phát cổng CDP riêng cho từng luồng
        port = find_free_port()
        co.set_local_port(port)

        # Tạo thư mục profile tạm thời độc lập cho luồng này
        self._temp_profile_dir = tempfile.mkdtemp(prefix=f"dp_profile_{self.worker_id}_")
        co.set_user_data_path(self._temp_profile_dir)

        # Chế độ ẩn/hiện cửa sổ
        if self.headless:
            co.set_argument("--headless=new")
        else:
            co.headless(False)

        # Cấu hình User-Agent và kích thước màn hình
        ua, width, height = get_random_profile(self.device_mode)
        co.set_user_agent(ua)
        co.set_argument(f"--window-size={width},{height}")

        # Tối ưu hóa hiệu năng và cờ chống phát hiện
        co.set_argument("--no-first-run")
        co.set_argument("--no-default-browser-check")
        co.set_argument("--mute-audio")
        co.set_argument("--disable-notifications")
        co.set_argument("--disable-popup-blocking")
        co.set_argument("--disable-blink-features=AutomationControlled")
        co.set_argument("--disable-infobars")
        co.set_argument("--lang=vi-VN,vi,en-US,en")

        # Cấu hình Proxy
        if self.proxy:
            if self.proxy.has_auth and self.proxy_manager:
                # Tạo extension giải quyết xác thực proxy tài khoản/mật khẩu
                self._ext_dir = self.proxy_manager.create_proxy_auth_extension(self.proxy)
                if self._ext_dir:
                    co.add_extension(self._ext_dir)
            else:
                co.set_proxy(self.proxy.to_standard_url())

        self.page = ChromiumPage(co)
        return self.page

    def human_type(self, element, text: str, stop_event=None):
        """Gõ phím với nhịp điệu ngẫu nhiên như người dùng thật"""
        for char in text:
            if stop_event and stop_event.is_set():
                break
            element.input(char)
            time.sleep(random.uniform(0.04, 0.16))

    def human_scroll(self, duration_sec: float, stop_event=None):
        """Cuộn trang mượt mà mô phỏng hành vi đọc bài viết của người thật"""
        if not self.page:
            return
        
        start_time = time.time()
        while time.time() - start_time < duration_sec:
            if stop_event and stop_event.is_set():
                break
                
            # Xác suất 80% cuộn xuống, 20% cuộn ngược nhẹ lên
            if random.random() < 0.8:
                scroll_amount = random.randint(150, 450)
                try:
                    self.page.run_js(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}});")
                except Exception:
                    pass
            else:
                scroll_amount = -random.randint(80, 200)
                try:
                    self.page.run_js(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}});")
                except Exception:
                    pass

            # Nghỉ ngơi dừng lại đọc 1 - 3.5 giây
            if not human_sleep(1.0, 3.5, stop_event):
                break

    def browse_internal_pages(self, target_domain: str, max_pages: int = 2, dwell_time_per_page: float = 15.0, stop_event=None):
        """Tự động tìm kiếm và nhấp vào các liên kết nội bộ để tăng Pageviews và giảm Bounce Rate"""
        if not self.page or max_pages <= 0:
            return

        for i in range(max_pages):
            if stop_event and stop_event.is_set():
                break

            try:
                links = self.page.eles("tag:a")
                valid_links = []
                for link in links:
                    href = link.link
                    if href and href.startswith("http") and domain_matches(target_domain, href):
                        # Bỏ qua các liên kết neo # hoặc link tải file
                        if "#" not in href and not any(href.lower().endswith(ext) for ext in ['.pdf', '.zip', '.rar', '.jpg', '.png']):
                            valid_links.append(link)

                if not valid_links:
                    break

                target_link = random.choice(valid_links[:15])  # Chọn ngẫu nhiên trong 15 link đầu
                logger.info(f"[{self.worker_id}] Duyệt trang con {i+1}/{max_pages}: {target_link.link[:50]}...", self.worker_id)
                
                # Cuộn đến phần tử link trước khi bấm
                try:
                    self.page.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target_link)
                    human_sleep(1.0, 2.0, stop_event)
                    target_link.click()
                except Exception:
                    # Nếu click element bị che, dùng JavaScript click
                    self.page.run_js("arguments[0].click();", target_link)

                self.page.wait.load_start()
                # Cuộn đọc trên trang con
                self.human_scroll(dwell_time_per_page, stop_event)
            except Exception as e:
                logger.warning(f"[{self.worker_id}] Không thể duyệt tiếp trang con: {e}", self.worker_id)
                break

    def close(self):
        """Đóng an toàn trình duyệt và dọn dẹp các thư mục profile/extension rác"""
        try:
            if self.page:
                self.page.quit()
        except Exception:
            pass
        finally:
            self.page = None

        # Dọn dẹp thư mục profile tạm thời
        if self._temp_profile_dir and os.path.exists(self._temp_profile_dir):
            try:
                shutil.rmtree(self._temp_profile_dir, ignore_errors=True)
            except Exception:
                pass

        # Dọn dẹp extension proxy tạm thời
        if self._ext_dir and os.path.exists(self._ext_dir):
            try:
                shutil.rmtree(self._ext_dir, ignore_errors=True)
            except Exception:
                pass
