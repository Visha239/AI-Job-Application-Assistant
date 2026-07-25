from __future__ import annotations
import hashlib,json,time
from pathlib import Path
CACHE_DIR=Path("data/job_connector_cache"); CACHE_DIR.mkdir(parents=True,exist_ok=True)
def _path(key): return CACHE_DIR/f"{hashlib.sha256(key.encode()).hexdigest()}.json"
def get_json(key,ttl_seconds):
    path=_path(key)
    if not path.exists(): return None
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
        if time.time()-float(payload["saved_at"])>ttl_seconds:return None
        return payload["data"]
    except Exception:return None
def set_json(key,data):
    _path(key).write_text(json.dumps({"saved_at":time.time(),"data":data},ensure_ascii=False),encoding="utf-8")
