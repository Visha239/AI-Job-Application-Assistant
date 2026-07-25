from __future__ import annotations

from pathlib import Path
import tempfile

from scripts.cleanup_project import discover_cleanup_targets
from scripts.project_health_check import (
    check_private_gitignore,
    check_required_paths,
    check_requirements_encoding,
)
from scripts.run_regression_suite import run_suite


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        required = [
            "dashboard.py",
            "app/services/example.py",
        ]

        (root / "app/services").mkdir(
            parents=True
        )
        (root / "dashboard.py").write_text(
            "print('ok')",
            encoding="utf-8",
        )
        (
            root
            / "app/services/example.py"
        ).write_text(
            "VALUE = 1",
            encoding="utf-8",
        )
        (root / "requirements.txt").write_text(
            "streamlit\npandas\n",
            encoding="utf-8",
        )
        (root / ".gitignore").write_text(
            ".env\n*.db\nexports/\ndata/application_queue.json\n",
            encoding="utf-8",
        )

        required_results = check_required_paths(
            root,
            required,
        )
        assert all(
            item.status == "PASS"
            for item in required_results
        )

        encoding_result = check_requirements_encoding(
            root
        )
        assert encoding_result[0].status == "PASS"

        private_results = check_private_gitignore(
            root,
            [
                ".env",
                "app/database/careerpilot.db",
                "exports",
                "data/application_queue.json",
            ],
        )
        assert all(
            item.status == "PASS"
            for item in private_results
        )

        cache_dir = root / "app/__pycache__"
        cache_dir.mkdir()
        (cache_dir / "example.pyc").write_bytes(
            b"cache"
        )
        (root / "debug.log").write_text(
            "debug",
            encoding="utf-8",
        )

        targets = discover_cleanup_targets(
            root
        )
        relative_targets = {
            path.relative_to(root).as_posix()
            for path in targets
        }

        assert "app/__pycache__" in relative_targets
        assert "debug.log" in relative_targets

        test_package = root / "sample_tests"
        test_package.mkdir()
        (test_package / "__init__.py").write_text(
            "",
            encoding="utf-8",
        )
        (test_package / "passing_test.py").write_text(
            "print('SAMPLE TEST PASSED')",
            encoding="utf-8",
        )

        suite = run_suite(
            ["sample_tests.passing_test"],
            root=root,
            timeout_seconds=30,
        )

        assert suite["passed"] is True
        assert suite["counts"]["PASS"] == 1

        print("=" * 70)
        print(
            "CAREERPILOT SPRINT 14 "
            "PRODUCTION READINESS TEST"
        )
        print("=" * 70)
        print("Required paths:", len(required_results))
        print("Private paths:", len(private_results))
        print("Cleanup targets:", len(targets))
        print("Regression tests:", suite["counts"]["PASS"])
        print(
            "\nSPRINT 14 PRODUCTION READINESS TEST PASSED"
        )


if __name__ == "__main__":
    main()
