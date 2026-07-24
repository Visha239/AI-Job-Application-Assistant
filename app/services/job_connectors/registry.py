from __future__ import annotations
import json
from pathlib import Path
from app.services.job_connectors.types import ConnectorConfig
DEFAULT_CONFIG=Path("config/job_connectors.json")
def load_connectors(path=DEFAULT_CONFIG):
    payload=json.loads(Path(path).read_text(encoding="utf-8-sig")); out=[]
    for r in payload.get("connectors",[]):
        c=ConnectorConfig(key=str(r.get("key","")).strip(),label=str(r.get("label","")).strip(),connector=str(r.get("connector","")).strip(),group=str(r.get("group","job_board")).strip(),enabled=bool(r.get("enabled",True)),official_source=bool(r.get("official_source",False)),company=str(r.get("company","")).strip(),token=str(r.get("token","")).strip(),board_url=str(r.get("board_url","")).strip(),priority=int(r.get("priority",50)),options=dict(r.get("options",{})))
        if c.key:out.append(c)
    return out
def enabled_connector_map(path=DEFAULT_CONFIG):return {c.key:c for c in load_connectors(path) if c.enabled}
def connector_groups(path=DEFAULT_CONFIG):
    groups={}
    for c in enabled_connector_map(path).values():groups.setdefault(c.group,[]).append(c)
    for vals in groups.values():vals.sort(key=lambda c:(c.priority,c.label.lower()))
    return groups
