import os
import re
import tempfile
import zipfile
import threading
import requests
from typing import Optional, Dict, List, Tuple

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
                self.username = parts[2]
                self.password = parts[3]
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
        """Gọi API dịch vụ xoay IP (TMProxy, Tinsoft, v.v...) để lấy IP mới"""
        try:
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.text.strip()
                # Nếu API trả về JSON
                try:
                    js = resp.json()
                    # Trường hợp TMProxy: {"code": 0, "data": {"https": "ip:port"}}
                    if "data" in js and isinstance(js["data"], dict) and "https" in js["data"]:
                        return ProxyItem(js["data"]["https"])
                    # Trường hợp Tinsoft: {"success": true, "proxy": "ip:port"}
                    if "proxy" in js and js["proxy"]:
                        return ProxyItem(js["proxy"])
                except Exception:
                    pass
                
                # Kiểm tra IP:PORT dạng text thông thường
                match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b', data)
                if match:
                    return ProxyItem(match.group(0))
        except Exception:
            pass
        return None

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
            import time
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
