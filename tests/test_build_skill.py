"""The packaged skill (for the Claude app) is complete and its check.py works without the repo."""

import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_skill  # noqa: E402


def test_zip_layout(tmp_path):
    names = set(build_skill.build(tmp_path / "mod-writer.zip"))
    assert {"mod-writer/SKILL.md", "mod-writer/scripts/check.py",
            "mod-writer/reference/brand.md", "mod-writer/reference/angles.md",
            "mod-writer/reference/flow.md"} <= names
    assert not any("hooks_library" in n for n in names)
    assert all(n.startswith("mod-writer/") for n in names)


def test_packaged_checker_runs_standalone(tmp_path):
    zip_path = tmp_path / "mod-writer.zip"
    build_skill.build(zip_path)
    unpacked = tmp_path / "app"
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(unpacked)

    # a run outside the repo: the unpacked checker works on its own
    run = tmp_path / "work" / "B01-run"
    run.mkdir(parents=True)
    source = json.loads((ROOT / "data" / "winner_source.json").read_text(encoding="utf-8"))
    hook = {"on_screen": "Gone", "shot": "S01"}
    candidates = {"body_id": "B01", "source": source, "variants": [
        {"variant_id": "B01-V01", "changes": {"hook": {**hook, "vo": "My dryer runs a sock black market."}}},
        {"variant_id": "B01-V02", "changes": {"hook": {**hook, "vo": "Socks vanish.", "shot": "S12"}}},
    ]}
    (run / "candidates.json").write_text(json.dumps(candidates), encoding="utf-8")

    result = subprocess.run([sys.executable, "-I", str(unpacked / "mod-writer" / "scripts" / "check.py"),
                             str(run / "candidates.json"), "--out", str(run)],
                            cwd=tmp_path / "work", capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    assert summary["violations"] == {"SHOT": 1}
    assert summary["passed"] == 1
