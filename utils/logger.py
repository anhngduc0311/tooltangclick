import datetime
import threading
from typing import Callable, List, Dict

class AppLogger:
    """
    Hệ thống ghi log tập trung, thread-safe, hỗ trợ gửi trực tiếp lên giao diện CustomTkinter.
    """
    def __init__(self, max_history: int = 2000):
        self._listeners: List[Callable[[Dict], None]] = []
        self._lock = threading.Lock()
        self._history: List[Dict] = []
        self._max_history = max_history

    def add_listener(self, listener: Callable[[Dict], None]):
        """Đăng ký hàm nhận log từ UI"""
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Dict], None]):
        """Hủy đăng ký hàm nhận log"""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def log(self, level: str, message: str, thread_name: str = ""):
        """Ghi nhận log mới"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "level": level.upper(),
            "message": message,
            "thread": thread_name
        }

        with self._lock:
            self._history.append(entry)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            listeners_copy = list(self._listeners)

        for callback in listeners_copy:
            try:
                callback(entry)
            except Exception:
                pass

    def info(self, message: str, thread_name: str = ""):
        self.log("INFO", message, thread_name)

    def success(self, message: str, thread_name: str = ""):
        self.log("SUCCESS", message, thread_name)

    def warning(self, message: str, thread_name: str = ""):
        self.log("WARNING", message, thread_name)

    def error(self, message: str, thread_name: str = ""):
        self.log("ERROR", message, thread_name)

    def clear(self):
        with self._lock:
            self._history.clear()

# Singleton instance dùng chung toàn app
logger = AppLogger()
