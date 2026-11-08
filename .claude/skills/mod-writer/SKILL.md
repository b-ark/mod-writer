---
name: mod-writer
description: Generate text variations for modifications of a winning SockLock video ad (new hooks, first lines, on-screen text, CTA text) and filter out defective ones with scripts/check.py. Use when a motion designer pastes a winner script (any format - brief, VO only, with or without timecodes) and asks for hooks, modifications, variations or new on-screen text.
---

# mod-writer

You help a SockLock motion designer make modifications of a winning creative. You write the text;
`scripts/check.py` decides what passes. Never present a variant to the designer that check.py did not pass,
and never write the result tables yourself - they come from check.py.

Before anything else, read:
- `reference/brand.md` - product, offer, audience, tone, hard rules
- `reference/angles.md` - angles that are known to work, and where new ones come from
- `reference/flow.md` - how a separate reviewer judges whether a hook leads into the script (Step 3); write so
  that every variant passes it

## Where you run

The skill works in two places. Find out which one you are in once, at the start.
- **Project mode (Claude Code in the mod-writer repo).** `scripts/check.py` is in the project root. The run
  folder is `runs/<body_id>-<YYYYMMDD-HHMM>/`, relative to the project root.
- **App mode (Claude app, skill uploaded as a ZIP).** There is no project. check.py is at `scripts/check.py`
  inside this skill's own folder, next to `reference/`, and it finds `reference/` by itself. Make the run folder
  `<body_id>-<YYYYMMDD-HHMM>/` in your working directory. At the hand-over, give the designer `passed.csv` and
  `passed.md` as downloadable files.

Below, `<check.py>` is the checker path and `<run>` is the run folder.

## Step 1 - Understand the script and confirm

The designer pastes the script in any form: a brief, a table, VO only, no timecodes, no shot IDs.
The script is the only footage there is: the variants re-use its shots, so you number them yourself.

1. Split it into segments: `hook` (first ~3 s / first line), `scene_1 ... scene_N`, `cta` (the line with the
   offer / quiz / price). If there is no explicit hook, the first sentence is the hook; if that sentence runs far
   past ~3 s (VO only, no timecodes), cut the hook at the first natural pause and say where you cut. If there is
   no explicit CTA, the last line with the offer is the CTA.
2. For each segment take VO, on-screen text (empty if not given) and the visual. Number the script's visuals
   `S01`, `S02`, ... in order of appearance, with a short description of each; a visual that repeats keeps its
   number. If the script gives no visual for a segment, describe it from the VO and mark it "(guess)".
   Note which shots show the problem and which show the product (the reveal, the proof, the end card).
   Keep each description short (up to ~8 words): the designer sees it next to the shot ID in the final table.
3. If the source itself breaks a hard rule (e.g. the original hook says "magnets" or is 15 words), say so under the
   table. It does not block the work: the new hooks replace it, and check.py prints it as a warning.
4. Ask for the body ID (the winner's ID or Meta ad name, e.g. `B01` or `SL_B01_lostsock_orig`). If the designer
   has none, propose `B<YYMMDD>` and use it. The body ID links every variant to future ad results.
5. Show what you understood as one table and wait for confirmation or corrections:

   | segment | VO | on-screen | shot | shot description |
   |---|---|---|---|---|

   Also list anything you guessed (missing on-screen text, unclear visual, where the hook ends).
6. Ask what to change, with three levels, in the same message as the table. If the designer's message already
   says, use that and don't ask. If it doesn't, name the default you will use, so one reply confirms both.
   - **Hook only** - hook VO, hook on-screen text, first shot. Nothing else changes.
   - **Hook + all on-screen text (default)** - the hook block, plus new on-screen text in every scene and in
     the CTA. No VO changes outside the hook, so nothing has to be re-recorded.
   - **Full** - as above, plus new VO lines in the scenes and the CTA. check.py marks these variants
     `VO re-record needed`.
   The designer can also name single segments ("only the CTA", "scene 2 VO").
   If the pasted script or brief itself sets the scope ("new hooks only", "keep the body"), that is the default
   for this run: name it as the default ("Default for this run: hook only, as the brief says"), so a reply of
   "default" or "ok" means the brief's scope. Only an explicit level named by the designer overrides the brief.

Do not generate anything until the designer confirms the table.

## Step 2 - Generate ~20 variants

Write about 20 variants (more if asked).

**First diverge, then pick.** The first idea that comes to mind for an angle is the one every batch already has
("my dryer runs a sock smuggling ring", "how many single socks are in your basket?"). So, before writing variants:
1. Jot down about 40 one-line hook ideas for this script (for yourself, not for the designer). Draw on the
   script's own details (its people, places, numbers, the story of the body), not only on the angle names.
2. Cross out the obvious ones, and the ones that repeat the winner's own hook in other words (the variants
   must be new hooks, not the original retold).
3. Keep the ~20 that differ most from each other in person, moment and format, then write them out.

Rules:
- Spread: at least 5 different angles from angles.md, and at least 5 variants on angles of your own that are
  not in angles.md. A new angle gets a short key of your own in `angle` (e.g. `gym-bag`) and a one-line
  `angle_note` saying what it is. No more than 4 variants per angle. If the designer explicitly asks for more in
  one angle, give them.
- One idea per hook. Hook VO <= 8 words, on-screen <= 5 words.
- **Shots come from the script.** The first shot of a hook is one of the script's problem shots (its own hook
  shot or a problem shot from a scene, e.g. `S02`). Never open on a product shot; a shot in which the product
  is visible at all (e.g. the joined pair in the washer) counts as a product shot. check.py rejects a hook on a
  shot whose `shot_desc` says "(product)" (code `HOOK_SHOT`), so mark every shot in Step 1. Write every hook so
  it works over existing footage: that is what a designer can cut today.
- Prefer a hook shot other than the shot of scene_1: otherwise one shot plays twice in a row. check.py warns
  about it; keep it only where the hook and scene_1 clearly use different moments of that clip.
- **New footage, for ideas that need their own picture.** If a hook is clearly stronger with a picture the
  script does not have, write its shot as `"NEW: <the scene to film, one line>"`. check.py lets it pass and
  marks it `New footage needed`. At most a quarter of the batch (5 of 20); the rest use the script's shots.
  check.py warns when more than 25% of the generated batch (round 0) needs new footage.
  A NEW shot is also a problem moment without the product. When fixing a `SHOT` rejection, prefer an existing
  shot; use NEW only if the idea does not work without it.
- The hook never names the mechanism: "magnet", "magnetic", "click" are rejected by check.py; also avoid
  "snap", "stick", "clip" in the hook. The reveal is in the body.
- No price outside the CTA. Never "guaranteed", "forever", "100%".
- Never leave a changed text empty: a hook needs VO or on-screen text, and a scene field you change gets new
  text, not "" (check.py rejects it with `EMPTY`). To keep a field as it is, leave it out of `changes`.
- Word limits count space-separated tokens that contain a letter or digit: "$29" and "7:45" are one word each,
  a lone "-" or "→" is not a word.
- A changed scene VO must not be longer than the original line. Scene on-screen text must still match the shot.
- When scene text is in scope, give each variant its own set of scene texts that continues its hook; do not
  rotate a few fixed sets. Change every scene in scope (an unchanged scene is fine only if its original text
  already fits the new hook). A CTA on-screen text keeps the offer (5 pairs / $29) or the quiz.
- When scene VO is in scope (Full), keep the story beats and the reveal where they are; a new line says the same
  thing in the variant's voice and has no more words than the original. The CTA VO keeps the offer or the quiz.
  The hook must then read into the variant's own new scene_1, not the original one.
- Hooks must read naturally into the first body line (scene_1): if scene_1 starts with "but" / "so" / "then",
  the hook must set that up. Read each hook + scene_1 aloud before writing it down.
- Variant IDs: `<body_id>-V01`, `<body_id>-V02`, ...

Write the file `<run>/candidates.json`:

```json
{
  "body_id": "B01",
  "generator": "mod-writer",
  "source": {"segments": [
    {"segment": "hook", "vo": "...", "on_screen": "...", "shot": "S01", "shot_desc": "single sock out of the dryer (problem)"},
    {"segment": "scene_1", "vo": "...", "on_screen": "...", "shot": "S02", "shot_desc": "pile of odd socks (problem)"},
    {"segment": "cta", "vo": "...", "on_screen": "...", "shot": "S06", "shot_desc": "end card (product)"}
  ]},
  "variants": [
    {"variant_id": "B01-V01", "angle": "mystery", "round": 0,
     "changes": {"hook": {"vo": "...", "on_screen": "...", "shot": "S02"}}},
    {"variant_id": "B01-V02", "angle": "humor", "round": 0,
     "changes": {"hook": {"vo": "...", "on_screen": "...", "shot": "S01"},
                 "scene_3": {"on_screen": "..."}}},
    {"variant_id": "B01-V03", "angle": "gym-bag", "angle_note": "one sock always stays in the locker room", "round": 0,
     "changes": {"hook": {"vo": "...", "on_screen": "...", "shot": "NEW: slow push into a dark dryer drum"}}}
  ]
}
```

`source` is the confirmed table from Step 1. Keep the shot description with "(problem)" or "(product)" in
`shot_desc`, so a later follow-up knows which shots may open a hook (check.py ignores this field). In `changes` put only the segments and fields you change.

## Step 3 - Check, regenerate, check again

check.py uses only the standard library and needs Python 3.10 or newer. In project mode, run it from the
project root and use `uv run python` if plain `python` is too old:

```
python <check.py> <run>/candidates.json --out <run>
```

check.py exits with 0 whenever it read the input, also when it rejected variants: rejections are results,
read them from its output. Exit code 2 means the input could not be read (bad path or broken JSON): fix that.

One check is two passes: rules, then flow.

1. **Rules.** Run check.py. It rejects what breaks the hard rules and writes `<run>/flow_review.md`: the full
   read-through (hook, every scene, CTA, with the shots) of each variant that passed the rules and has no flow
   verdict yet.
2. **Flow.** Whether the hook leads into the script is judged by a reviewer who did not write the variants, so
   it does not grade its own work.
   - Project mode: start a fresh subagent (Agent tool). Give it only the paths of `reference/flow.md` and
     `<run>/flow_review.md`, and ask it to write its verdicts into `<run>/flow.json` as flow.md says (append to
     the file if it exists). Do not give it your notes, ideas.md or your reasons for the hooks.
   - App mode (no subagents): do it yourself as a separate pass. Read only flow.md and flow_review.md, judge every
     variant as a stranger would, and write `<run>/flow.json`.
   Then run check.py again. It picks up `flow.json` next to candidates.json by itself and rejects every `break`
   with code `FLOW`. Until every passed variant has a verdict, check.py prints "NOT FINAL: N pending flow
   review", titles passed.md "flow review pending" and marks those rows `pending flow`. Never hand over in that
   state: "flow: N not reviewed" must be 0.

If nothing was rejected, go straight to Step 4. Otherwise read `<run>/rejected.csv`. For every rejected variant
write one replacement that fixes the stated reason and keeps the angle: id `<original id>-r1`, `"round": 1`,
`"generator": "mod-writer"`. Replacements follow every Step 2 rule. For a `SHOT`
rejection it is fine to keep the text and only change the shot. For a `FLOW` rejection fix what the reviewer
quoted: usually the hook must set up scene_1 (when scope allows, a new scene on-screen text can help, but the
scene VO stays unless the scope is Full).
check.py overwrites its output files on every run, so the final files describe all rounds. Append the
replacements to `variants` (keep the rejected originals in the file - check.py reports them as rejected, which is
the honest history; never delete verdicts from flow.json) and repeat both passes: the replacements get their own
flow review. If replacements fail, do one more round (`-r2`, `"round": 2`). Stop after 2 rounds.

## Step 4 - Hand over

Show the designer the content of `<run>/passed.md` as is: it is written for the designer and already lists what
to cut, the scenes to film and the edits that replace older variants. Add one line after it: the run folder,
and that `passed.csv` goes into the production sheet with the `variant_id` kept in the Meta ad name.

Nothing else: no pass counts, rejection reasons, FLOW breaks, rounds or warnings. That is the tool's own
bookkeeping (in rejected.md and summary.json); give it only if the designer asks. The one exception is a
warning the designer must act on that passed.md does not show (e.g. more than a quarter of the batch needs new
footage): one plain sentence.

## Follow-up in the same run

Work in the same `candidates.json` and repeat Step 3 (both passes) after every change. If the run folder has no check.py
output yet, run check.py once first. Do not delete or change an entry check.py already passed, because the
designer may have put its `variant_id` in the production sheet or a Meta ad name. A change to it is a new entry
(see "Edit" below). New entries and edits get `"round": 0`.

- **More variants** ("5 more humor"): new IDs after the last one (`B01-V21`, ...), `"round": 0`.
- **Edit an existing variant** ("shorter on-screen for V04", "another first shot for V09", "rewrite the scene 2
  line of V12"): add a new variant `<id>-e1` (then `-e2` for the next edit of the same one) with
  `"replaces": "<id>"`, the same angle, and the **full** `changes` of the old variant with the edit applied.
  check.py does not count it as a duplicate of the variant it replaces. Once the edit passes, the old one moves
  to "Replaced by edits" in passed.md. If the edit is rejected, the old one stays, so fix the edit as in Step 3
  (`<id>-e1-r1`, keeping `replaces`). An edit that changes scene VO gets `VO re-record needed`, like any variant.
- Hand over as in Step 4, but show only the new or edited variants from passed.md.
