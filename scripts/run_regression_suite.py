from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_TEST_MODULES = [
    "tests.sprint3_application_assistant_test",
    "tests.sprint4_application_copilot_test",
    "tests.sprint5_recruiter_outreach_test",
    "tests.sprint6_shared_context_test",
    "tests.sprint7_auto_apply_assistant_test",
    "tests.sprint8_application_crm_test",
    "tests.sprint9_career_dashboard_test",
    "tests.sprint10_career_coach_test",
    "tests.sprint11_resume_intelligence_test",
    "tests.sprint13_one_click_optimizer_test",
    "tests.sprint14_production_readiness_test",
]


@dataclass
class TestResult:
    module: str
    status: str
    seconds: float
    output: str


def run_test_module(
    module: str,
    *,
    root: Path = PROJECT_ROOT,
    timeout_seconds: int = 180,
) -> TestResult:
    start = time.perf_counter()

    try:
        completed = subprocess.run(
            [sys.executable, "-m", module],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        output = (
            (completed.stdout or "")
            + (completed.stderr or "")
        ).strip()
        status = "PASS" if completed.returncode == 0 else "FAIL"

    except subprocess.TimeoutExpired as exc:
        output = (
            f"Timed out after {timeout_seconds} seconds.\n"
            f"{exc.stdout or ''}\n{exc.stderr or ''}"
        ).strip()
        status = "TIMEOUT"

    return TestResult(
        module=module,
        status=status,
        seconds=round(
            time.perf_counter() - start,
            2,
        ),
        output=output,
    )


def run_suite(
    modules: list[str],
    *,
    root: Path = PROJECT_ROOT,
    stop_on_failure: bool = False,
    timeout_seconds: int = 180,
) -> dict:
    results: list[TestResult] = []

    for module in modules:
        print(f"\nRunning {module} ...")
        result = run_test_module(
            module,
            root=root,
            timeout_seconds=timeout_seconds,
        )
        results.append(result)

        print(
            f"{result.status}: {module} "
            f"({result.seconds}s)"
        )

        if result.status != "PASS" and stop_on_failure:
            break

    counts = {
        "PASS": sum(item.status == "PASS" for item in results),
        "FAIL": sum(item.status == "FAIL" for item in results),
        "TIMEOUT": sum(item.status == "TIMEOUT" for item in results),
    }

    return {
        "project_root": str(root),
        "counts": counts,
        "results": [asdict(item) for item in results],
        "passed": counts["FAIL"] == 0 and counts["TIMEOUT"] == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run CareerPilot regression tests."
    )
    parser.add_argument(
        "modules",
        nargs="*",
        help="Optional test modules; defaults to the stable sprint suite",
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
    )
    parser.add_argument(
        "--report",
        default="exports/test_reports/regression_report.json",
    )
    args = parser.parse_args()

    modules = args.modules or DEFAULT_TEST_MODULES
    report = run_suite(
        modules,
        stop_on_failure=args.stop_on_failure,
        timeout_seconds=args.timeout,
    )

    report_path = PROJECT_ROOT / args.report
    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print("CAREERPILOT REGRESSION SUMMARY")
    print("=" * 72)
    print(
        f"PASS: {report['counts']['PASS']} | "
        f"FAIL: {report['counts']['FAIL']} | "
        f"TIMEOUT: {report['counts']['TIMEOUT']}"
    )
    print(f"Report: {report_path}")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
