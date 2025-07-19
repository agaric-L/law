# backend/app/services/case_cards.py
import time
from threading import Lock
from .falv_fetcher import CourtCaseDataFetcher 
fetcher = CourtCaseDataFetcher()
_cache = {"data": None, "ts": 0}
_cache_lock = Lock()

def get_case_cards(force_refresh=False):
    """获取五类案例卡片数据，带1小时缓存"""
    with _cache_lock:
        now = time.time()
        if not force_refresh and _cache["data"] and now - _cache["ts"] < 3600:
            return _cache["data"]
        all_cases = fetcher.get_all_case_types()
        _cache["data"] = all_cases
        _cache["ts"] = now
        return all_cases