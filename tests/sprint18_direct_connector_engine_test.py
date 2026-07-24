from __future__ import annotations
import ast
from pathlib import Path
from app.services.job_connectors.connectors import CONNECTORS
from app.services.job_connectors.registry import enabled_connector_map,connector_groups
ROOT=Path(__file__).resolve().parents[1]
def main():
    sm=enabled_connector_map();groups=connector_groups()
    assert {"indeed","linkedin","naukri","foundit","internshala"}<=set(sm)
    assert {"jobspy","greenhouse","lever","smartrecruiters","workday","direct_link"}<=set(CONNECTORS)
    text=(ROOT/'pages/1_Job_Search.py').read_text(encoding='utf-8');ast.parse(text);assert 'Open manual job searches' in text;assert 'job_platform_v2' not in text
    print('='*72);print('CAREERPILOT SPRINT 18 DIRECT CONNECTOR ENGINE TEST');print('='*72);print('Enabled sources:',len(sm));print('Automated sources:',len(groups['job_board']));print('Manual India searches:',len(groups['india_board']));print('Connector types:',len(CONNECTORS));print();print('SPRINT 18 DIRECT CONNECTOR ENGINE TEST PASSED')
if __name__=='__main__':main()
