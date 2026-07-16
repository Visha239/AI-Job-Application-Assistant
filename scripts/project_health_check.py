from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "dashboard.py",
    "requirements.txt",
    ".gitignore",
    "app/__init__.py",
    "app/services/application_context.py",
    "app/services/application_crm.py",
    "app/services/application_queue.py",
    "app/services/career_dashboard.py",
    "app/services/career_coach.py",
    "app/services/job_search.py",
    "app/services/one_click_optimizer.py",
    "app/services/resume_intelligence_v2.py",
    "pages/1_Job_Search.py",
    "pages/2_Apply_Workflow.py",
    "pages/9_Recruiter_Outreach.py",
    "pages/10_Auto_Apply_Assistant.py",
    "pages/11_Application_CRM.py",
    "pages/12_Career_Coach.py",
    "pages/13_Resume_Intelligence.py",
    "pages/14_One_Click_Optimizer.py",
    "resumes/master/master_resume.docx",
]

PRIVATE_PATHS = [
    ".env",
    "app/database/careerpilot.db",
    "data/current_job_context.json",
    "data/application_queue.json",
    "data/application_crm.json",
    "data/outreach_records.json",
    "data/resume_uploads",
    "exports",
]

REQUIRED_PACKAGES = [
    "streamlit",
    "pandas",
    "docx",
    "requests",
    "bs4",
    "dotenv",
]


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def check_required_paths(
    root: Path,
    required_paths: Iterable[str] = REQUIRED_PATHS,
) -> list[CheckResult]:
    results: list[CheckResult] = []

    for relative in required_paths:
        path = root / relative
        results.append(
            CheckResult(
                name=f"path:{relative}",
                status="PASS" if path.exists() else "FAIL",
                detail=(
                    "Found"
                    if path.exists()
                    else "Missing required project file"
                ),
            )
        )

    return results


def check_private_gitignore(
    root: Path,
    private_paths: Iterable[str] = PRIVATE_PATHS,
) -> list[CheckResult]:
    gitignore = root / ".gitignore"

    if not gitignore.exists():
        return [
            CheckResult(
                name="gitignore",
                status="FAIL",
                detail=".gitignore is missing",
            )
        ]

    text = gitignore.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    normalized_lines = {
        line.strip().rstrip("/")
        for line in text.splitlines()
        if line.strip()
        and not line.strip().startswith("#")
    }

    results: list[CheckResult] = []

    for private_path in private_paths:
        normalized = private_path.rstrip("/")
        ignored = any(
            normalized == line
            or normalized.startswith(line + "/")
            or line.startswith(normalized + "/")
            or (
                normalized.endswith(".db")
                and line == "*.db"
            )
            or (
                normalized == ".env"
                and line in {".env", ".env.*"}
            )
            or (
                normalized == "exports"
                and line.startswith("exports/")
            )
            for line in normalized_lines
        )

        results.append(
            CheckResult(
                name=f"private:{private_path}",
                status="PASS" if ignored else "WARN",
                detail=(
                    "Covered by .gitignore"
                    if ignored
                    else "Add this private/generated path to .gitignore"
                ),
            )
        )

    return results


def check_python_packages(
    packages: Iterable[str] = REQUIRED_PACKAGES,
) -> list[CheckResult]:
    results: list[CheckResult] = []

    for package in packages:
        available = importlib.util.find_spec(package) is not None
        results.append(
            CheckResult(
                name=f"package:{package}",
                status="PASS" if available else "FAIL",
                detail=(
                    "Installed"
                    if available
                    else "Package is not installed in the active environment"
                ),
            )
        )

    return results


def check_requirements_encoding(
    root: Path,
) -> list[CheckResult]:
    path = root / "requirements.txt"

    if not path.exists():
        return [
            CheckResult(
                name="requirements_encoding",
                status="FAIL",
                detail="requirements.txt is missing",
            )
        ]

    raw = path.read_bytes()

    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return [
            CheckResult(
                name="requirements_encoding",
                status="WARN",
                detail=(
                    "requirements.txt is UTF-16. "
                    "Convert it to UTF-8 for GitHub and deployment."
                ),
            )
        ]

    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return [
            CheckResult(
                name="requirements_encoding",
                status="FAIL",
                detail="requirements.txt is not valid UTF-8",
            )
        ]

    return [
        CheckResult(
            name="requirements_encoding",
            status="PASS",
            detail="requirements.txt is valid UTF-8",
        )
    ]


def run_health_check(
    root: Path = PROJECT_ROOT,
    *,
    include_packages: bool = True,
) -> dict:
    results: list[CheckResult] = []
    results.extend(check_required_paths(root))
    results.extend(check_private_gitignore(root))
    results.extend(check_requirements_encoding(root))

    if include_packages:
        results.extend(check_python_packages())

    counts = {
        "PASS": sum(item.status == "PASS" for item in results),
        "WARN": sum(item.status == "WARN" for item in results),
        "FAIL": sum(item.status == "FAIL" for item in results),
    }

    return {
        "project_root": str(root),
        "counts": counts,
        "results": [asdict(item) for item in results],
        "healthy": counts["FAIL"] == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check CareerPilot project readiness."
    )
    parser.add_argument(
        "--root",
        default=str(PROJECT_ROOT),
        help="CareerPilot project root",
    )
    parser.add_argument(
        "--skip-packages",
        action="store_true",
        help="Skip Python package checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output",
    )
    args = parser.parse_args()

    report = run_health_check(
        Path(args.root).resolve(),
        include_packages=not args.skip_packages,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 72)
        print("CAREERPILOT PROJECT HEALTH CHECK")
        print("=" * 72)

        for item in report["results"]:
            print(
                f"[{item['status']:<4}] "
                f"{item['name']}: {item['detail']}"
            )

        counts = report["counts"]
        print("-" * 72)
        print(
            f"PASS: {counts['PASS']} | "
            f"WARN: {counts['WARN']} | "
            f"FAIL: {counts['FAIL']}"
        )

    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
