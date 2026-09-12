import os
import re
import json
import time
import tempfile
import zipfile
import threading
import requests
from typing import Optional, Dict, List, Tuple
from utils.logger import logger

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".proxy_cache.json")

class ProxyItem:
    def __init__(self, raw: str):
        self.raw = raw.strip()
        self.scheme = "http"
        self.host = ""
        self.port = 80
        self.username = None
        self.password = None
        self._parse()

    def _parse(self):
        text = self.raw
        # Bỏ tiền tố scheme nếu có
        if text.startswith("http://"):
            self.scheme = "http"
            text = text[7:]
        elif text.startswith("https://"):
            self.scheme = "https"
            text = text[8:]
        elif text.startswith("socks5://"):
            self.scheme = "socks5"
            text = text[9:]

        # Xử lý trường hợp proxy trả về có 2 dấu hai chấm ở đuôi như Proxy.vn (ví dụ: 42.117.243.215:10836::)
        if text.endswith("::"):
            text = text[:-2]

        # Dạng user:pass@host:port
        if "@" in text:
            auth_part, host_part = text.split("@", 1)
            if ":" in auth_part:
                self.username, self.password = auth_part.split(":", 1)
            else:
                self.username = auth_part
            if ":" in host_part:
                self.host, port_str = host_part.split(":", 1)
                self.port = int(port_str)
            else:
                self.host = host_part
        # Dạng host:port:user:pass hoặc host:port
        elif ":" in text:
            parts = text.split(":")
            if len(parts) == 2:
                self.host = parts[0]
                self.port = int(parts[1])
            elif len(parts) == 4:
                self.host = parts[0]
                self.port = int(parts[1])
                self.username = parts[2] if parts[2].strip() else None
                self.password = parts[3] if parts[3].strip() else None
            else:
                self.host = parts[0]
                self.port = int(parts[1])
        else:
            self.host = text

    @property
    def has_auth(self) -> bool:
        return bool(self.username and self.password)

    def to_standard_url(self) -> str:
        """Định dạng chuẩn URL cho requests hoặc DrissionPage không auth"""
        if self.has_auth:
            return f"{self.scheme}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.scheme}://{self.host}:{self.port}"

    def to_requests_dict(self) -> dict:
        url = self.to_standard_url()
        return {"http": url, "https": url}

class ProxyManager:
    def __init__(self):
        self.proxies: List[ProxyItem] = []
        self.api_url: str = ""
        self._index: int = 0
        self._lock = threading.Lock()
        self._temp_ext_dirs: List[str] = []
        self._last_api_proxy: Optional[ProxyItem] = None
        self._last_fetch_time: float = 0
        self._load_cache()

    def _save_cache(self, proxy_item: ProxyItem):
        try:
            data = {
                "raw": proxy_item.raw,
                "timestamp": time.time()
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_cache(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                t = data.get("timestamp", 0)
                if time.time() - t < 1200:
                    raw = data.get("raw")
                    if raw:
                        self._last_api_proxy = ProxyItem(raw)
                        self._last_fetch_time = t
                        logger.info(f"[Proxy] Đã nạp proxy từ bộ nhớ đệm: {self._last_api_proxy.host}:{self._last_api_proxy.port}", "Proxy")
        except Exception:
            pass

    def set_proxies_from_text(self, text: str):
        """Nạp danh sách proxy từ chuỗi nhiều dòng"""
        with self._lock:
            self.proxies.clear()
            lines = text.strip().splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        self.proxies.append(ProxyItem(line))
                    except Exception:
                        pass
            self._index = 0

    def set_api_url(self, api_url: str):
        self.api_url = api_url.strip()

    def get_proxy(self) -> Optional[ProxyItem]:
        """Lấy proxy tiếp theo theo cơ chế Round Robin hoặc từ API xoay IP"""
        # Nếu có API xoay IP, thử gọi API
        if self.api_url:
            api_proxy = self._fetch_proxy_from_api(self.api_url)
            if api_proxy:
                return api_proxy

        with self._lock:
            if not self.proxies:
                return None
            proxy = self.proxies[self._index % len(self.proxies)]
            self._index += 1
            return proxy

    def _fetch_proxy_from_api(self, api_url: str) -> Optional[ProxyItem]:
        """
        Hỗ trợ các nhà cung cấp API Proxy:
        - Proxy.vn / Proxyxoay.shop: {"status": 100, "proxyhttp": "ip:port::", "message": "...", ...}
        - TMProxy: {"code": 0, "data": {"https": "ip:port"}}
        - Tinsoft: {"success": true, "proxy": "ip:port"}
        - Plain text: IP:PORT
        """
        url = api_url.strip()
        # Nếu người dùng chỉ nhập Key của Proxy.vn (không có http)
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://proxyxoay.shop/api/get.php?key={url}&nhamang=Random&tinhthanh=0"

        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.text.strip()
                try:
                    js = resp.json()
                    
                    # 1. Định dạng Proxy.vn / Proxyxoay.shop
                    if "status" in js:
                        st = js.get("status")
                        if st == 100:
                            proxy_str = js.get("proxyhttp") or js.get("proxysocks5")
                            if proxy_str:
                                raw_clean = proxy_str.rstrip(":")
                                prefix = "socks5://" if "proxysocks5" in js and not js.get("proxyhttp") else ""
                                item = ProxyItem(f"{prefix}{raw_clean}")
                                with self._lock:
                                    self._last_api_proxy = item
                                    self._last_fetch_time = time.time()
                                self._save_cache(item)
                                msg = js.get("message", "")
                                loc = js.get("Vi Tri", "")
                                logger.info(f"[Proxy.vn] Đổi IP thành công: {item.host}:{item.port} ({loc}) - {msg}", "Proxy")
                                return item
                        elif st in [101, 102]:
                            err_msg = js.get("message") or js.get("comen") or f"Mã trạng thái {st}"
                            logger.warning(f"[Proxy.vn] Phản hồi API: {err_msg}", "Proxy")
                            # Nếu proxy cũ trước đó vẫn còn hiệu lực trong vòng 20 phút thì dùng lại
                            with self._lock:
                                if self._last_api_proxy and (time.time() - self._last_fetch_time < 1200):
                                    logger.info(f"[Proxy.vn] Tiếp tục sử dụng proxy hiện tại: {self._last_api_proxy.host}:{self._last_api_proxy.port}", "Proxy")
                                    return self._last_api_proxy

                            # Nếu chưa có proxy cũ và cần chờ, tự động chờ nếu <= 60s
                            wait_m = re.search(r'(\d+)\s*s', err_msg)
                            wait_sec = int(wait_m.group(1)) if wait_m else 0
                            if 0 < wait_sec <= 60:
                                logger.info(f"[Proxy.vn] Đang chờ {wait_sec + 1}s để đổi IP mới...", "Proxy")
                                time.sleep(wait_sec + 1)
                                return self._fetch_proxy_from_api(api_url)

                    # 2. TMProxy: {"code": 0, "data": {"https": "ip:port"}}
                    if "data" in js and isinstance(js["data"], dict) and "https" in js["data"]:
                        item = ProxyItem(js["data"]["https"])
                        with self._lock:
                            self._last_api_proxy = item
                        return item

                    # 3. Tinsoft: {"success": true, "proxy": "ip:port"}
                    if "proxy" in js and js["proxy"]:
                        item = ProxyItem(js["proxy"])
                        with self._lock:
                            self._last_api_proxy = item
                        return item

                except Exception:
                    pass

                # 4. Kiểm tra chuỗi IP:PORT thông thường
                match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b', data)
                if match:
                    item = ProxyItem(match.group(0))
                    with self._lock:
                        self._last_api_proxy = item
                    return item

        except Exception as e:
            logger.error(f"Lỗi khi kết nối API xoay proxy: {e}", "Proxy")

        with self._lock:
            return self._last_api_proxy

    @staticmethod
    def test_api_xoay(api_url_or_key: str) -> Dict:
        """Kiểm tra gọi API xoay Proxy.vn / TMProxy trực tiếp và trả về chi tiết"""
        url = api_url_or_key.strip()
        if not url:
            return {"success": False, "message": "Chưa nhập URL hoặc Key API"}

        # Nếu chỉ có key xoay của Proxy.vn
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://proxyxoay.shop/api/get.php?key={url}&nhamang=Random&tinhthanh=0"

        try:
            start = time.time()
            resp = requests.get(url, timeout=10)
            latency = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                try:
                    js = resp.json()
                    # Trường hợp Proxy.vn
                    if "status" in js:
                        if js.get("status") == 100:
                            proxy_http = (js.get("proxyhttp") or "").rstrip(":")
                            msg = js.get("message", "")
                            location = js.get("Vi Tri", "")
                            isp = js.get("Nha Mang", "")
                            try:
                                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                                    json.dump({"raw": proxy_http, "timestamp": time.time()}, f)
                            except Exception:
                                pass
                            return {
                                "success": True,
                                "proxy": proxy_http,
                                "latency_ms": latency,
                                "detail": f"IP: {proxy_http} | Nhà mạng: {isp} | Vị trí: {location} ({msg})"
                            }
                        else:
                            err_msg = js.get("message") or js.get("comen") or f"Lỗi status={js.get('status')}"
                            cached_info = ""
                            try:
                                if os.path.exists(CACHE_FILE):
                                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                                        cd = json.load(f)
                                    if time.time() - cd.get("timestamp", 0) < 1200:
                                        cached_info = f" (Proxy đang dùng: {cd.get('raw')})"
                            except Exception:
                                pass
                            return {
                                "success": bool(cached_info),
                                "proxy": None,
                                "latency_ms": latency,
                                "detail": f"[Proxy.vn]: {err_msg}{cached_info}"
                            }
                    # Các loại API khác
                    return {
                        "success": True,
                        "proxy": str(js),
                        "latency_ms": latency,
                        "detail": f"Phản hồi JSON: {str(js)[:100]}"
                    }
                except Exception:
                    return {
                        "success": True,
                        "proxy": resp.text.strip()[:50],
                        "latency_ms": latency,
                        "detail": resp.text.strip()[:100]
                    }
            return {
                "success": False,
                "proxy": None,
                "latency_ms": latency,
                "detail": f"HTTP Status {resp.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "proxy": None,
                "latency_ms": 0,
                "detail": f"Lỗi kết nối: {e}"
            }

    def create_proxy_auth_extension(self, proxy: ProxyItem) -> Optional[str]:
        """
        Tạo Chrome Extension tạm thời để xử lý xác thực tài khoản Proxy (username/password).
        Trả về đường dẫn thư mục extension được giải nén.
        """
        if not proxy or not proxy.has_auth:
            return None

        manifest_json = """{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy Auth",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}"""

        background_js = f"""var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "{proxy.scheme}",
            host: "{proxy.host}",
            port: parseInt({proxy.port})
        }},
        bypassList: ["localhost", "127.0.0.1"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy.username}",
            password: "{proxy.password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);
"""
        ext_dir = tempfile.mkdtemp(prefix="proxy_ext_")
        with open(os.path.join(ext_dir, "manifest.json"), "w", encoding="utf-8") as f:
            f.write(manifest_json)
        with open(os.path.join(ext_dir, "background.js"), "w", encoding="utf-8") as f:
            f.write(background_js)

        with self._lock:
            self._temp_ext_dirs.append(ext_dir)
        return ext_dir

    @staticmethod
    def test_proxy(proxy_str: str, timeout: int = 6) -> Dict:
        """Kiểm tra proxy có hoạt động không, trả về thông tin IP và độ trễ"""
        try:
            item = ProxyItem(proxy_str)
            proxies_dict = item.to_requests_dict()
            start = time.time()
            resp = requests.get(
                "http://httpbin.org/ip",
                proxies=proxies_dict,
                timeout=timeout
            )
            latency = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                ip_data = resp.json().get("origin", "")
                return {
                    "success": True,
                    "ip": ip_data,
                    "latency_ms": latency,
                    "error": None
                }
            return {
                "success": False,
                "ip": None,
                "latency_ms": latency,
                "error": f"Mã trạng thái {resp.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "ip": None,
                "latency_ms": 0,
                "error": str(e)
            }
