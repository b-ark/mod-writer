#!/usr/bin/env python3
"""check.py - validate text variations for modifications of a winning creative.

Standard library only (Python 3.10+; the project pins 3.15): runs without Claude, without network and
without access to any SockLock system.

Input (detected by file extension):
  * candidates.json written by the mod-writer skill:
      {"body_id": "B01", "generator": "mod-writer",
       "source":   {"segments": [{"segment": "hook", "vo": ..., "on_screen": ..., "shot": "S02"}, ...]},
       "variants": [{"variant_id": "B01-V01", "angle": "mystery", "round": 0,
                     "changes": {"hook": {"vo": ..., "on_screen": ..., "shot": ...},
                                 "scene_2": {"on_screen": ...}, "cta": {"on_screen": ...}}}]}
    Every variant is laid over the source script; only what it changed is checked
    (the unchanged winner is already approved). An edit of an existing variant is a new variant
    with "replaces": "<old variant_id>" and the full set of its changes. It is not a duplicate of
    the variant it replaces, and once it passes, the old one moves to "superseded" in passed.md.
    Shots: a variant may use only the shot IDs of its source script. A shot written as
    "NEW: <scene to film>", or described in words instead of an ID ("socks on the bed", as external
    generators write it), is allowed and marked "New footage needed". A hook may not open on a shot whose
    shot_desc in the source says "(product)".
  * CSV from any generator (Atria, ChatGPT, manual): one row per segment of a variant.
    Columns: variant_id, body_id, segment (hook | scene_N | cta), vo, on_screen, shot,
    optional angle, angle_note, generator, round, replaces. Extra columns are ignored. Accepted aliases:
    voiceover / voice_over / text for vo, onscreen / on_screen_text / text_on_screen for on_screen,
    shot_id / first_frame / visual for shot. An empty segment means hook; an empty cell means "not given".
    Pass --source (a script JSON) to merge the rows over the original script and compare VO length.

Hook-to-script flow (FLOW): whether a hook leads into the rest of the script is a judgement, not a rule a
script can check. check.py writes flow_review.md: the full read-through of every variant that passed the rules
and has no verdict yet. A reviewer who did not write the variants (a fresh agent, or the designer) reads it
against reference/flow.md and writes flow.json next to the input (or pass --flow):
    {"reviewer": "...", "verdicts": [{"variant_id": "B01-V01", "verdict": "ok" | "break", "reason": "..."}]}
On the next run "break" rejects the variant with code FLOW. A variant with no verdict yet passes the rules but is
marked "pending flow" in passed.csv / passed.md: the tables are not final until no variant is pending.

Exit code: 0 whenever the input was read and checked (rejections included), 2 if the input could not be read.

Output (written to --out, default ./out). Only this script writes these files:
  passed.csv, passed.md, rejected.csv, rejected.md, summary.json, flow_review.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

# ---------------------------------------------------------------- rules
MAX_ONSCREEN_WORDS = 5
MAX_HOOK_VO_WORDS = 8          # ~3 seconds of voice-over
DUP_THRESHOLD = 0.9            # difflib ratio on normalized text
MAX_NEW_FOOTAGE_SHARE = 0.25   # at most a quarter of the generated batch may need new footage (warning)
FLOW_VERDICTS = ("ok", "break")
FIELDS = ("vo", "on_screen", "shot")
TEXT_FIELDS = ("vo", "on_screen")

BANNED = {
    "guaranteed": re.compile(r"\bguarantee[ds]?\b", re.I),
    "forever": re.compile(r"\bforever\b", re.I),
    "100%": re.compile(r"\b100\s*(?:%|percent\b)", re.I),
}
PRICE = re.compile(
    r"\$\s*\d+(?:\.\d+)?"                                   # $29, $ 29, $29.99
    r"|\b\d+(?:\.\d+)?\s*(?:dollars?|bucks|usd)\b"           # 29 dollars, 29 USD
    r"|\b(?:twenty|thirty|forty|fifty)[- ]?\w*\s+(?:dollars?|bucks)\b",
    re.I,
)
# product mechanism, forbidden in the hook only; "clicking away", "click here" are ordinary phrases, not the reveal
REVEAL = re.compile(r"\bmagnet\w*|\bclick(?:s|ed|ing)?\b(?!\s+(?:away|here|through|on\b))", re.I)
NEW_SHOT = re.compile(r"^new\b\s*[:\-]?\s*(.*)$", re.I | re.S)  # "NEW: <scene to film>" = footage the script lacks
SHOT_ID = re.compile(r"[A-Z]{0,4}\d{1,4}[A-Z]?")             # S02, SH12, 3, S04B; anything else is a description

REASON_TEXT = {
    "MISSING_ID": "variant_id or body_id is missing",
    "DUP_ID": "variant_id is used twice in the input",
    "BAD_SEGMENT": "unknown segment",
    "NO_CHANGE": "variant changes nothing",
    "ONSCREEN_LEN": f"on-screen text longer than {MAX_ONSCREEN_WORDS} words",
    "BANNED": "banned word",
    "PRICE": "price outside the CTA",
    "REVEAL": "product revealed in the hook",
    "HOOK_SHOT": "hook opens on a product shot",
    "EMPTY": "a changed text is empty, or the hook has neither VO nor on-screen text",
    "HOOK_VO_LEN": f"hook VO longer than {MAX_HOOK_VO_WORDS} words",
    "SCENE_VO_LEN": "VO longer than the original line",
    "SHOT": "shot ID is not in the source script",
    "DUP_SET": "repeats another variant in this set",
    "BAD_REPLACES": "replaces a variant_id that is not in this set",
    "FLOW": "hook does not lead into the rest of the script (flow review)",
}

Segments = dict[str, dict[str, str]]   # plain alias (not `type`): keeps 3.10+ for the claude.ai sandbox


@dataclass(slots=True)
class Variant:
    variant_id: str
    body_id: str
    angle: str = ""
    angle_note: str = ""                                    # what a new angle (not in angles.md) is
    generator: str = ""
    round: int = 0
    segments: Segments = field(default_factory=dict)       # final creative after the change
    changed: dict[str, set[str]] = field(default_factory=dict)  # segment -> changed fields
    has_source: bool = False
    replaces: str = ""                                       # variant_id this one is an edit of
    superseded_by: str = ""                                  # set when a passed edit replaces this one
    reasons: list[tuple[str, str]] = field(default_factory=list)
    source_shots: frozenset[str] = frozenset()               # normalized shot texts of the source script
    flow: str = ""                                           # flow verdict: "ok", "break" or "" (not reviewed)

    def fail(self, code: str, detail: str) -> None:
        self.reasons.append((code, detail))

    def changed_items(self):
        for seg, fields in self.changed.items():
            for f in FIELDS:
                if f in fields:
                    yield seg, f, self.segments[seg].get(f, "")

    @property
    def vo_rerecord(self) -> bool:
        return any(f == "vo" and seg != "hook" for seg, f, _ in self.changed_items())

    @property
    def new_footage(self) -> list[str]:
        """Scenes to film: changed shots written as "NEW: <description>" or described in words."""
        return [f"{seg}: {scene}" for seg, f, value in self.changed_items()
                if f == "shot" and (scene := described_scene(value, self.source_shots))]


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


# ---------------------------------------------------------------- text helpers
def words(text: str) -> list[str]:
    return [t for t in text.split() if re.search(r"[A-Za-z0-9]", t)]


def norm(text: str) -> str:
    text = re.sub(r"[^a-z0-9$% ]+", " ", text.lower())
    return " ".join(text.split())


def similar(a: str, b: str) -> bool:
    a, b = norm(a), norm(b)
    if not a or not b:
        return False
    return a == b or SequenceMatcher(None, a, b).ratio() >= DUP_THRESHOLD


def segment_name(raw: str) -> str | None:
    s = raw.strip().lower()
    if s in ("hook", "cta"):
        return s
    if m := re.fullmatch(r"(?:scene|body|s)[ _-]?(\d+)", s):
        return f"scene_{int(m[1])}"
    return None


def split_shots(raw: str) -> list[str]:
    return [s.upper() for s in re.split(r"[\s,;/+]+", raw.strip()) if s]


def seg_order(seg: str) -> tuple[int, int]:
    if seg == "hook":
        return (0, 0)
    if seg == "cta":
        return (2, 0)
    return (1, int(seg.split("_")[1]))


# ---------------------------------------------------------------- reference data
def is_shot_ids(value: str) -> bool:
    tokens = split_shots(value)
    return bool(tokens) and all(SHOT_ID.fullmatch(t) for t in tokens)


def described_scene(value: str, source_shots: frozenset[str] = frozenset()) -> str:
    """The scene to film if this shot is not existing footage: "NEW: <scene>" or a description in words.
    A description that is word for word a shot of the source script is existing footage."""
    if m := NEW_SHOT.match(value):
        return m[1].strip()
    if value.strip() and not is_shot_ids(value) and norm(value) not in source_shots:
        return value.strip()
    return ""


def script_shots(source: Segments) -> set[str]:
    """Shot IDs that exist: the ones the source script itself uses."""
    return {s for vals in source.values() if is_shot_ids(vals.get("shot", ""))
            for s in split_shots(vals.get("shot", ""))}


def product_shots(source: Segments) -> set[str]:
    """Shot IDs whose shot_desc says "(product)": a hook may not open on them."""
    return {s for vals in source.values() if "(product)" in vals.get("shot_desc", "").lower()
            and is_shot_ids(vals.get("shot", "")) for s in split_shots(vals["shot"])}


def parse_source(raw: dict) -> Segments:
    segs: Segments = {}
    for item in raw.get("segments", []):
        name = segment_name(item.get("segment", ""))
        if name:
            segs[name] = {f: str(item.get(f) or "").strip() for f in (*FIELDS, "shot_desc")}
    return segs


def load_source_file(path: Path) -> dict[str, Segments]:
    """A script JSON {"body_id", "segments"} or a candidates.json (its "source" is used)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    src = data.get("source", data)
    return {str(data.get("body_id") or src.get("body_id") or "").strip(): parse_source(src)}


# ---------------------------------------------------------------- input
def apply_changes(v: Variant, source: Segments, changes: dict[str, dict]) -> None:
    v.segments = {seg: dict(vals) for seg, vals in source.items()}
    v.source_shots = frozenset(norm(vals["shot"]) for vals in source.values() if vals.get("shot"))
    for raw_seg, vals in changes.items():
        seg = segment_name(raw_seg)
        if seg is None or (v.has_source and seg not in source):
            v.fail("BAD_SEGMENT", f"segment '{raw_seg}' is not in the source script")
            continue
        target = v.segments.setdefault(seg, {f: "" for f in FIELDS})
        for f in FIELDS:
            if f not in vals:
                continue
            value = str(vals[f] or "").strip()
            original = source.get(seg, {}).get(f, "")
            if (v.has_source and value != original) or (not v.has_source and value):
                v.changed.setdefault(seg, set()).add(f)
            target[f] = value
            if f == "shot" and value != original:
                target["shot_desc"] = ""     # the source description is about the old shot
    v.segments = dict(sorted(v.segments.items(), key=lambda kv: seg_order(kv[0])))
    v.changed = dict(sorted(v.changed.items(), key=lambda kv: seg_order(kv[0])))


def load_json(path: Path) -> tuple[list[Variant], dict[str, Segments]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    source = parse_source(data.get("source", {}))
    body = str(data.get("body_id") or "").strip()
    generator = str(data.get("generator") or "mod-writer")
    variants = []
    for item in data.get("variants", []):
        v = Variant(
            variant_id=str(item.get("variant_id") or "").strip(),
            body_id=str(item.get("body_id") or body).strip(),
            angle=str(item.get("angle") or ""),
            angle_note=str(item.get("angle_note") or ""),
            generator=str(item.get("generator") or generator),
            round=int(item.get("round") or 0),
            replaces=str(item.get("replaces") or "").strip(),
            has_source=bool(source),
        )
        apply_changes(v, source, item.get("changes", {}))
        variants.append(v)
    return variants, ({body: source} if source else {})


def load_csv(path: Path, sources: dict[str, Segments]) -> list[Variant]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [{(k or "").strip().lower(): (val or "").strip() for k, val in r.items()} for r in csv.DictReader(f)]

    alias = {"vo": ("vo", "voiceover", "voice_over", "text"),
             "on_screen": ("on_screen", "onscreen", "on_screen_text", "text_on_screen"),
             "shot": ("shot", "shot_id", "first_frame", "visual")}
    grouped: dict[str, list[dict]] = {}
    for i, r in enumerate(rows, start=2):
        key = r.get("variant_id") or f"<row {i}>"
        grouped.setdefault(key, []).append(r)

    variants = []
    for key, group in grouped.items():
        first = group[0]
        body = first.get("body_id", "")
        source = sources.get(body, {})
        v = Variant(
            variant_id=first.get("variant_id", ""),
            body_id=body,
            angle=first.get("angle", ""),
            angle_note=first.get("angle_note", ""),
            generator=first.get("generator", "") or path.stem,
            round=int(first.get("round") or 0),
            replaces=first.get("replaces", ""),
            has_source=bool(source),
        )
        changes: dict[str, dict] = {}
        for r in group:
            seg = r.get("segment", "") or "hook"
            vals = {}
            for f, names in alias.items():
                for n in names:
                    if r.get(n):
                        vals[f] = r[n]
                        break
            changes.setdefault(seg, {}).update(vals)
        apply_changes(v, source, changes)
        variants.append(v)
    return variants


# ---------------------------------------------------------------- checks
def check_variant(v: Variant, shots: set[str] | None, product: set[str] | None = None) -> None:
    """shots: shot IDs of the source script; None = no source given, shots are not checked.
    product: shot IDs that show the product (from shot_desc), which a hook may not open on."""
    if not v.variant_id or not v.body_id:
        v.fail("MISSING_ID", "variant_id and body_id are required to link the variant to ad results")
    if not v.changed:
        v.fail("NO_CHANGE", "nothing differs from the source script")

    if "hook" in v.changed and not hook(v, "vo") and not hook(v, "on_screen"):
        v.fail("EMPTY", "the hook has neither VO nor on-screen text")

    for seg, f, value in v.changed_items():
        if f in TEXT_FIELDS and not value:
            v.fail("EMPTY", f"{seg} {f} is empty (the original has text here)")
        if f in TEXT_FIELDS:
            for word, rx in BANNED.items():
                if rx.search(value):
                    v.fail("BANNED", f"{seg} {f}: '{word}' in \"{value}\"")
            if seg != "cta" and (m := PRICE.search(value)):
                v.fail("PRICE", f"{seg} {f}: price '{m[0].strip()}' is allowed only in the CTA")
            if seg == "hook" and (m := REVEAL.search(value)):
                v.fail("REVEAL", f"hook {f}: '{m[0]}' reveals the product before the body does")

        if f == "on_screen" and (n := len(words(value))) > MAX_ONSCREEN_WORDS:
            v.fail("ONSCREEN_LEN", f"{seg} on-screen has {n} words (max {MAX_ONSCREEN_WORDS}): \"{value}\"")

        # VO of other scenes is compared with the original line in check_scene_vo()
        if f == "vo" and seg == "hook" and (n := len(words(value))) > MAX_HOOK_VO_WORDS:
            v.fail("HOOK_VO_LEN", f"hook VO has {n} words (max {MAX_HOOK_VO_WORDS}, ~3 s): \"{value}\"")

        if f == "shot":
            if NEW_SHOT.match(value) and not described_scene(value):
                v.fail("SHOT", f"{seg}: a NEW shot needs a description of the scene to film")
                continue
            if not value:
                v.fail("EMPTY", f"{seg} shot is empty")
                continue
            if described_scene(value, v.source_shots):
                continue           # new footage: passes, marked "New footage needed"
            if seg == "hook" and product and (hit := [s for s in split_shots(value) if s in product]):
                v.fail("HOOK_SHOT", f"hook opens on {', '.join(hit)}, a product shot; "
                                    f"open on a problem shot")
            if shots is None:
                continue
            bad = [s for s in split_shots(value) if s not in shots]
            if bad:
                v.fail("SHOT", f"{seg}: {', '.join(bad)} not in the source script "
                               f"(it has {', '.join(sorted(shots)) or 'no shots'}); "
                               f"write \"NEW: <scene>\" if this needs new footage")


def check_scene_vo(v: Variant, source: Segments) -> None:
    for seg, f, value in v.changed_items():
        if f != "vo" or seg == "hook":
            continue
        original = source.get(seg, {}).get("vo", "")
        if original and (n := len(words(value))) > (m := len(words(original))):
            v.fail("SCENE_VO_LEN", f"{seg} VO has {n} words, original line has {m}: \"{value}\"")


def fingerprint(v: Variant) -> str:
    return " ".join(value for _, f, value in v.changed_items() if f in TEXT_FIELDS)


def check_duplicates(variants: list[Variant]) -> None:
    """Runs after the other checks: a variant only counts as taken if it passed everything else."""
    kept: list[Variant] = []
    by_id = {v.variant_id: v for v in variants}
    for v in variants:
        if v.reasons:
            continue
        family = lineage(v, by_id)
        hook_changed = v.changed.get("hook", set())
        for other in kept:
            if other.variant_id in family or v.variant_id in lineage(other, by_id):
                continue   # an edit is meant to be close to the variant it replaces
            same_hook_vo = "vo" in hook_changed and "vo" in other.changed.get("hook", set()) \
                and similar(v.segments["hook"]["vo"], other.segments["hook"]["vo"])
            if same_hook_vo or similar(fingerprint(v), fingerprint(other)):
                v.fail("DUP_SET", f"near-duplicate of {other.variant_id}")
                break
        if not v.reasons:
            kept.append(v)


def lineage(v: Variant, by_id: dict[str, Variant]) -> set[str]:
    """IDs this variant edits, directly or through a chain of edits (V04 <- V04-e1 <- V04-e2)."""
    seen: set[str] = set()
    while v.replaces and v.replaces not in seen and v.replaces in by_id:
        seen.add(v.replaces)
        v = by_id[v.replaces]
    return seen


def check_ids(variants: list[Variant]) -> None:
    counts = Counter(v.variant_id for v in variants if v.variant_id)
    for v in variants:
        if counts[v.variant_id] > 1:
            v.fail("DUP_ID", f"variant_id {v.variant_id} appears {counts[v.variant_id]} times")
        if v.replaces and (v.replaces not in counts or v.replaces == v.variant_id):
            v.fail("BAD_REPLACES", f"replaces '{v.replaces}', which is not another variant in this set")


def mark_superseded(variants: list[Variant]) -> None:
    """A passed edit takes the place of the variant it replaces; a rejected edit changes nothing."""
    by_id = {v.variant_id: v for v in variants}
    for v in variants:
        if v.replaces and not v.reasons and (old := by_id.get(v.replaces)):
            old.superseded_by = v.variant_id


def load_flow(path: Path) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """flow.json -> {variant_id: (verdict, reason)}, plus warnings about entries that cannot be used."""
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("verdicts", []) if isinstance(data, dict) else data
    flow: dict[str, tuple[str, str]] = {}
    warnings: list[str] = []
    for item in items:
        vid = str(item.get("variant_id") or "").strip()
        verdict = str(item.get("verdict") or "").strip().lower()
        if not vid or verdict not in FLOW_VERDICTS:
            warnings.append(f"flow.json: entry {item!r} skipped (needs variant_id and verdict ok|break)")
            continue
        flow[vid] = (verdict, str(item.get("reason") or "").strip())
    return flow, warnings


def check_flow(variants: list[Variant], flow: dict[str, tuple[str, str]]) -> None:
    for v in variants:
        verdict, reason = flow.get(v.variant_id, ("", ""))
        v.flow = verdict
        if verdict == "break":
            v.fail("FLOW", reason or "the reviewer found that the hook does not lead into the script")


def run_checks(variants: list[Variant], sources: dict[str, Segments],
               flow: dict[str, tuple[str, str]] | None = None) -> list[Variant]:
    check_ids(variants)
    for v in variants:
        source = sources.get(v.body_id) if v.has_source else None
        check_variant(v, script_shots(source) if source else None, product_shots(source) if source else None)
        if v.has_source:
            check_scene_vo(v, sources.get(v.body_id, {}))
    check_flow(variants, flow or {})   # before duplicates: a broken variant does not take its idea
    check_duplicates(variants)
    mark_superseded(variants)
    return variants


# ---------------------------------------------------------------- output
def other_changes(v: Variant) -> str:
    return "; ".join(f"{seg} {f}: {value}" for seg, f, value in v.changed_items() if seg != "hook")


def hook(v: Variant, f: str) -> str:
    return v.segments.get("hook", {}).get(f, "")


BASE_COLS = ["variant_id", "replaces", "body_id", "generator", "round", "angle", "angle_note",
             "hook_vo", "hook_on_screen", "hook_shot"]
FLAG_COLS = ["vo_rerecord", "new_footage", "flow"]
REJECTED_COLS = BASE_COLS + ["other_changes", "codes", "reasons"]
SUPERSEDED_COLS = ["variant_id", "superseded_by", "hook_vo", "hook_on_screen", "hook_shot", "other_changes"]


def active(v: Variant) -> bool:
    """Goes to passed.csv: passed every check and was not replaced by a passed edit."""
    return not v.reasons and not v.superseded_by


def segment_columns(variants: list[Variant]) -> list[str]:
    """One column per scene/CTA field that any of these variants changes, e.g. scene_2_on_screen, cta_vo."""
    pairs = {(seg, f) for v in variants for seg, f, _ in v.changed_items() if seg != "hook"}
    return [f"{seg}_{f}" for seg, f in sorted(pairs, key=lambda p: (seg_order(p[0]), FIELDS.index(p[1])))]


def passed_cols(variants: list[Variant]) -> list[str]:
    return BASE_COLS + segment_columns(variants) + FLAG_COLS


def passed_row(v: Variant) -> dict[str, str]:
    """Scene/CTA cells hold the new text only where the variant changed it; empty = as in the original."""
    scenes = {f"{seg}_{f}": value for seg, f, value in v.changed_items() if seg != "hook"}
    return {"variant_id": v.variant_id, "replaces": v.replaces, "body_id": v.body_id, "generator": v.generator,
            "round": str(v.round), "angle": v.angle, "angle_note": v.angle_note, "hook_vo": hook(v, "vo"),
            "hook_on_screen": hook(v, "on_screen"), "hook_shot": hook(v, "shot"),
            **scenes,
            "vo_rerecord": "VO re-record needed" if v.vo_rerecord else "",
            "new_footage": "; ".join(f"New footage needed - {d}" for d in v.new_footage),
            "flow": "ok" if v.flow == "ok" else "pending flow"}


def superseded_row(v: Variant) -> dict[str, str]:
    return {"variant_id": v.variant_id, "superseded_by": v.superseded_by, "hook_vo": hook(v, "vo"),
            "hook_on_screen": hook(v, "on_screen"), "hook_shot": hook(v, "shot"),
            "other_changes": other_changes(v)}


def rejected_row(v: Variant) -> dict[str, str]:
    return {"variant_id": v.variant_id, "replaces": v.replaces, "body_id": v.body_id, "generator": v.generator,
            "round": str(v.round), "angle": v.angle, "angle_note": v.angle_note, "hook_vo": hook(v, "vo"),
            "hook_on_screen": hook(v, "on_screen"), "hook_shot": hook(v, "shot"),
            "other_changes": other_changes(v),
            "codes":";".join(dict.fromkeys(c for c, _ in v.reasons)),
            "reasons": " | ".join(d for _, d in v.reasons)}


def md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def md_table(cols: list[str], rows: list[dict[str, str]]) -> str:
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(md_cell(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join(lines)


def flow_pending(variants: list[Variant], flow: dict[str, tuple[str, str]]) -> list[Variant]:
    """Passed every rule, but nobody has judged its flow yet."""
    return [v for v in variants if active(v) and v.variant_id not in flow]


def repeated_shots(variants: list[Variant]) -> list[str]:
    """Variants whose changed hook shot is also the shot of the segment right after the hook."""
    found = []
    for v in variants:
        if "shot" not in v.changed.get("hook", set()):
            continue
        after = next((vals for seg, vals in v.segments.items() if seg != "hook"), {})
        same = set(split_shots(hook(v, "shot"))) & set(split_shots(after.get("shot", "")))
        if same and is_shot_ids(hook(v, "shot")):
            found.append(f"{v.variant_id} ({', '.join(sorted(same))})")
    return found


def summarize(variants: list[Variant], warnings: list[str],
              flow: dict[str, tuple[str, str]] | None = None, flow_file: str = "") -> dict:
    passed = [v for v in variants if active(v)]
    flow = flow or {}
    pending = [v.variant_id for v in flow_pending(variants, flow)]
    warnings = list(warnings)
    if pending:
        where = f"no verdict in {flow_file}" if flow_file else "no flow.json"
        shown = ", ".join(pending[:10]) + (f" and {len(pending) - 10} more" if len(pending) > 10 else "")
        warnings.append(f"hook-to-script flow not reviewed for {plural(len(pending), 'variant')} ({where}): "
                        f"{shown} - see flow_review.md")
    if unknown := sorted(set(flow) - {v.variant_id for v in variants}):
        warnings.append(f"flow.json has verdicts for variants that are not in the input: {', '.join(unknown)}")
    first = [v for v in variants if v.round == 0]
    batch = len(first) or len(variants)          # the batch as generated: a rejection does not shrink it
    footage = sum(bool(v.new_footage) for v in passed)
    if batch and footage > MAX_NEW_FOOTAGE_SHARE * batch:
        warnings.append(f"{footage} of {batch} generated variants need new footage "
                        f"(more than {MAX_NEW_FOOTAGE_SHARE:.0%} of the batch)")
    if repeats := repeated_shots(passed):
        warnings.append("hook on the same shot as the next scene, so one shot plays twice in a row: "
                        + ", ".join(repeats))
    by_gen: dict[str, dict[str, int]] = {}
    for v in variants:
        g = by_gen.setdefault(v.generator, {"total": 0, "passed": 0})
        g["total"] += 1
        g["passed"] += not v.reasons
    return {
        "total": len(variants),
        "passed": len(passed),
        "pending_flow": len(pending),
        "rejected": sum(bool(v.reasons) for v in variants),
        "superseded": sum(bool(v.superseded_by) for v in variants),
        "new_footage": sum(bool(v.new_footage) for v in passed),
        "first_round_total": len(first),
        "first_round_passed": sum(not v.reasons for v in first),
        "by_generator": by_gen,
        "by_round": {str(r): {"total": sum(v.round == r for v in variants),
                              "passed": sum(v.round == r and not v.reasons for v in variants)}
                     for r in sorted({v.round for v in variants})},
        "violations": dict(Counter(c for v in variants for c in dict.fromkeys(c for c, _ in v.reasons))
                           .most_common()),
        "flow": {"file": flow_file,
                 "ok": sum(flow.get(v.variant_id, ("",))[0] == "ok" for v in passed),
                 "break": sum(flow.get(v.variant_id, ("",))[0] == "break" for v in variants),
                 "unreviewed": pending},
        "warnings": warnings,
    }


def shot_descriptions(sources: dict[str, Segments]) -> dict[str, str]:
    """{"S01": "single sock out of the dryer (problem)"} from the shot_desc fields of the source scripts."""
    return {vals["shot"].upper(): vals["shot_desc"] for src in sources.values() for vals in src.values()
            if vals.get("shot") and vals.get("shot_desc")}


def flow_review_md(variants: list[Variant], sources: dict[str, Segments],
                   flow: dict[str, tuple[str, str]]) -> str:
    """Read-through of every variant that still needs a flow verdict. The original script is printed once;
    each variant shows its changed segments (in **bold**) plus the segment right after the hook, and the
    whole ad read aloud."""
    pending = flow_pending(variants, flow)
    shot_desc = shot_descriptions(sources)

    def shot(value: str) -> str:
        return f"{value} ({shot_desc[value.upper()]})" if value.upper() in shot_desc else value

    def row(seg: str, vals: dict[str, str], bold: set[str], note: str = "") -> str:
        vals = {**vals, "shot": shot(vals.get("shot", ""))}
        cells = [f"**{vals[f]}**" if f in bold and vals.get(f) else vals.get(f, "") for f in FIELDS]
        return "| " + " | ".join(md_cell(c) for c in [seg + note, *cells]) + " |"

    head = ["| segment | VO | on-screen | shot |", "|---|---|---|---|"]
    lines = ["# Flow review", "",
             f"{plural(len(pending), 'variant')} passed the rules and have no flow verdict yet.",
             "Judge each one by reference/flow.md and add its verdict to flow.json next to candidates.json:", "",
             '`{"reviewer": "...", "verdicts": [{"variant_id": "...", "verdict": "ok" | "break", "reason": "..."}]}`',
             "", "Each variant lists only what it changes (**bold**) and the segment right after the hook; every",
             "other segment is as in the original script below. \"Read aloud\" is the whole ad.", ""]
    for body, src in sources.items():
        lines += [f"## Original script {body}", "", *head, *(row(seg, vals, set()) for seg, vals in src.items()),
                  "", "Read aloud: " + " / ".join(s["vo"] for s in src.values() if s.get("vo")), ""]
    for v in pending:
        note = f" ({v.angle_note})" if v.angle_note else ""
        after = next((seg for seg in v.segments if seg != "hook"), "")
        lines += [f"## {v.variant_id} - {v.angle or 'no angle'}{note}", "", *head]
        for seg, vals in v.segments.items():
            if seg in v.changed:
                lines.append(row(seg, vals, v.changed[seg]))
            elif seg == after or seg == "hook":
                lines.append(row(seg, vals, set(), " (as original)"))
        lines += ["", "Read aloud: " + " / ".join(s["vo"] for s in v.segments.values() if s.get("vo")), ""]
    return "\n".join(lines)


MD_NOTE_COLS = ("vo_rerecord", "new_footage", "flow")


def md_view(cols: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]], str]:
    """passed.md is read in a chat: drop columns that are empty everywhere, move the ones that are the same in
    every row (body_id, generator, round) into a line above the table, merge the flags into one "notes"."""
    same = [c for c in ("body_id", "generator", "round") if rows and len({r.get(c, "") for r in rows}) == 1]
    line = ", ".join(f"{c}: {rows[0][c]}" for c in same if rows[0].get(c))
    rows = [{**r, "notes": "; ".join(x for c in MD_NOTE_COLS if (x := r.get(c, "")) and x != "ok")}
            for r in rows]
    keep = [c for c in cols if c not in same and c not in MD_NOTE_COLS] + ["notes"]
    keep = [c for c in keep if c == "variant_id" or any(r.get(c) for r in rows)]
    return keep, rows, line


def write_outputs(variants: list[Variant], out: Path, summary: dict,
                  sources: dict[str, Segments] | None = None,
                  flow: dict[str, tuple[str, str]] | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    kept = [v for v in variants if active(v)]
    cols_passed = passed_cols(kept)
    passed = [passed_row(v) for v in kept]
    rejected = [rejected_row(v) for v in variants if v.reasons]
    superseded = [superseded_row(v) for v in variants if v.superseded_by]

    for name, cols, rows in (("passed", cols_passed, passed), ("rejected", REJECTED_COLS, rejected)):
        # utf-8-sig: the BOM makes Excel open the file as UTF-8 (otherwise "→" and "’" break)
        with (out / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, restval="")
            w.writeheader()
            w.writerows(rows)

    pending = summary.get("pending_flow", 0)
    title = "Passed variants" if not pending else "Passed the rules - flow review pending"
    head = (f"{summary['passed']} of {plural(summary['total'], 'variant')} passed "
            f"(first round: {summary['first_round_passed']} of {summary['first_round_total']}).")
    if pending:
        head = (f"**Not final: {plural(pending, 'variant')} still wait for the flow review"
                f" (\"pending flow\" in notes).** " + head)
    if superseded:
        head += (f" {len(superseded)} earlier versions were replaced by their edits"
                 " (listed at the end, not for production).")
    if len(cols_passed) > len(BASE_COLS + FLAG_COLS):
        head += " Scene and CTA columns show the new text; an empty cell means the original stays."
    md_cols, md_rows, same = md_view(cols_passed, passed)
    if same:
        head += f" All rows: {same}."
    warn = "".join(f"\n> Warning: {w}\n" for w in summary["warnings"])
    old = f"\n## Superseded by edits\n\n{md_table(SUPERSEDED_COLS, superseded)}\n" if superseded else ""
    (out / "passed.md").write_text(
        f"# {title}\n\n{head}\n{warn}\n{md_table(md_cols, md_rows)}\n{old}", encoding="utf-8")
    viol = "\n".join(f"- {c} ({REASON_TEXT.get(c, '')}): {n}" for c, n in summary["violations"].items())
    (out / "rejected.md").write_text(
        f"# Rejected variants\n\n{plural(summary['rejected'], 'variant')} rejected.\n\n{viol}\n\n"
        f"{md_table(REJECTED_COLS, rejected)}\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "flow_review.md").write_text(flow_review_md(variants, sources or {}, flow or {}), encoding="utf-8")


# ---------------------------------------------------------------- main
def check_file(input_path: Path, source_path: Path | None = None, flow_path: Path | None = None
               ) -> tuple[list[Variant], dict]:
    variants, summary, _, _ = check_all(input_path, source_path, flow_path)
    return variants, summary


def check_all(input_path: Path, source_path: Path | None = None, flow_path: Path | None = None):
    """-> variants, summary, sources, flow verdicts."""
    warnings: list[str] = []
    sources = load_source_file(source_path) if source_path else {}
    flow: dict[str, tuple[str, str]] = {}
    if flow_path is not None:
        flow, flow_warnings = load_flow(flow_path)
        warnings += flow_warnings

    if input_path.suffix.lower() == ".json":
        variants, json_sources = load_json(input_path)
        sources = sources or json_sources
    elif input_path.suffix.lower() == ".csv":
        variants = load_csv(input_path, sources)
    else:
        raise ValueError(f"unsupported input type: {input_path.suffix} (use .json or .csv)")

    if any(not v.has_source for v in variants):
        warnings.append("no source script given: shots and scene/CTA VO length were not checked "
                        "(pass --source with the original script)")

    # sanity check of the source itself: reported, never blocks variants
    for body, src in sources.items():
        probe = Variant(variant_id="source", body_id=body or "?", segments=src,
                        changed={s: set(FIELDS) for s in src})
        check_variant(probe, None)
        warnings += [f"source script {body}: {code} - {detail}" for code, detail in probe.reasons
                     if code != "EMPTY"]

    run_checks(variants, sources, flow)
    return variants, summarize(variants, warnings, flow, str(flow_path or "")), sources, flow


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check text variations of a winning creative and drop the defective ones.")
    p.add_argument("input", type=Path, help="candidates.json from the skill or a CSV from any generator")
    p.add_argument("--source", type=Path, help="original script JSON (for CSV input): its shots are the allowed ones")
    p.add_argument("--out", type=Path, default=Path("out"), help="output folder (default: ./out)")
    p.add_argument("--flow", type=Path,
                   help="flow verdicts JSON (default: flow.json next to the input, if it exists)")
    a = p.parse_args(argv)
    flow_path = a.flow
    if flow_path is None and (a.input.parent / "flow.json").exists():
        flow_path = a.input.parent / "flow.json"

    try:
        variants, summary, sources, flow = check_all(a.input, a.source, flow_path)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    write_outputs(variants, a.out, summary, sources, flow)

    pending = summary["pending_flow"]
    print(f"{summary['passed']}/{summary['total']} passed the rules"
          f" (first round {summary['first_round_passed']}/{summary['first_round_total']})"
          + (f", {summary['superseded']} replaced by edits" if summary["superseded"] else "")
          + (f" - NOT FINAL: {pending} pending flow review" if pending else ", flow reviewed"))
    for gen, g in summary["by_generator"].items():
        print(f"  {gen}: {g['passed']}/{g['total']}")
    for code, n in summary["violations"].items():
        print(f"  {code}: {n}")
    for w in summary["warnings"]:
        print(f"warning: {w}")
    fl = summary["flow"]
    print(f"flow: {fl['ok']} ok, {fl['break']} break, {len(fl['unreviewed'])} not reviewed"
          + (f" ({fl['file']})" if fl["file"] else " (no flow.json)"))
    print(f"written to {a.out}/: passed.csv, passed.md, rejected.csv, rejected.md, summary.json, flow_review.md")
    return 0   # rejections are results, not errors: exit code 2 only when the input could not be read


if __name__ == "__main__":
    sys.exit(main())
