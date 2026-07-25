from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DIRECTORY_NAMES = {
    "__pycache__",
    ".pytest_cache",
}

FILE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.log",
}

OPTIONAL_FILES = {
    "README.txt",
    "README_FIX.txt",
    "README_FEATURE_PACK_1.md",
}

OPTIONAL_INSTALLERS_PATTERN = "install_sprint*.ps1"


def discover_cleanup_targets(
    root: Path = PROJECT_ROOT,
    *,
    include_installers: bool = False,
    include_old_readmes: bool = False,
) -> list[Path]:
    targets: set[Path] = set()

    for directory_name in DIRECTORY_NAMES:
        targets.update(
            path
            for path in root.rglob(directory_name)
            if path.is_dir()
        )

    for pattern in FILE_PATTERNS:
        targets.update(
            path
            for path in root.rglob(pattern)
            if path.is_file()
        )

    if include_installers:
        targets.update(
            path
            for path in root.glob(OPTIONAL_INSTALLERS_PATTERN)
            if path.is_file()
        )

    if include_old_readmes:
        targets.update(
            root / relative
            for relative in OPTIONAL_FILES
            if (root / relative).exists()
        )

    return sorted(
        targets,
        key=lambda path: (
            len(path.parts),
            str(path),
        ),
        reverse=True,
    )


def remove_targets(
    targets: list[Path],
) -> tuple[int, int]:
    removed = 0
    failed = 0

    for target in targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            removed += 1
        except OSError:
            failed += 1

    return removed, failed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely clean generated CareerPilot files."
    )
    parser.add_argument(
        "--root",
        default=str(PROJECT_ROOT),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually remove files. Default is dry-run.",
    )
    parser.add_argument(
        "--include-installers",
        action="store_true",
    )
    parser.add_argument(
        "--include-old-readmes",
        action="store_true",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    targets = discover_cleanup_targets(
        root,
        include_installers=args.include_installers,
        include_old_readmes=args.include_old_readmes,
    )

    print("=" * 72)
    print(
        "CAREERPILOT CLEANUP "
        + ("APPLY" if args.apply else "DRY RUN")
    )
    print("=" * 72)

    for target in targets:
        print(target.relative_to(root))

    print("-" * 72)
    print(f"Targets: {len(targets)}")

    if not args.apply:
        print(
            "Nothing was deleted. Run again with --apply after reviewing."
        )
        return 0

    removed, failed = remove_targets(targets)
    print(f"Removed: {removed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
