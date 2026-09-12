import random
from typing import Tuple

DESKTOP_USER_AGENTS = [
    # Chrome on Windows 10/11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Edge on Windows 10/11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
]

MOBILE_USER_AGENTS = [
    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.134 Mobile Safari/537.36",
    # Safari on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
]

DESKTOP_RESOLUTIONS = [
    (1920, 1080),
    (1536, 864),
    (1440, 900),
    (1366, 768),
    (1600, 900),
    (1280, 720)
]

MOBILE_RESOLUTIONS = [
    (412, 915),  # Samsung Galaxy
    (393, 852),  # iPhone 14/15 Pro
    (390, 844),  # iPhone 12/13/14
    (360, 800)   # Android phổ thông
]

def get_random_profile(device_mode: str = "desktop") -> Tuple[str, int, int]:
    """
    Trả về bộ (user_agent, width, height) tùy theo chế độ:
    - 'desktop': chỉ máy tính
    - 'mobile': chỉ điện thoại
    - 'random' / 'mixed': ngẫu nhiên cả hai (tỷ lệ 80% desktop, 20% mobile)
    """
    mode = device_mode.lower()
    if mode == "mobile":
        ua = random.choice(MOBILE_USER_AGENTS)
        w, h = random.choice(MOBILE_RESOLUTIONS)
    elif mode == "desktop":
        ua = random.choice(DESKTOP_USER_AGENTS)
        w, h = random.choice(DESKTOP_RESOLUTIONS)
    else:
        # 80% desktop, 20% mobile
        if random.random() < 0.8:
            ua = random.choice(DESKTOP_USER_AGENTS)
            w, h = random.choice(DESKTOP_RESOLUTIONS)
        else:
            ua = random.choice(MOBILE_USER_AGENTS)
            w, h = random.choice(MOBILE_RESOLUTIONS)
            
    return ua, w, h
