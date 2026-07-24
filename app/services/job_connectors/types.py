from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import pandas as pd

JOB_COLUMNS=["site","source_key","source_group","source_label","official_source","title","company","location","date_posted","job_type","is_remote","job_url","description","experience","requirements","searched_role"]

@dataclass(frozen=True)
class ConnectorConfig:
    key:str; label:str; connector:str; group:str
    enabled:bool=True; official_source:bool=False
    company:str=""; token:str=""; board_url:str=""
    priority:int=50; options:dict[str,Any]=field(default_factory=dict)

@dataclass
class ConnectorResult:
    jobs:pd.DataFrame; status:str; error:str=""; direct_url:str=""

def empty_jobs(): return pd.DataFrame(columns=JOB_COLUMNS)

def normalize_jobs(frame,*,source,searched_role):
    if frame is None or frame.empty: return empty_jobs()
    result=frame.copy()
    defaults={"site":source.key,"source_key":source.key,"source_group":source.group,"source_label":source.label,"official_source":source.official_source,"title":"","company":source.company,"location":"","date_posted":None,"job_type":"","is_remote":False,"job_url":"","description":"","experience":"","requirements":"","searched_role":searched_role}
    for col,default in defaults.items():
        if col not in result.columns: result[col]=default
        else: result[col]=result[col].where(result[col].notna(),default)
    result["site"]=source.key; result["source_key"]=source.key; result["source_group"]=source.group; result["source_label"]=source.label; result["official_source"]=bool(source.official_source); result["searched_role"]=searched_role
    if source.company:
        missing=result["company"].fillna("").astype(str).str.strip()==""
        result.loc[missing,"company"]=source.company
    return result[JOB_COLUMNS]
