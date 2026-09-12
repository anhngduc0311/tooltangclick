import re
import time
import random
from urllib.parse import urlparse

def extract_domain(url: str) -> str:
    """
    Trích xuất tên miền sạch từ URL.
    Ví dụ: https://www.example.com/blog/item-1 -> example.com
    """
    if not url:
        return ""
    url = url.strip().lower()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc or parsed.path.split('/')[0]
        # Bỏ port nếu có
        netloc = netloc.split(':')[0]
        # Bỏ tiền tố www.
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")

def domain_matches(target_domain: str, candidate_url: str) -> bool:
    """
    Kiểm tra xem candidate_url có thuộc target_domain hay không.
    Ví dụ: target_domain = 'shopee.vn', candidate_url = 'https://shopee.vn/product/123' -> True
    """
    clean_target = extract_domain(target_domain)
    clean_candidate = extract_domain(candidate_url)
    
    if not clean_target or not clean_candidate:
        return False
        
    return clean_target == clean_candidate or clean_candidate.endswith("." + clean_target)

def clean_keyword(keyword: str) -> str:
    """Chuẩn hóa từ khóa tìm kiếm"""
    return re.sub(r'\s+', ' ', keyword.strip())

def human_sleep(min_sec: float, max_sec: float, stop_event=None) -> bool:
    """
    Nghỉ ngẫu nhiên theo khoảng thời gian giả lập người thật.
    Có kiểm tra stop_event để dừng ngay lập tức khi người dùng bấm Dừng.
    Trả về False nếu bị stop_event ngắt quãng.
    """
    if min_sec > max_sec:
        min_sec, max_sec = max_sec, min_sec
    duration = random.uniform(min_sec, max_sec)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        if stop_event and stop_event.is_set():
            return False
        time.sleep(0.2)
    return True

def format_duration(seconds: float) -> str:
    """Chuyển đổi giây thành chuỗi mm:ss hoặc hh:mm:ss"""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
