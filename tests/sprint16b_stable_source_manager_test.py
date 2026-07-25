from __future__ import annotations

import ast
from pathlib import Path

from app.services.job_sources.source_manager import (
    build_source_selection,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    page_path = ROOT / "pages" / "1_Job_Search.py"
    page_text = page_path.read_text(encoding="utf-8")
    ast.parse(page_text)

    assert "build_naukri_search_url(search_term" not in page_text
    assert "naukri_link_role =" in page_text
    assert "build_naukri_search_url(naukri_link_role" in page_text

    naukri_only = build_source_selection(
        jobspy_sites=[],
        include_naukri=True,
        include_company_careers=False,
        selected_companies=[],
    )
    assert naukri_only.has_any_source

    company_only = build_source_selection(
        jobspy_sites=[],
        include_naukri=False,
        include_company_careers=True,
        selected_companies=["Microsoft"],
    )
    assert company_only.has_any_source

    jobspy_only = build_source_selection(
        jobspy_sites=["indeed"],
        include_naukri=False,
        include_company_careers=False,
        selected_companies=[],
    )
    assert jobspy_only.has_any_source

    print("=" * 72)
    print("CAREERPILOT SPRINT 16B STABLE SOURCE MANAGER TEST")
    print("=" * 72)
    print("Undefined search_term bug: fixed")
    print("Naukri-only search: supported")
    print("Company-only search: supported")
    print("JobSpy-only search: supported")
    print()
    print("SPRINT 16B STABLE SOURCE MANAGER TEST PASSED")


if __name__ == "__main__":
    main()
