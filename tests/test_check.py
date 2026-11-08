"""Unit tests for scripts/check.py: one block per rule, plus input formats and outputs."""

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check  # noqa: E402

SOURCE = json.loads((ROOT / "data" / "winner_source.json").read_text(encoding="utf-8"))
GOOD_HOOK = {"vo": "My dryer ate another sock today.", "on_screen": "Dryer: 1, me: 0", "shot": "S01"}


def run(tmp_path, variants, name="candidates.json"):
    """Write a candidates.json with the B01 source and the given variants, return {variant_id: codes}."""
    path = tmp_path / name
    path.write_text(json.dumps({"body_id": "B01", "source": SOURCE, "variants": variants}), encoding="utf-8")
    result, summary = check.check_file(path)
    return {v.variant_id: {c for c, _ in v.reasons} for v in result}, result, summary


def hook_variant(vid, **hook):
    return {"variant_id": vid, "angle": "test", "changes": {"hook": {**GOOD_HOOK, **hook}}}


def test_clean_variant_passes(tmp_path):
    codes, _, _ = run(tmp_path, [hook_variant("V1")])
    assert codes["V1"] == set()


# ---- on-screen text <= 5 words in any scene
@pytest.mark.parametrize("text,ok", [("One two three four five", True), ("One two three four five six", False)])
def test_onscreen_length_hook(tmp_path, text, ok):
    codes, _, _ = run(tmp_path, [hook_variant("V1", on_screen=text)])
    assert ("ONSCREEN_LEN" not in codes["V1"]) is ok


def test_onscreen_length_in_body_scene(tmp_path):
    v = {"variant_id": "V1", "changes": {"scene_3": {"on_screen": "They stay together in every wash"}}}
    codes, _, _ = run(tmp_path, [v])
    assert codes["V1"] == {"ONSCREEN_LEN"}


def test_punctuation_is_not_a_word(tmp_path):
    codes, _, _ = run(tmp_path, [hook_variant("V1", on_screen="Gone - again - and again")])
    assert codes["V1"] == set()


# ---- banned words everywhere
@pytest.mark.parametrize("segment,text", [
    ("hook", "Lose socks? Not forever."),
    ("scene_1", "Guaranteed pairs"),
    ("cta", "100% pairs"),
    ("cta", "Pairs 100 percent"),
])
def test_banned_words_everywhere(tmp_path, segment, text):
    changes = {segment: {"on_screen": text}}
    if segment == "hook":
        changes = {"hook": {**GOOD_HOOK, "on_screen": text}}
    codes, _, _ = run(tmp_path, [{"variant_id": "V1", "changes": changes}])
    assert "BANNED" in codes["V1"]


# ---- price only in the CTA
def test_price_allowed_in_cta(tmp_path):
    codes, _, _ = run(tmp_path, [{"variant_id": "V1", "changes": {"cta": {"on_screen": "Just $29 today"}}}])
    assert codes["V1"] == set()


@pytest.mark.parametrize("segment,text", [("hook", "Five pairs, $29"), ("scene_4", "Only 29 dollars")])
def test_price_rejected_outside_cta(tmp_path, segment, text):
    changes = {"hook": {**GOOD_HOOK, "on_screen": text}} if segment == "hook" else {segment: {"on_screen": text}}
    codes, _, _ = run(tmp_path, [{"variant_id": "V1", "changes": changes}])
    assert "PRICE" in codes["V1"]


# ---- product reveal forbidden only in the hook
def test_reveal_rejected_in_hook(tmp_path):
    codes, _, _ = run(tmp_path, [hook_variant("V1", vo="Magnetic socks changed my laundry.")])
    assert codes["V1"] == {"REVEAL"}


def test_reveal_allowed_in_body(tmp_path):
    codes, _, _ = run(tmp_path, [{"variant_id": "V1", "changes": {"scene_2": {"on_screen": "One tiny click"}}}])
    assert codes["V1"] == set()


# ---- VO length
@pytest.mark.parametrize("vo,ok", [
    ("One two three four five six seven eight.", True),
    ("One two three four five six seven eight nine.", False),
])
def test_hook_vo_max_8_words(tmp_path, vo, ok):
    codes, _, _ = run(tmp_path, [hook_variant("V1", vo=vo)])
    assert ("HOOK_VO_LEN" not in codes["V1"]) is ok


def test_scene_vo_not_longer_than_original(tmp_path):
    # original scene_3 VO has 12 words
    short = {"variant_id": "V1", "changes": {"scene_3": {"vo": "In the wash as a pair, out as a pair."}}}
    long = {"variant_id": "V2", "changes": {"scene_3": {"vo": "They go into the wash as a pair and they come out as a pair."}}}
    codes, result, _ = run(tmp_path, [short, long])
    assert codes["V1"] == set()
    assert codes["V2"] == {"SCENE_VO_LEN"}


def test_body_vo_change_is_marked_for_rerecord(tmp_path):
    v = {"variant_id": "V1", "changes": {"scene_3": {"vo": "In the wash as a pair, out as a pair."}}}
    _, result, _ = run(tmp_path, [v, hook_variant("V2")])
    flags = {r.variant_id: r.vo_rerecord for r in result}
    assert flags == {"V1": True, "V2": False}


# ---- shots only from the source script (B01 has S01-S06), or marked NEW
@pytest.mark.parametrize("shot,ok", [("S02", True), ("S06", True), ("s05", True), ("S07", False), ("S12", False)])
def test_shots_from_source_script(tmp_path, shot, ok):
    codes, _, _ = run(tmp_path, [hook_variant("V1", shot=shot)])
    assert ("SHOT" not in codes["V1"]) is ok


def test_new_shot_passes_and_is_marked(tmp_path):
    codes, result, summary = run(tmp_path, [
        hook_variant("V1", shot="NEW: slow push into a dark dryer drum"), hook_variant("V2", vo="Laundry day again.")])
    assert codes == {"V1": set(), "V2": set()}
    by_id = {v.variant_id: v for v in result}
    assert by_id["V1"].new_footage == ["hook: slow push into a dark dryer drum"]
    assert by_id["V2"].new_footage == []
    assert summary["new_footage"] == 1
    assert check.passed_row(by_id["V1"])["new_footage"] == "New footage needed - hook: slow push into a dark dryer drum"


@pytest.mark.parametrize("shot", ["NEW", "new:", "NEW - "])
def test_new_shot_needs_description(tmp_path, shot):
    codes, _, _ = run(tmp_path, [hook_variant("V1", shot=shot)])
    assert codes["V1"] == {"SHOT"}


# ---- repeats inside the set
def test_duplicate_inside_set(tmp_path):
    a = hook_variant("V1", vo="My dryer ate another sock today.")
    b = hook_variant("V2", vo="My dryer ate another sock today!")
    codes, _, _ = run(tmp_path, [a, b])
    assert codes["V1"] == set()
    assert codes["V2"] == {"DUP_SET"}


def test_duplicate_of_rejected_variant_is_not_counted(tmp_path):
    a = hook_variant("V1", vo="My dryer ate another sock today.", shot="S99")   # rejected for SHOT
    b = hook_variant("V2", vo="My dryer ate another sock today.")               # regenerated fix
    codes, _, _ = run(tmp_path, [a, b])
    assert codes == {"V1": {"SHOT"}, "V2": set()}




# ---- ids
def test_missing_ids_rejected(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"source": SOURCE | {"body_id": ""}, "variants": [
        {"changes": {"hook": GOOD_HOOK}}]}), encoding="utf-8")
    result, _ = check.check_file(path, None)
    assert {c for c, _ in result[0].reasons} == {"MISSING_ID"}


def test_duplicate_variant_id_rejected(tmp_path):
    codes_list = run(tmp_path, [hook_variant("V1"), hook_variant("V1", vo="Another totally new line here.")])[1]
    assert all("DUP_ID" in {c for c, _ in v.reasons} for v in codes_list)


def test_no_change_rejected(tmp_path):
    codes, _, _ = run(tmp_path, [{"variant_id": "V1", "changes": {"hook": dict(SOURCE["segments"][0])}}])
    assert codes["V1"] == {"NO_CHANGE"}


# ---- input formats and outputs
def test_csv_with_source_matches_json(tmp_path):
    variants = [
        hook_variant("V1"),
        hook_variant("V2", vo="A tiny magnet fixed my laundry."),
        {"variant_id": "V3", "changes": {"scene_3": {"vo": "They go into the wash as a pair and they come out as a pair."}}},
    ]
    json_codes, _, _ = run(tmp_path, variants)

    csv_path = tmp_path / "gen.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "body_id", "segment", "vo", "on_screen", "shot"])
        for v in variants:
            for seg, vals in v["changes"].items():
                w.writerow([v["variant_id"], "B01", seg, vals.get("vo", ""), vals.get("on_screen", ""), vals.get("shot", "")])
    # empty cells in a CSV mean "not given", so they keep the source value
    result, _ = check.check_file(csv_path, ROOT / "data" / "winner_source.json")
    assert {v.variant_id: {c for c, _ in v.reasons} for v in result} == json_codes


def test_csv_without_source_checks_text_not_shots(tmp_path):
    csv_path = tmp_path / "atria.csv"
    csv_path.write_text("variant_id,body_id,segment,vo,on_screen,shot\n"
                        "A1,B01,hook,Where do my socks keep going?,Gone again,S02\n"
                        "A2,B01,hook,Where do my socks keep hiding forever?,Lost again,S20\n", encoding="utf-8")
    result, summary = check.check_file(csv_path, None)
    # without the original script there is no list of shots, so S20 is not judged; the text still is
    assert [{c for c, _ in v.reasons} for v in result] == [set(), {"BANNED"}]
    assert summary["by_generator"] == {"atria": {"total": 2, "passed": 1}}
    assert any("shots" in w for w in summary["warnings"])


def test_cli_writes_all_outputs(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"body_id": "B01", "source": SOURCE, "variants": [
        hook_variant("B01-V01"), hook_variant("B01-V02", shot="S42")]}), encoding="utf-8")
    out = tmp_path / "out"
    assert check.main([str(path), "--out", str(out)]) == 0
    for name in ("passed.csv", "passed.md", "rejected.csv", "rejected.md", "summary.json"):
        assert (out / name).exists()
    passed = list(csv.DictReader((out / "passed.csv").open(encoding="utf-8-sig")))
    rejected = list(csv.DictReader((out / "rejected.csv").open(encoding="utf-8-sig")))
    assert [r["variant_id"] for r in passed] == ["B01-V01"]
    assert passed[0]["body_id"] == "B01"
    assert rejected[0]["codes"] == "SHOT"


def test_cli_bad_input_returns_error(tmp_path):
    bad = tmp_path / "x.txt"
    bad.write_text("hello", encoding="utf-8")
    assert check.main([str(bad), "--out", str(tmp_path / "o")]) == 2


# ---- edits of an existing variant: new ID + "replaces"
def edit_of(vid, parent, **hook):
    return {**hook_variant(vid, **hook), "replaces": parent}


def test_edit_is_not_a_duplicate_of_its_parent_and_supersedes_it(tmp_path):
    codes, result, summary = run(tmp_path, [
        hook_variant("V04", on_screen="All singles. No pairs."),
        edit_of("V04-e1", "V04", on_screen="All singles."),
    ])
    assert codes == {"V04": set(), "V04-e1": set()}
    by_id = {v.variant_id: v for v in result}
    assert by_id["V04"].superseded_by == "V04-e1"
    assert summary["passed"] == 1 and summary["superseded"] == 1 and summary["rejected"] == 0


def test_edit_still_duplicate_of_another_variant(tmp_path):
    codes, _, _ = run(tmp_path, [
        hook_variant("V01", vo="Where did my other sock go?"),
        hook_variant("V02", vo="Laundry day is a sock graveyard."),
        edit_of("V02-e1", "V02", vo="Where did my other sock go?"),
    ])
    assert codes["V02-e1"] == {"DUP_SET"}


def test_rejected_edit_keeps_the_parent(tmp_path):
    codes, result, summary = run(tmp_path, [
        hook_variant("V04"),
        edit_of("V04-e1", "V04", on_screen="Gone forever"),
    ])
    assert codes["V04-e1"] == {"BANNED"}
    assert not {v.variant_id: v for v in result}["V04"].superseded_by
    assert summary["passed"] == 1 and summary["superseded"] == 0


def test_edit_chain(tmp_path):
    codes, result, summary = run(tmp_path, [
        hook_variant("V04", on_screen="All singles. No pairs."),
        edit_of("V04-e1", "V04", on_screen="All singles."),
        edit_of("V04-e2", "V04-e1", on_screen="Singles only."),
    ])
    assert all(c == set() for c in codes.values())
    assert summary["passed"] == 1 and summary["superseded"] == 2


def test_replaces_unknown_id(tmp_path):
    codes, _, _ = run(tmp_path, [edit_of("V09-e1", "V09")])
    assert codes["V09-e1"] == {"BAD_REPLACES"}


def test_superseded_listed_in_passed_md(tmp_path):
    _, result, summary = run(tmp_path, [hook_variant("V04"), edit_of("V04-e1", "V04", shot="S02")])
    out = tmp_path / "out"
    check.write_outputs(result, out, summary)
    with (out / "passed.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert [(r["variant_id"], r["replaces"]) for r in rows] == [("V04-e1", "V04")]
    assert "## Replaced by edits (do not use)" in (out / "passed.md").read_text(encoding="utf-8")


def test_passed_has_a_column_per_changed_scene_field(tmp_path):
    variants = [
        {"variant_id": "V1", "changes": {"hook": GOOD_HOOK, "scene_3": {"on_screen": "Still a pair"},
                                         "cta": {"on_screen": "Quiz: 5 pairs, $29"}}},
        {"variant_id": "V2", "changes": {"hook": {**GOOD_HOOK, "vo": "Laundry day again."},
                                         "scene_1": {"vo": "One more sock vanishes every wash."}}},
    ]
    _, result, summary = run(tmp_path, variants)
    out = tmp_path / "out"
    check.write_outputs(result, out, summary)
    with (out / "passed.csv").open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = {r["variant_id"]: r for r in reader}
        cols = reader.fieldnames
    assert cols[cols.index("hook_shot") + 1:] == ["scene_1_vo", "scene_3_on_screen", "cta_on_screen",
                                                  "vo_rerecord", "new_footage", "flow"]
    assert rows["V1"]["scene_3_on_screen"] == "Still a pair" and rows["V1"]["scene_1_vo"] == ""
    assert rows["V2"]["scene_1_vo"] == "One more sock vanishes every wash."
    assert rows["V2"]["vo_rerecord"] == "VO re-record needed"


def test_hook_only_set_has_no_scene_columns(tmp_path):
    _, result, summary = run(tmp_path, [hook_variant("V1")])
    out = tmp_path / "out"
    check.write_outputs(result, out, summary)
    header = (out / "passed.csv").read_text(encoding="utf-8-sig").splitlines()[0]
    assert header == ",".join(check.BASE_COLS + check.FLAG_COLS)


# ---- flow review: a separate reviewer's verdicts in flow.json
def write_flow(tmp_path, verdicts):
    path = tmp_path / "flow.json"
    path.write_text(json.dumps({"reviewer": "test", "verdicts": verdicts}), encoding="utf-8")
    return path


def run_flow(tmp_path, variants, verdicts):
    cand = tmp_path / "candidates.json"
    cand.write_text(json.dumps({"body_id": "B01", "source": SOURCE, "variants": variants}), encoding="utf-8")
    result, summary = check.check_file(cand, None, write_flow(tmp_path, verdicts))
    return {v.variant_id: {c for c, _ in v.reasons} for v in result}, result, summary


def test_flow_break_rejects_and_ok_passes(tmp_path):
    variants = [hook_variant("V1"), hook_variant("V2", vo="Laundry day. Again.")]
    codes, result, summary = run_flow(tmp_path, variants, [
        {"variant_id": "V1", "verdict": "ok"},
        {"variant_id": "V2", "verdict": "break", "reason": "dangling join"}])
    assert codes == {"V1": set(), "V2": {"FLOW"}}
    assert dict(next(v for v in result if v.variant_id == "V2").reasons)["FLOW"] == "dangling join"
    assert summary["flow"]["ok"] == 1 and summary["flow"]["break"] == 1 and summary["flow"]["unreviewed"] == []


def test_flow_broken_variant_does_not_block_a_duplicate(tmp_path):
    variants = [hook_variant("V1"), hook_variant("V2")]
    codes, _, _ = run_flow(tmp_path, variants, [{"variant_id": "V1", "verdict": "break"},
                                                {"variant_id": "V2", "verdict": "ok"}])
    assert codes == {"V1": {"FLOW"}, "V2": set()}


def test_flow_missing_verdict_is_a_warning_not_a_rejection(tmp_path):
    codes, _, summary = run_flow(tmp_path, [hook_variant("V1"), hook_variant("V2", vo="Laundry day. Again.")],
                                 [{"variant_id": "V1", "verdict": "ok"}, {"variant_id": "X9", "verdict": "ok"},
                                  {"variant_id": "V1", "verdict": "maybe"}])
    assert codes["V2"] == set()
    assert summary["flow"]["unreviewed"] == ["V2"]
    joined = " ".join(summary["warnings"])
    assert "not reviewed for 1 variant " in joined and "X9" in joined and "skipped" in joined


def test_no_flow_file_warns(tmp_path):
    _, _, summary = run(tmp_path, [hook_variant("V1")])
    assert any("no flow.json" in w for w in summary["warnings"])


def test_cli_picks_up_flow_json_next_to_input(tmp_path):
    cand = tmp_path / "candidates.json"
    cand.write_text(json.dumps({"body_id": "B01", "source": SOURCE,
                                "variants": [hook_variant("V1"), hook_variant("V2", vo="Laundry day. Again.")]}),
                    encoding="utf-8")
    write_flow(tmp_path, [{"variant_id": "V1", "verdict": "break", "reason": "contradiction"}])
    out = tmp_path / "out"
    assert check.main([str(cand), "--out", str(out)]) == 0
    assert "FLOW" in (out / "rejected.csv").read_text(encoding="utf-8-sig")
    review = (out / "flow_review.md").read_text(encoding="utf-8")
    assert "## V2" in review and "## V1" not in review       # only variants still waiting for a verdict
    assert "**Laundry day. Again.**" in review and "Read aloud: Laundry day. Again. / " in review


def test_new_footage_over_a_quarter_warns(tmp_path):
    hooks = ["Laundry day. Again.", "Where did it go?", "Odd socks everywhere.", "My dryer is hungry."]
    variants = [hook_variant(f"V{i}", vo=t, on_screen=f"Text {i}") for i, t in enumerate(hooks)]
    variants[0]["changes"]["hook"]["shot"] = "NEW: a dark dryer drum"
    _, _, summary = run(tmp_path, variants)
    assert not any("new footage" in w for w in summary["warnings"])        # 1 of 4 = 25%: allowed
    variants[1]["changes"]["hook"]["shot"] = "NEW: sock on the stairs"
    _, _, summary = run(tmp_path, variants)
    assert any("2 of 4 generated variants need new footage" in w for w in summary["warnings"])


# ---- hook may not open on a product shot (shot_desc "(product)" in the source)
def test_hook_on_product_shot_rejected(tmp_path):
    codes, _, _ = run(tmp_path, [hook_variant("V1", shot="S06"), hook_variant("V2", shot="S02", vo="Odd socks again.")])
    assert codes == {"V1": {"HOOK_SHOT"}, "V2": set()}


def test_product_shot_allowed_in_body(tmp_path):
    codes, _, _ = run(tmp_path, [{"variant_id": "V1", "changes": {"scene_1": {"shot": "S04"}}}])
    assert codes["V1"] == set()


# ---- empty text
def test_empty_hook_rejected(tmp_path):
    codes, _, _ = run(tmp_path, [hook_variant("V1", vo="", on_screen="")])
    assert codes["V1"] == {"EMPTY"}


def test_cleared_scene_text_rejected(tmp_path):
    codes, _, _ = run(tmp_path, [{"variant_id": "V1", "changes": {"scene_2": {"on_screen": ""}}}])
    assert codes["V1"] == {"EMPTY"}


def test_source_with_empty_on_screen_is_not_a_warning(tmp_path):
    source = json.loads(json.dumps(SOURCE))
    source["segments"][1]["on_screen"] = ""
    path = tmp_path / "candidates.json"
    path.write_text(json.dumps({"body_id": "B01", "source": source, "variants": [hook_variant("V1")]}), encoding="utf-8")
    _, summary = check.check_file(path)
    assert not any("EMPTY" in w for w in summary["warnings"])


# ---- shots described in words (external generators) are new footage, not a rejection
def test_shot_in_words_is_new_footage(tmp_path):
    codes, result, _ = run(tmp_path, [hook_variant("V1", shot="socks scattered on the bed")])
    assert codes["V1"] == set()
    assert result[0].new_footage == ["hook: socks scattered on the bed"]


def test_shot_in_words_from_csv(tmp_path):
    path = tmp_path / "atria.csv"
    path.write_text("variant_id,body_id,segment,vo,on_screen,shot\n"
                    "AT-1,B01,hook,Laundry day. Again.,Again?,woman holding one sock\n"
                    "AT-2,B01,hook,Where did it go?,Gone,S14\n", encoding="utf-8")
    variants, summary = check.check_file(path, ROOT / "data" / "winner_source.json")
    codes = {v.variant_id: {c for c, _ in v.reasons} for v in variants}
    assert codes == {"AT-1": set(), "AT-2": {"SHOT"}}
    assert summary["new_footage"] == 1


# ---- new footage share is counted over the generated batch
def test_new_footage_share_counts_rejected_variants(tmp_path):
    hooks = ["Laundry day. Again.", "Where did it go?", "Odd socks everywhere.", "My dryer is hungry."]
    variants = [hook_variant(f"V{i}", vo=t, on_screen=f"Text {i}") for i, t in enumerate(hooks)]
    variants[0]["changes"]["hook"]["shot"] = "NEW: a dark dryer drum"
    variants[3]["changes"]["hook"]["vo"] = "Magnetic socks, finally."         # rejected: 1 of 4 generated is fine
    _, _, summary = run(tmp_path, variants)
    assert summary["passed"] == 3
    assert not any("new footage" in w for w in summary["warnings"])


# ---- pending flow is marked, the tables say they are not final
def test_pending_flow_is_marked(tmp_path):
    cand = tmp_path / "candidates.json"
    cand.write_text(json.dumps({"body_id": "B01", "source": SOURCE,
                                "variants": [hook_variant("V1"), hook_variant("V2", vo="Laundry day. Again.")]}),
                    encoding="utf-8")
    write_flow(tmp_path, [{"variant_id": "V1", "verdict": "ok"}])
    out = tmp_path / "out"
    check.main([str(cand), "--out", str(out)])
    with (out / "passed.csv").open(encoding="utf-8-sig") as f:
        rows = {r["variant_id"]: r for r in csv.DictReader(f)}
    assert rows["V1"]["flow"] == "ok" and rows["V2"]["flow"] == "pending flow"
    md = (out / "passed.md").read_text(encoding="utf-8")
    assert "> Not final: 1 variant still needs the hook-to-script check." in md
    assert json.loads((out / "summary.json").read_text(encoding="utf-8"))["pending_flow"] == 1


def test_all_reviewed_is_final(tmp_path):
    cand = tmp_path / "candidates.json"
    cand.write_text(json.dumps({"body_id": "B01", "source": SOURCE, "variants": [hook_variant("V1")]}),
                    encoding="utf-8")
    write_flow(tmp_path, [{"variant_id": "V1", "verdict": "ok"}])
    out = tmp_path / "out"
    check.main([str(cand), "--out", str(out)])
    assert "Not final" not in (out / "passed.md").read_text(encoding="utf-8")


# ---- passed.md is the designer's view: only what to cut
def test_passed_md_hook_only_is_one_table(tmp_path):
    _, result, summary = run(tmp_path, [hook_variant("V1"), hook_variant("V2", vo="Laundry day. Again.",
                                                                          shot="NEW: sock on the stairs")])
    out = tmp_path / "out"
    check.write_outputs(result, out, summary, {"B01": check.parse_source(SOURCE)})
    md = (out / "passed.md").read_text(encoding="utf-8")
    assert md.startswith("# B01: 2 variants")
    assert "| ID | VO | On-screen | First shot |" in md
    assert "| V1 | My dryer ate another sock today. | Dryer: 1, me: 0 | S01 · close-up: one sock alone on the bed |" in md
    assert "## To film\n\n- V2: sock on the stairs" in md
    for noise in ("Warning", "angle", "generator", "round", "passed", "flow"):
        assert noise not in md


def test_passed_md_scene_changes_are_cards(tmp_path):
    variants = [{"variant_id": "V1", "changes": {"hook": GOOD_HOOK, "scene_3": {"on_screen": "Still a pair"},
                                                 "scene_1": {"vo": "One more sock vanishes every wash."}}}]
    _, result, summary = run(tmp_path, variants)
    out = tmp_path / "out"
    check.write_outputs(result, out, summary, {"B01": check.parse_source(SOURCE)})
    md = (out / "passed.md").read_text(encoding="utf-8")
    assert "**V1**" in md and "- Scene 3: on-screen \u201cStill a pair\u201d" in md
    assert "- Scene 1: VO \u201cOne more sock vanishes every wash.\u201d" in md
    assert "- **VO re-record needed**" in md and "| ID |" not in md


# ---- flow_review.md shows the unchanged body once, not per variant
def test_flow_review_lists_only_changes(tmp_path):
    variants = [{"variant_id": "V1", "angle": "t", "changes": {"hook": GOOD_HOOK, "scene_3": {"on_screen": "Still a pair"}}}]
    _, result, summary = run(tmp_path, variants)
    review = check.flow_review_md(result, {"B01": check.parse_source(SOURCE)}, {})
    part = review.split("## V1")[1]
    assert "| scene_1 (as original) |" in part and "**Still a pair**" in part
    assert "| scene_2" not in part and "| cta" not in part
    assert "Read aloud: My dryer ate another sock today. / Every laundry day" in part


# ---- the same shot twice in a row
def test_hook_on_the_next_scene_shot_warns(tmp_path):
    _, _, summary = run(tmp_path, [hook_variant("V1", shot="S02"), hook_variant("V2", vo="Laundry day. Again.")])
    assert any("twice in a row" in w and "V1 (S02)" in w for w in summary["warnings"])
    assert not any("V2" in w for w in summary["warnings"] if "twice" in w)


# ---- "click" as an ordinary phrase is not the reveal
@pytest.mark.parametrize("vo,reveal", [("Mom is clicking away at her laptop.", False),
                                        ("Click here for socks.", False),
                                        ("They click together in the wash.", True),
                                        ("Socks that click.", True)])
def test_click_phrases(tmp_path, vo, reveal):
    codes, _, _ = run(tmp_path, [hook_variant("V1", vo=vo)])
    assert ("REVEAL" in codes["V1"]) is reveal


def test_exit_code_is_zero_with_rejections(tmp_path):
    cand = tmp_path / "candidates.json"
    cand.write_text(json.dumps({"body_id": "B01", "source": SOURCE,
                                "variants": [hook_variant("V1", vo="Magnetic socks.")]}), encoding="utf-8")
    assert check.main([str(cand), "--out", str(tmp_path / "out")]) == 0
    assert check.main([str(tmp_path / "missing.json"), "--out", str(tmp_path / "out")]) == 2


# ---- passed.xlsx: the designer's file
def test_passed_xlsx_is_the_full_ad_per_variant(tmp_path):
    import zipfile
    import xml.etree.ElementTree as ET
    variants = [{"variant_id": "V1", "changes": {"hook": {**GOOD_HOOK, "shot": "NEW: sock on the stairs"},
                                                 "scene_3": {"on_screen": "Still a pair & more"}}},
                hook_variant("V2", vo="Laundry day. Again.")]
    _, result, summary = run(tmp_path, variants)
    out = tmp_path / "out"
    check.write_outputs(result, out, summary, {"B01": check.parse_source(SOURCE)})
    with zipfile.ZipFile(out / "passed.xlsx") as z:
        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        ET.fromstring(z.read("xl/styles.xml"))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows = [["".join(c.itertext()) for c in r.findall("m:c", ns)] for r in root.find("m:sheetData", ns)]
    assert rows[1] == ["Variant", "Part", "Picture (what is in the shot)", "Voice-over (read aloud)",
                       "On-screen text", "Note"]
    v1 = rows[2:2 + len(SOURCE["segments"])]
    assert v1[0][:2] == ["Variant 1", "Hook"]
    assert v1[0][2] == "NEW FOOTAGE, film this: sock on the stairs" and v1[0][5].startswith("New footage to film")
    assert v1[1][2] == "laundry basket full of odd socks" and v1[1][3].startswith("Every laundry day")
    assert v1[3][4] == "Still a pair & more"
    assert rows[2 + len(SOURCE["segments"])][0] == "Variant 2"
    assert not any("V1" in cell or "B01" in cell for row in rows for cell in row)
    styles = {c.get("r"): c.get("s") for r in root.find("m:sheetData", ns) for c in r.findall("m:c", ns)}
    assert styles["E6"] == str(check.X_NEW) and styles["E4"] != str(check.X_NEW)
