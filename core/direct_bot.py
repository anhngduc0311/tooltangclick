import time
import random
from typing import Tuple, Dict, Any, Optional
from core.browser_engine import BrowserSession
from utils.helpers import extract_domain, human_sleep
from utils.logger import logger

REFERRAL_SOURCES = {
    "Facebook": "https://www.facebook.com/",
    "X (Twitter)": "https://t.co/",
    "YouTube": "https://www.youtube.com/",
    "Reddit": "https://www.reddit.com/",
    "Direct": None
}

def run_direct_bot_task(
    session: BrowserSession,
    target_url: str,
    referral_source: Optional[str] = None,
    dwell_time_range: Tuple[int, int] = (40, 80),
    internal_pages_count: int = 2,
    stop_event = None
) -> Dict[str, Any]:
    """
    Thực hiện truy cập trực tiếp (Direct) hoặc có nguồn giới thiệu (Referral):
    1. Mở trang mục tiêu (với Referer tùy chọn)
    2. Cuộn trang mượt mà tăng thời gian xem (Dwell Time)
    3. Duyệt thêm các liên kết nội bộ
    """
    clean_target = extract_domain(target_url)
    worker_id = session.worker_id
    result_data = {
        "success": False,
        "keyword": "Direct/Referral",
        "rank": "-",
        "page": "-",
        "message": ""
    }

    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    try:
        ref_text = f" từ {referral_source}" if referral_source and referral_source != "Direct" else ""
        logger.info(f"Bắt đầu truy cập{ref_text} vào: {target_url}", worker_id)
        page = session.start()

        if stop_event and stop_event.is_set():
            return result_data

        # Nếu có referral source, thiết lập referer qua CDP hoặc JS navigation
        ref_url = REFERRAL_SOURCES.get(referral_source) if referral_source else None
        if ref_url:
            try:
                # Giả lập truy cập từ trang nguồn hoặc dùng CDP Network
                page.run_cdp("Network.setExtraHTTPHeaders", headers={"Referer": ref_url})
            except Exception:
                pass

        page.get(target_url)
        human_sleep(1.5, 3.0, stop_event)

        dwell_seconds = random.uniform(dwell_time_range[0], dwell_time_range[1])
        logger.info(f"Đang lướt đọc trang trong {int(dwell_seconds)} giây...", worker_id)
        session.human_scroll(dwell_seconds, stop_event)

        if internal_pages_count > 0 and not (stop_event and stop_event.is_set()):
            session.browse_internal_pages(
                clean_target,
                max_pages=internal_pages_count,
                dwell_time_per_page=random.uniform(10, 20),
                stop_event=stop_event
            )

        result_data["success"] = True
        result_data["message"] = f"Hoàn thành truy cập{ref_text}"
        logger.success("Hoàn thành phiên truy cập trực tiếp.", worker_id)

    except Exception as e:
        logger.error(f"Lỗi truy cập trực tiếp: {e}", worker_id)
        result_data["message"] = str(e)
    finally:
        session.close()

    return result_data
