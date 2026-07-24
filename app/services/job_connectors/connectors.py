from __future__ import annotations
from datetime import datetime,timezone
from html import unescape
from urllib.parse import quote_plus
import re,pandas as pd
from app.services.job_connectors.cache import get_json as cache_get,set_json as cache_set
from app.services.job_connectors.http import get_json,post_json
from app.services.job_connectors.types import ConnectorResult,empty_jobs,normalize_jobs

def _matches(text,role):
    terms=[x.lower() for x in re.split(r"[^a-zA-Z0-9+#]+",role) if len(x)>=3]
    hay=(text or "").lower(); return not terms or any(x in hay for x in terms)
def _strip(v): return re.sub(r"<[^>]+>"," ",unescape(v or "")).strip()

class JobSpyConnector:
    def __init__(self,c): self.config=c
    def search(self,*,role,location,results_wanted,hours_old):
        try:
            from app.services.job_search import search_jobs
            jobs=search_jobs(search_term=role,location=location,results_wanted=results_wanted,hours_old=hours_old,sites=[self.config.options.get("site",self.config.key)],fetch_linkedin_description=True)
            return ConnectorResult(normalize_jobs(jobs,source=self.config,searched_role=role),"success")
        except Exception as e:return ConnectorResult(empty_jobs(),"error",str(e))

class GreenhouseConnector:
    def __init__(self,c): self.config=c
    def search(self,*,role,location,results_wanted,hours_old):
        del location,hours_old
        if not self.config.token:return ConnectorResult(empty_jobs(),"disabled","Greenhouse board token is not configured.",self.config.board_url)
        try:
            key=f"gh:{self.config.token}"; data=cache_get(key,900)
            if data is None:
                data=get_json(f"https://boards-api.greenhouse.io/v1/boards/{self.config.token}/jobs",params={"content":"true"}); cache_set(key,data)
            rows=[]
            for item in data.get("jobs",[]):
                loc=(item.get("location") or {}).get("name",""); body=_strip(item.get("content") or "")
                if not _matches(" ".join([item.get("title") or "",loc,body]),role): continue
                rows.append({"title":item.get("title") or "","company":self.config.company,"location":loc,"date_posted":item.get("updated_at"),"is_remote":"remote" in loc.lower(),"job_url":item.get("absolute_url") or "","description":body,"requirements":body})
                if len(rows)>=results_wanted:break
            return ConnectorResult(normalize_jobs(pd.DataFrame(rows),source=self.config,searched_role=role),"success",direct_url=self.config.board_url)
        except Exception as e:return ConnectorResult(empty_jobs(),"error",str(e),self.config.board_url)

class LeverConnector:
    def __init__(self,c): self.config=c
    def search(self,*,role,location,results_wanted,hours_old):
        del location,hours_old
        if not self.config.token:return ConnectorResult(empty_jobs(),"disabled","Lever site token is not configured.",self.config.board_url)
        try:
            key=f"lever:{self.config.token}"; data=cache_get(key,900)
            if data is None:data=get_json(f"https://api.lever.co/v0/postings/{self.config.token}",params={"mode":"json"}); cache_set(key,data)
            rows=[]
            for item in data:
                cats=item.get("categories") or {}; loc=cats.get("location") or ""; body=" ".join([item.get("descriptionPlain") or "",item.get("additionalPlain") or ""]).strip()
                if not _matches(" ".join([item.get("text") or "",loc,body]),role):continue
                created=item.get("createdAt"); posted=datetime.fromtimestamp(created/1000,tz=timezone.utc).isoformat() if isinstance(created,(int,float)) else None
                rows.append({"title":item.get("text") or "","company":self.config.company,"location":loc,"date_posted":posted,"job_type":cats.get("commitment") or "","is_remote":"remote" in loc.lower(),"job_url":item.get("hostedUrl") or "","description":body,"requirements":body})
                if len(rows)>=results_wanted:break
            return ConnectorResult(normalize_jobs(pd.DataFrame(rows),source=self.config,searched_role=role),"success",direct_url=self.config.board_url)
        except Exception as e:return ConnectorResult(empty_jobs(),"error",str(e),self.config.board_url)

class SmartRecruitersConnector:
    def __init__(self,c):self.config=c
    def search(self,*,role,location,results_wanted,hours_old):
        del location,hours_old
        if not self.config.token:return ConnectorResult(empty_jobs(),"disabled","SmartRecruiters company identifier is not configured.",self.config.board_url)
        try:
            data=get_json(f"https://api.smartrecruiters.com/v1/companies/{self.config.token}/postings",params={"q":role,"limit":min(results_wanted,100),"offset":0})
            rows=[]
            for item in data.get("content",[]):
                loc=item.get("location") or {}; loc_text=", ".join(v for v in [loc.get("city"),loc.get("region"),loc.get("country")] if v)
                rows.append({"title":item.get("name") or "","company":self.config.company,"location":loc_text,"date_posted":item.get("releasedDate"),"job_type":(item.get("typeOfEmployment") or {}).get("label",""),"is_remote":"remote" in loc_text.lower(),"job_url":f"https://jobs.smartrecruiters.com/{self.config.token}/{item.get('id','')}","description":"","requirements":""})
            return ConnectorResult(normalize_jobs(pd.DataFrame(rows),source=self.config,searched_role=role),"success",direct_url=self.config.board_url)
        except Exception as e:return ConnectorResult(empty_jobs(),"error",str(e),self.config.board_url)

class WorkdayConnector:
    def __init__(self,c):self.config=c
    def search(self,*,role,location,results_wanted,hours_old):
        del location,hours_old
        o=self.config.options; tenant=o.get("tenant","");site=o.get("site","");host=o.get("host","")
        if not all([tenant,site,host]):return ConnectorResult(empty_jobs(),"disabled","Workday tenant, site and host are not configured.",self.config.board_url)
        try:
            data=post_json(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",payload={"appliedFacets":{},"limit":min(results_wanted,20),"offset":0,"searchText":role})
            rows=[]
            for item in data.get("jobPostings",[]):
                loc=item.get("locationsText") or ""; ext=item.get("externalPath") or ""
                rows.append({"title":item.get("title") or "","company":self.config.company,"location":loc,"date_posted":item.get("postedOn"),"is_remote":"remote" in loc.lower(),"job_url":f"https://{host}/en-US/{site}{ext}","description":"","requirements":""})
            return ConnectorResult(normalize_jobs(pd.DataFrame(rows),source=self.config,searched_role=role),"success",direct_url=self.config.board_url)
        except Exception as e:return ConnectorResult(empty_jobs(),"error",str(e),self.config.board_url)

class DirectLinkConnector:
    def __init__(self,c):self.config=c
    def search(self,*,role,location,results_wanted,hours_old):
        del results_wanted,hours_old
        template=self.config.options.get("search_url",self.config.board_url); role_slug="-".join(role.lower().strip().split()); location_slug="-".join(location.lower().replace("bengaluru","bangalore").split(",")[0].strip().split())
        url=template.format(role=quote_plus(role),location=quote_plus(location),role_slug=role_slug,location_slug=location_slug) if template else ""
        return ConnectorResult(empty_jobs(),"manual","Open this source directly; automated collection is intentionally disabled.",url)

CONNECTORS={"jobspy":JobSpyConnector,"greenhouse":GreenhouseConnector,"lever":LeverConnector,"smartrecruiters":SmartRecruitersConnector,"workday":WorkdayConnector,"direct_link":DirectLinkConnector}
