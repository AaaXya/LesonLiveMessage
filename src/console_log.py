"""
console_log.py — 控制台日志捕获
将 print / stdout / stderr 输出镜像到内存环形缓冲区，
供前端「控制台」页面实时查看后端日志。
"""

import sys
import threading

MAX_LINES = 500

_lock = threading.Lock()
_lines = []
_seq = 0


def _append(text: str):
    global _seq
    if not text:
        return
    with _lock:
        for line in text.splitlines():
            if not line.strip():
                continue
            _seq += 1
            _lines.append({"seq": _seq, "time": None, "line": line})
            if len(_lines) > MAX_LINES:
                del _lines[: len(_lines) - MAX_LINES]


class _TeeWriter:
    """写入时同时发送到原始流和日志缓冲区"""

    def __init__(self, original):
        self.original = original

    def write(self, text):
        try:
            self.original.write(text)
            self.original.flush()
        except Exception:
            pass
        _append(text)
        return len(text)

    def flush(self):
        try:
            self.original.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return self.original.isatty()
        except Exception:
            return False


_installed = False


def install():
    """安装 stdout/stderr 捕获（幂等）"""
    global _installed
    if _installed:
        return
    sys.stdout = _TeeWriter(sys.stdout)
    sys.stderr = _TeeWriter(sys.stderr)
    _installed = True


def get_logs(since_seq=0, limit=200):
    with _lock:
        items = [item for item in _lines if item["seq"] > since_seq]
        return items[-limit:]


def clear():
    global _seq
    with _lock:
        _lines.clear()
        _seq = 0
