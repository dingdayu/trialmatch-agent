"""登录安全控制 — 对应 Task 4.5
提供登录失败计数和频率限制（内存实现，因当前无 Redis）"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Tuple


class LoginSecurityManager:
    """登录安全管理器（内存实现）"""

    def __init__(self, max_failures: int = 5, lock_minutes: int = 30, rate_limit: int = 10):
        self.max_failures = max_failures
        self.lock_minutes = lock_minutes
        self.rate_limit = rate_limit  # 每分钟

        self._failures: Dict[str, Tuple[int, float]] = {}  # username -> (count, first_attempt_time)
        self._attempts: Dict[str, list] = defaultdict(list)  # ip -> [timestamps]

    def check_login_allowed(self, username: str, ip: str = "0.0.0.0") -> bool:
        """检查是否允许登录"""
        # 检查失败次数
        if username in self._failures:
            count, first_time = self._failures[username]
            if count >= self.max_failures:
                lock_seconds = self.lock_minutes * 60
                if time.time() - first_time < lock_seconds:
                    return False
                else:
                    del self._failures[username]

        # 检查频率限制
        now = time.time()
        minute_ago = now - 60
        self._attempts[ip] = [t for t in self._attempts[ip] if t > minute_ago]
        if len(self._attempts[ip]) >= self.rate_limit:
            return False

        self._attempts[ip].append(now)
        return True

    def record_failure(self, username: str):
        """记录登录失败"""
        if username not in self._failures:
            self._failures[username] = (1, time.time())
        else:
            count, first_time = self._failures[username]
            self._failures[username] = (count + 1, first_time)

    def reset_failures(self, username: str):
        """重置失败计数（登录成功后）"""
        self._failures.pop(username, None)

    def get_remaining_lock_seconds(self, username: str) -> int:
        """获取剩余锁定秒数"""
        if username in self._failures:
            count, first_time = self._failures[username]
            if count >= self.max_failures:
                elapsed = time.time() - first_time
                lock_seconds = self.lock_minutes * 60
                remaining = int(lock_seconds - elapsed)
                return max(0, remaining)
        return 0


# 全局单例
login_security = LoginSecurityManager()
