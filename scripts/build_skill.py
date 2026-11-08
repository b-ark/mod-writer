#!/usr/bin/env python3
"""build_skill.py - package the mod-writer skill as a ZIP for the Claude app (claude.ai / desktop).

The ZIP holds one folder, mod-writer/, with SKILL.md, reference/ and scripts/check.py. In the app,
check.py finds reference/ next to its own folder, so nothing is rewritten.

    python scripts/build_skill.py            # -> dist/mod-writer.zip
    python scripts/build_skill.py --out x.zip

Upload the ZIP in the Claude app under Settings > Capabilities > Skills (code execution must be on).
Rebuild and upload again after changing SKILL.md, reference/ or check.py.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".claude" / "skills" / "mod-writer"
CHECKER = ROOT / "scripts" / "check.py"
NAME = "mod-writer"


def skill_files() -> list[tuple[Path, str]]:
    """(source file, path inside the ZIP) for every file of the packaged skill."""
    files = [(p, f"{NAME}/{p.relative_to(SKILL).as_posix()}")
             for p in sorted(SKILL.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts]
    files.append((CHECKER, f"{NAME}/scripts/check.py"))
    return files


def build(out: Path) -> list[str]:
    if not (SKILL / "SKILL.md").exists():
        raise FileNotFoundError(f"{SKILL / 'SKILL.md'} not found")
    out.parent.mkdir(parents=True, exist_ok=True)
    names = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in skill_files():
            z.write(src, arc)
            names.append(arc)
    return names


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Package the mod-writer skill as a ZIP for the Claude app.")
    p.add_argument("--out", type=Path, default=ROOT / "dist" / f"{NAME}.zip")
    a = p.parse_args(argv)
    names = build(a.out)
    print(f"{a.out}: {len(names)} files")
    for n in names:
        print(f"  {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
