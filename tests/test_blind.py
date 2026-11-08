"""check.py must find, on its own, the same violations a person found by hand in the blind test
(Atria vs Claude baseline, 24 hooks on body B01): shots that are not in the B01 script for Atria, product reveal
in the hook for Claude, plus the few other defects marked in `manual_violation`."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check  # noqa: E402

BLIND = ROOT / "data" / "blind_test_labeled.csv"


def manual_labels() -> dict[str, set[str]]:
    with BLIND.open(encoding="utf-8-sig", newline="") as f:
        return {r["variant_id"]: {c for c in r["manual_violation"].split(";") if c} for r in csv.DictReader(f)}


def found() -> dict[str, set[str]]:
    variants, _ = check.check_file(BLIND, ROOT / "data" / "winner_source.json")
    return {v.variant_id: {c for c, _ in v.reasons} for v in variants}


def test_same_violations_as_manual_review():
    assert found() == manual_labels()


def test_atria_shots_outside_script():
    auto = found()
    atria_shot = {vid for vid, codes in auto.items() if vid.startswith("AT-") and "SHOT" in codes}
    assert atria_shot == {"AT-02", "AT-05", "AT-07", "AT-11"}


def test_claude_reveals_product_in_hook():
    auto = found()
    claude_reveal = {vid for vid, codes in auto.items() if vid.startswith("CL-") and "REVEAL" in codes}
    assert claude_reveal == {"CL-01", "CL-03", "CL-06", "CL-09"}


def test_accepted_hooks_pass_the_checker():
    with BLIND.open(encoding="utf-8-sig", newline="") as f:
        accepted = {r["variant_id"] for r in csv.DictReader(f) if r["accepted"] == "1"}
    auto = found()
    assert all(auto[vid] == set() for vid in accepted)
