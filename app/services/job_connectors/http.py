from __future__ import annotations
import time,requests
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/150 Safari/537.36","Accept":"application/json,text/plain,*/*"}
def get_json(url,*,params=None,attempts=3,timeout=25):
    last=None
    for i in range(attempts):
        try:
            r=requests.get(url,params=params,headers=HEADERS,timeout=timeout); r.raise_for_status(); return r.json()
        except Exception as e:
            last=e
            if i<attempts-1: time.sleep(1.5*(i+1))
    raise last
def post_json(url,*,payload,attempts=3,timeout=25):
    last=None
    for i in range(attempts):
        try:
            r=requests.post(url,json=payload,headers=HEADERS,timeout=timeout); r.raise_for_status(); return r.json()
        except Exception as e:
            last=e
            if i<attempts-1: time.sleep(1.5*(i+1))
    raise last
