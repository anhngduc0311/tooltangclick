import time
import random
from typing import Tuple, Dict, Any
from core.browser_engine import BrowserSession
from utils.helpers import extract_domain, domain_matches, human_sleep
from utils.logger import logger

def handle_google_consent(page):
    """Xử lý popup chấp nhận điều khoản cookie của Google nếu có"""
    try:
        consent_selectors = [
            "#L2AGLb",
            "tag:button@@text()=Accept all",
            "tag:button@@text()=Tôi đồng ý",
            "tag:button@@text()=I agree",
            "tag:button@@text()=Agree",
            "tag:div@@text()=Accept all",
            "tag:button@@aria-label=Accept all"
        ]
        for sel in consent_selectors:
            btn = page.ele(sel)
            if btn:
                btn.click()
                time.sleep(1.5)
                break
    except Exception:
        pass

def run_seo_bot_task(
    session: BrowserSession,
    keyword: str,
    target_domain: str,
    max_search_pages: int = 5,
    dwell_time_range: Tuple[int, int] = (40, 80),
    internal_pages_count: int = 2,
    fallback_direct: bool = False,
    google_domain: str = "https://www.google.com",
    stop_event = None
) -> Dict[str, Any]:
    """
    Thực hiện quy trình SEO CTR:
    1. Vào Google, gõ từ khóa tự nhiên
    2. Quét kết quả từng trang để tìm target_domain
    3. Click vào kết quả và duyệt website để tăng dwell time & pageviews
    """
    clean_target = extract_domain(target_domain)
    worker_id = session.worker_id
    result_data = {
        "success": False,
        "found": False,
        "rank": None,
        "page": None,
        "keyword": keyword,
        "message": ""
    }

    try:
        logger.info(f"[{worker_id}] Bắt đầu phiên SEO cho từ khóa: '{keyword}' (Mục tiêu: {clean_target})", worker_id)
        page = session.start()

        if stop_event and stop_event.is_set():
            return result_data

        # 1. Truy cập trang chủ Google
        logger.info(f"[{worker_id}] Đang mở Google ({google_domain})...", worker_id)
        page.get(google_domain)
        page.wait.load_start()
        handle_google_consent(page)
        human_sleep(1.0, 2.5, stop_event)

        # 2. Tìm ô tìm kiếm
        search_box = page.ele("tag:textarea@@name=q") or page.ele("tag:input@@name=q")
        if not search_box:
            # Kiểm tra xem có bị captcha không
            if "sorry" in page.url or page.ele("tag:form@@action=CaptchaRedirect"):
                logger.warning(f"[{worker_id}] Google yêu cầu xác minh Captcha. Vui lòng đổi Proxy!", worker_id)
                result_data["message"] = "Bị Google Captcha"
                return result_data
            raise Exception("Không tìm thấy ô nhập tìm kiếm trên Google")

        # 3. Gõ từ khóa tự nhiên
        logger.info(f"[{worker_id}] Đang gõ từ khóa: '{keyword}'...", worker_id)
        try:
            search_box.click()
            human_sleep(0.3, 0.7, stop_event)
        except Exception:
            pass
        search_box.clear()
        session.human_type(search_box, keyword, stop_event)
        human_sleep(0.5, 1.5, stop_event)

        # 4. Gửi tìm kiếm (nhấn Enter)
        search_box.input("\n")
        page.wait.load_start()
        human_sleep(2.0, 3.5, stop_event)

        # Kiểm tra nếu bị redirect sorry
        if "sorry" in page.url:
            logger.warning(f"[{worker_id}] Google phát hiện IP truy cập dày đặc. Nên thêm danh sách Proxy sạch!", worker_id)
            if fallback_direct:
                logger.info(f"[{worker_id}] Kích hoạt chế độ dự phòng: Truy cập trực tiếp {target_domain}...", worker_id)
                target_url = target_domain if target_domain.startswith("http") else f"https://{target_domain}"
                page.get(target_url)
                page.wait.load_start()
                dwell_seconds = random.uniform(dwell_time_range[0], dwell_time_range[1])
                logger.info(f"[{worker_id}] Đang lướt đọc trang mục tiêu trong {int(dwell_seconds)} giây...", worker_id)
                session.human_scroll(dwell_seconds, stop_event)
                if internal_pages_count > 0 and not (stop_event and stop_event.is_set()):
                    session.browse_internal_pages(
                        clean_target,
                        max_pages=internal_pages_count,
                        dwell_time_per_page=random.uniform(10, 20),
                        stop_event=stop_event
                    )
                result_data["success"] = True
                result_data["message"] = "Đã hoàn thành qua Direct Fallback"
                logger.success(f"[{worker_id}] Hoàn thành phiên duyệt qua Fallback.", worker_id)
                return result_data
            else:
                result_data["message"] = "Google chặn IP (Sorry page)"
                return result_data

        # 5. Lặp qua từng trang kết quả tìm kiếm
        current_page_num = 1
        overall_rank = 0
        found_element = None

        while current_page_num <= max_search_pages:
            if stop_event and stop_event.is_set():
                break

            logger.info(f"[{worker_id}] Đang quét kết quả Google Trang {current_page_num}/{max_search_pages}...", worker_id)
            
            # Cuộn nhẹ xuống để các kết quả tải đầy đủ
            page.run_js("window.scrollBy({top: 400, behavior: 'smooth'});")
            human_sleep(1.0, 2.0, stop_event)

            # Lấy tất cả các tiêu đề h3 trên trang kết quả
            h3_elements = page.eles("tag:h3")
            for h3 in h3_elements:
                if stop_event and stop_event.is_set():
                    break

                try:
                    # Thẻ link bao quanh h3 hoặc thẻ cha gần nhất
                    a_tag = h3.parent("tag:a")
                    if not a_tag:
                        continue

                    overall_rank += 1

                    # Kiểm tra domain mục tiêu có nằm trong link, thẻ cite, hoặc nội dung block kết quả
                    container = a_tag.parent()
                    container_text = container.text.lower() if container else ""
                    href = (a_tag.attr("href") or "").lower()

                    is_match = (
                        clean_target in container_text or
                        clean_target in href or
                        domain_matches(clean_target, href)
                    )

                    if is_match:
                        found_element = a_tag
                        result_data["found"] = True
                        result_data["rank"] = overall_rank
                        result_data["page"] = current_page_num
                        logger.success(
                            f"[{worker_id}] ĐÃ TÌM THẤY '{clean_target}' tại Trang {current_page_num}, Top #{overall_rank}!",
                            worker_id
                        )
                        break
                except Exception:
                    continue

            if found_element:
                break

            # Nếu chưa tìm thấy ở trang hiện tại, thử chuyển sang trang kế tiếp
            if current_page_num < max_search_pages:
                logger.info(f"[{worker_id}] Chưa thấy ở trang {current_page_num}, chuyển sang trang kế tiếp...", worker_id)
                # Cuộn xuống cuối trang
                page.run_js("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                human_sleep(1.5, 3.0, stop_event)

                next_btn = (
                    page.ele("#pnnext") or
                    page.ele(f"tag:a@@aria-label=Trang {current_page_num + 1}") or
                    page.ele(f"tag:a@@aria-label=Page {current_page_num + 1}") or
                    page.ele("tag:span@@text()=Xem thêm kết quả") or
                    page.ele("tag:span@@text()=More results")
                )

                if next_btn:
                    try:
                        next_btn.click()
                        page.wait.load_start()
                        current_page_num += 1
                        human_sleep(2.0, 4.0, stop_event)
                    except Exception as e:
                        logger.warning(f"[{worker_id}] Không thể bấm nút trang tiếp: {e}", worker_id)
                        break
                else:
                    logger.info(f"[{worker_id}] Không tìm thấy nút trang tiếp hoặc đã hết kết quả.", worker_id)
                    break
            else:
                break

        # 6. Xử lý sau khi tìm thấy (Click & Dwell)
        if found_element:
            # Cuộn mượt đến vị trí phần tử
            try:
                page.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", found_element)
                human_sleep(1.5, 3.0, stop_event)
                logger.info(f"[{worker_id}] Đang click vào liên kết mục tiêu...", worker_id)
                found_element.click()
            except Exception:
                page.run_js("arguments[0].click();", found_element)

            page.wait.load_start()
            human_sleep(2.0, 4.0, stop_event)

            # Nếu mở sang tab mới, chuyển điều khiển sang tab đó
            if len(page.tabs) > 1:
                page = page.get_tab(page.tabs[-1])
                session.page = page

            # Thời gian lưu lại trên trang (Dwell time)
            dwell_seconds = random.uniform(dwell_time_range[0], dwell_time_range[1])
            logger.info(f"[{worker_id}] Đang lướt đọc trang mục tiêu trong {int(dwell_seconds)} giây...", worker_id)
            session.human_scroll(dwell_seconds, stop_event)

            # Lướt thêm các trang con
            if internal_pages_count > 0 and not (stop_event and stop_event.is_set()):
                session.browse_internal_pages(
                    clean_target,
                    max_pages=internal_pages_count,
                    dwell_time_per_page=random.uniform(10, 20),
                    stop_event=stop_event
                )

            result_data["success"] = True
            result_data["message"] = f"Thành công! Top #{overall_rank} (Trang {result_data['page']})"
            logger.success(f"[{worker_id}] Hoàn thành phiên SEO CTR cho '{keyword}'.", worker_id)

        else:
            # Không tìm thấy trong số trang cho phép
            logger.warning(
                f"[{worker_id}] Không tìm thấy '{clean_target}' trong {max_search_pages} trang đầu cho từ khóa '{keyword}'.",
                worker_id
            )
            if fallback_direct:
                logger.info(f"[{worker_id}] Chuyển sang chế độ dự phòng: Truy cập trực tiếp {target_domain}...", worker_id)
                target_url = target_domain if target_domain.startswith("http") else f"https://{target_domain}"
                page.get(target_url)
                page.wait.load_start()
                dwell_seconds = random.uniform(dwell_time_range[0], dwell_time_range[1])
                session.human_scroll(dwell_seconds, stop_event)
                result_data["success"] = True
                result_data["message"] = f"Hoàn thành qua Direct Fallback (Không thấy trong Top {max_search_pages} trang)"
            else:
                result_data["message"] = f"Không nằm trong Top {max_search_pages} trang Google"

    except Exception as e:
        logger.error(f"[{worker_id}] Lỗi trong quá trình chạy SEO Bot: {e}", worker_id)
        result_data["message"] = str(e)
    finally:
        session.close()

    return result_data
