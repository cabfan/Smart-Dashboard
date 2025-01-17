from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

class QueryCache:
    def __init__(self, ttl_seconds: int = 3600):  # 默认缓存1小时
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds
    
    def _generate_key(self, sql: str, params: tuple = None) -> str:
        """生成缓存键"""
        # 将 SQL 和参数组合成一个唯一的字符串
        cache_str = sql
        if params:
            cache_str += json.dumps(params, sort_keys=True)
        # 使用 MD5 生成固定长度的键
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """获取缓存的查询结果"""
        key = self._generate_key(sql, params)
        if key in self._cache:
            cached_data = self._cache[key]
            # 检查是否过期
            if datetime.now() < cached_data['expires_at']:
                print(f"Cache hit for query: {sql[:100]}...")
                return cached_data['data']
            else:
                # 删除过期数据
                del self._cache[key]
        return None
    
    def set(self, sql: str, params: tuple, data: Dict[str, Any]) -> None:
        """缓存查询结果"""
        key = self._generate_key(sql, params)
        self._cache[key] = {
            'data': data,
            'expires_at': datetime.now() + timedelta(seconds=self._ttl_seconds)
        }
        print(f"Cached query result for: {sql[:100]}...")
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        print("Cache cleared")
    
    def remove_expired(self) -> None:
        """删除所有过期的缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self._cache.items()
            if now >= value['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            print(f"Removed {len(expired_keys)} expired cache entries") 