from __future__ import annotations
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd
from app.services.job_connectors.connectors import CONNECTORS
from app.services.job_connectors.registry import enabled_connector_map
from app.services.job_connectors.types import empty_jobs

def collect_jobs(*,roles,location,selected_source_keys,results_per_role,hours_old,max_workers=5):
    sm=enabled_connector_map(); sources=[sm[k] for k in selected_source_keys if k in sm]
    if not sources:raise ValueError("Select at least one enabled source.")
    frames=[];errors=[];runs=[];links=[]
    with ThreadPoolExecutor(max_workers=max(1,min(max_workers,8))) as pool:
        futures={}
        for role in roles:
            role=str(role).strip()
            if not role:continue
            for source in sources:
                cls=CONNECTORS.get(source.connector)
                if cls is None:continue
                futures[pool.submit(cls(source).search,role=role,location=location,results_wanted=results_per_role,hours_old=hours_old)]=(source,role)
        for future in as_completed(futures):
            source,role=futures[future]
            try:
                result=future.result(); count=len(result.jobs)
                runs.append({"source":source.label,"group":source.group,"role":role,"status":result.status,"collected":count,"error":result.error})
                if result.direct_url:links.append({"source":source.label,"role":role,"url":result.direct_url})
                if count:frames.append(result.jobs)
                if result.status=="error":errors.append(f"{source.label} / {role}: {result.error}")
            except Exception as e:
                errors.append(f"{source.label} / {role}: {e}");runs.append({"source":source.label,"group":source.group,"role":role,"status":"error","collected":0,"error":str(e)})
    jobs=pd.concat(frames,ignore_index=True,sort=False) if frames else empty_jobs(); counts=Counter(jobs["source_group"].fillna("unknown")) if not jobs.empty else Counter()
    sc={"job_boards":int(counts.get("job_board",0)),"india_boards":int(counts.get("india_board",0)),"company_careers":int(counts.get("company_careers",0)),"ats_platforms":int(counts.get("ats_platform",0)),"total":int(len(jobs))}
    return jobs,errors,sc,runs,links
