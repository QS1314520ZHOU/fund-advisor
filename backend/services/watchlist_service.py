
import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class WatchlistService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.watchlist_file = self.data_dir / "watchlist.json"
        
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
            
        if not self.watchlist_file.exists():
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_watchlist(self) -> List[Dict]:
        try:
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load watchlist: {e}")
            return []

    def _save_watchlist(self, watchlist: List[Dict]):
        try:
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(watchlist, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save watchlist: {e}")

    def get_watchlist(self) -> List[Dict]:
        return self._load_watchlist()

    def add_to_watchlist(self, code: str, name: str) -> bool:
        watchlist = self._load_watchlist()
        if any(item['code'] == code for item in watchlist):
            return True
            
        watchlist.append({
            'code': code,
            'name': name,
            'added_at': os.times()[4] # Using some timestamp proxy if time.time() is not imported
        })
        
        # Fixed timestamp
        import time
        watchlist[-1]['added_at'] = time.time()
        
        self._save_watchlist(watchlist)
        return True

    def remove_from_watchlist(self, code: str) -> bool:
        watchlist = self._load_watchlist()
        original_len = len(watchlist)
        watchlist = [item for item in watchlist if item['code'] != code]
        
        if len(watchlist) < original_len:
            self._save_watchlist(watchlist)
            return True
        return False

_watchlist_service = None

def get_watchlist_service() -> WatchlistService:
    global _watchlist_service
    if _watchlist_service is None:
        _watchlist_service = WatchlistService()
    return _watchlist_service
