from typing import Dict, Optional
from datetime import datetime, timedelta
import hashlib

class CommandCache:
    def __init__(self, ttl_seconds: int = 7200):  # 默认缓存2小时
        self._cache: Dict[str, Dict[str, any]] = {}
        self._ttl_seconds = ttl_seconds
    
    def _generate_key(self, command: str) -> str:
        """生成缓存键"""
        # 规范化命令文本（去除多余空格，转小写）
        normalized = ' '.join(command.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, command: str) -> Optional[str]:
        """获取缓存的 SQL"""
        key = self._generate_key(command)
        if key in self._cache:
            cached_data = self._cache[key]
            if datetime.now() < cached_data['expires_at']:
                print(f"Command cache hit for: {command}")
                return cached_data['sql']
            else:
                del self._cache[key]
        return None
    
    def set(self, command: str, sql: str) -> None:
        """缓存命令对应的 SQL"""
        key = self._generate_key(command)
        self._cache[key] = {
            'sql': sql,
            'expires_at': datetime.now() + timedelta(seconds=self._ttl_seconds),
            'command': command  # 保存原始命令用于调试
        }
        print(f"Cached SQL for command: {command}")
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        print("Command cache cleared")
    
    def remove_expired(self) -> None:
        """删除过期缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self._cache.items()
            if now >= value['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            print(f"Removed {len(expired_keys)} expired command cache entries")
    
    def get_stats(self) -> Dict[str, any]:
        """获取缓存统计信息"""
        now = datetime.now()
        return {
            'total_entries': len(self._cache),
            'active_entries': sum(1 for v in self._cache.values() if v['expires_at'] > now),
            'expired_entries': sum(1 for v in self._cache.values() if v['expires_at'] <= now),
            'commands': [v['command'] for v in self._cache.values() if v['expires_at'] > now]
        } 