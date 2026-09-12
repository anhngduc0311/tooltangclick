import time
import random
import threading
from typing import List, Dict, Callable, Optional
from core.browser_engine import BrowserSession
from core.proxy_manager import ProxyManager
from core.seo_bot import run_seo_bot_task
from core.direct_bot import run_direct_bot_task
from utils.logger import logger

class TaskManager:
    """
    Điều phối các luồng chạy nền, quản lý số lượt chạy, thống kê và cơ chế dừng an toàn.
    """
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.is_running = False
        self._stop_event = threading.Event()
        self._worker_threads: List[threading.Thread] = []
        self._stats_lock = threading.Lock()

        # Thống kê
        self.total_completed = 0
        self.success_count = 0
        self.failed_count = 0
        self.ranks_list: List[int] = []

        # Callbacks
        self._stats_callbacks: List[Callable[[Dict], None]] = []

    def register_stats_callback(self, cb: Callable[[Dict], None]):
        self._stats_callbacks.append(cb)

    def _notify_stats(self):
        with self._stats_lock:
            avg_rank = round(sum(self.ranks_list) / len(self.ranks_list), 1) if self.ranks_list else 0.0
            data = {
                "total": self.total_completed,
                "success": self.success_count,
                "failed": self.failed_count,
                "avg_rank": avg_rank,
                "is_running": self.is_running
            }
        for cb in self._stats_callbacks:
            try:
                cb(data)
            except Exception:
                pass

    def start(self, config: Dict):
        """Khởi chạy chiến dịch"""
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self.total_completed = 0
        self.success_count = 0
        self.failed_count = 0
        self.ranks_list.clear()
        self._worker_threads.clear()
        self._notify_stats()

        threads_count = max(1, min(config.get("threads_count", 1), 10))
        logger.info(f"Khởi động chiến dịch với {threads_count} luồng song song...", "Hệ thống")

        for i in range(threads_count):
            worker_id = f"Worker-{i+1}"
            t = threading.Thread(
                target=self._worker_loop,
                args=(worker_id, config),
                daemon=True
            )
            self._worker_threads.append(t)
            t.start()

    def stop(self):
        """Dừng tất cả các luồng worker"""
        if not self.is_running:
            return
        logger.info("Đang phát tín hiệu dừng tất cả các luồng...", "Hệ thống")
        self._stop_event.set()
        self.is_running = False
        self._notify_stats()

    def _worker_loop(self, worker_id: str, config: Dict):
        """Vòng lặp thực thi của từng worker độc lập"""
        keywords: List[str] = config.get("keywords", [])
        target_domain = config.get("target_domain", "")
        mode = config.get("mode", "SEO Google CTR")
        referral_source = config.get("referral_source", "Direct")
        total_target_runs = config.get("total_runs", 0)  # 0 nghĩa là chạy không giới hạn
        headless = config.get("headless", False)
        device_mode = config.get("device_mode", "desktop")
        dwell_min = config.get("dwell_min", 40)
        dwell_max = config.get("dwell_max", 80)
        max_search_pages = config.get("max_search_pages", 5)
        internal_pages = config.get("internal_pages", 2)
        fallback_direct = config.get("fallback_direct", True)
        google_domain = config.get("google_domain", "https://www.google.com")

        kw_index = random.randint(0, len(keywords) - 1) if keywords else 0

        while not self._stop_event.is_set():
            # Kiểm tra nếu đã đủ số lượt chạy mục tiêu
            with self._stats_lock:
                if 0 < total_target_runs <= self.total_completed:
                    logger.info(f"[{worker_id}] Đã đạt mục tiêu {total_target_runs} lượt chạy.", worker_id)
                    break

            # Lấy proxy cho phiên này
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                logger.info(f"[{worker_id}] Sử dụng Proxy: {proxy.host}:{proxy.port}", worker_id)
            else:
                has_proxy_cfg = bool(config.get("proxy_api_url") or config.get("proxies"))
                if has_proxy_cfg:
                    logger.warning(f"[{worker_id}] Chưa lấy được Proxy, đang chờ để lấy IP mới...", worker_id)
                    time.sleep(5)
                    proxy = self.proxy_manager.get_proxy()
                    if not proxy:
                        logger.error(f"[{worker_id}] Chưa có Proxy khả dụng! Tạm nghỉ 10s để tránh làm lộ IP mạng nhà.", worker_id)
                        time.sleep(10)
                        continue

            session = BrowserSession(
                headless=headless,
                proxy=proxy,
                proxy_manager=self.proxy_manager,
                device_mode=device_mode,
                worker_id=worker_id
            )

            res = None
            if mode == "SEO Google CTR" and keywords:
                # Chọn từ khóa luân phiên
                keyword = keywords[kw_index % len(keywords)]
                kw_index += 1

                res = run_seo_bot_task(
                    session=session,
                    keyword=keyword,
                    target_domain=target_domain,
                    max_search_pages=max_search_pages,
                    dwell_time_range=(dwell_min, dwell_max),
                    internal_pages_count=internal_pages,
                    fallback_direct=fallback_direct,
                    google_domain=google_domain,
                    stop_event=self._stop_event
                )
            else:
                # Chế độ Direct hoặc Referral
                res = run_direct_bot_task(
                    session=session,
                    target_url=target_domain,
                    referral_source=referral_source,
                    dwell_time_range=(dwell_min, dwell_max),
                    internal_pages_count=internal_pages,
                    stop_event=self._stop_event
                )

            # Cập nhật số liệu thống kê
            if not self._stop_event.is_set():
                with self._stats_lock:
                    self.total_completed += 1
                    if res and res.get("success"):
                        self.success_count += 1
                        if res.get("rank") is not None and isinstance(res.get("rank"), int):
                            self.ranks_list.append(res["rank"])
                    else:
                        self.failed_count += 1
                self._notify_stats()

            # Nghỉ ngơi giữa các phiên 3 - 8 giây
            if self._stop_event.is_set():
                break
            time.sleep(random.uniform(3.0, 8.0))

        logger.info(f"[{worker_id}] Luồng đã kết thúc an toàn.", worker_id)

        # Kiểm tra nếu tất cả luồng đã xong
        all_alive = any(t.is_alive() for t in self._worker_threads if t != threading.current_thread())
        if not all_alive:
            self.is_running = False
            self._notify_stats()
            logger.success("Chiến dịch đã hoàn tất toàn bộ!", "Hệ thống")
