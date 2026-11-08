# Eval results - mod-writer skill + check.py

Date: 2026-11-08. Model: Claude Opus 5.5 in Claude Code. Checker: `scripts/check.py` on Python 3.15.2.

## Setup

Each case was run by a fresh agent that only had SKILL.md, its reference/ files and the designer's message
(`evals/scripts/*.txt`). It could not see check.py, the tests or the blind test data. The run is non-interactive:
the agent writes the Step 1 "how I understood it" table to `parse.md` and treats it as confirmed. Every file
of a run is in `evals/runs/<case>/`: `candidates.json`, the check.py output, and `rejected_round0.csv` /
`summary_round0.json` with the state after the first check.

**Shots come from the script.** There is no shared shot list. The skill numbers the visuals of the pasted script
S01, S02, ... and every variant re-uses them. A hook whose idea needs footage the script does not have may use
`"shot": "NEW: <scene to film>"`: check.py lets it pass and marks it `New footage needed` (at most 3 per batch).

| # | Case | Input form | Scope asked |
|---|---|---|---|
| 01 | B03 Morning rush | timecodes, VO + text + visual | hook (default) |
| 02 | B04 Parents laundry | marketer's brief in prose, no timecodes | hook (default) |
| 03 | SL_B05_skeptic | **dirty**: VO only, lowercase, no timecodes, no on-screen text, no visuals | hook (default) |
| 04 | B06 Dryer conspiracy | one line per scene, 5 scenes | hook + on-screen in every scene + CTA text |
| 05 | B01 Lost sock (main winner) | timecodes; body already has 9 hooks in hooks_library | hook (default) |
| 06 | B01, regeneration loop | round 0 = the 24 blind-test hooks from Atria and Claude baseline; the skill does Steps 3-4 | hook |
| 08 | B01, follow-up after 05 | 3 designer messages: more variants, edits, a scene VO change | see "Follow-up messages" |
| 09 | B01, scope not named | same script as 05, request "New variations for B01 please." | default: hook + all on-screen text |
| 10 | B03, full package | same script as 01, request names new VO lines too | full: hook + on-screen + scene/CTA VO |

## Results

| # | Generated (round 0) | Passed first time | Rejected in round 0 | Replacements | Final in passed.csv | New footage | Angles | check.py warnings |
|---|---|---|---|---|---|---|---|---|
| 01 | 21 | 19 (90%) | 2 HOOK_VO_LEN | 2 in round 1, both passed | 21 | 2 | 11 | - |
| 02 | 20 | **20 (100%)** | 0 | 0 | 20 | 1 | 10 | - |
| 03 | 20 | **20 (100%)** | 0 | 0 | 20 | 2 | 9 | 2 about the source (see below) |
| 04 | 20 (7 segments each) | **20 (100%)** | 0 | 0 | 20 | 1 | 10 | - |
| 05 | 20 | **20 (100%)** | 0 | 0 | 20 | 2 | 11 | - |
| 06 | 24 (external) | 10 (42%) | 14 | 14 in round 1, all passed | 24 | 0 | - | - |
| 09 | 20 (hook + 5 on-screen texts) | **20 (100%)** | 0 | 0 | 20 | 1 | 11 | - |
| 10 | 20 (hook + 4 segments, VO and on-screen) | **20 (100%)** | 0 | 0 | 20, all `VO re-record needed` | 2 | 8 | - |

**Skill, cases 01-05: 99 of 101 variants passed check.py the first time, 101 of 101 after one round.**
Cases 09 and 10 check the scope levels. With no scope named, the skill took the default and wrote a new
on-screen text for every scene and the CTA. With "new voiceover lines too" it rewrote every scene and CTA line
within the original word count, kept the story beats and the reveal, and every variant got `VO re-record needed`.
`passed.csv` has one column per changed field (`scene_2_vo`, `scene_2_on_screen`, ..., `cta_vo`); an empty cell
means the original stays.
The 2 rejections in case 01 were 9-word hooks the agent counted as 8; check.py caught them and the rewrites passed.
8 of 101 variants (8%) ask for new footage, within the cap of 3 per batch; the other 93 can be cut from the
existing video today.

**Same body, same checker, other generators** (blind test, `data/blind_test_labeled.csv`, case 06 round 0):

| Generator | Passed check.py | Designer accepted |
|---|---|---|
| Atria | 4 / 12 (33%) | 3 / 12 |
| Claude, no skill (plain chat + the script) | 6 / 12 (50%) | 5 / 12 |
| mod-writer skill (case 05, same body B01) | 20 / 20 (100%) | not judged yet (pilot) |

## Violations seen

| Code | Count | Where | Example |
|---|---|---|---|
| SHOT | 4 | Atria | "Scene 12/13/14/15": the B01 script has 6 shots, Atria invented footage that does not exist |
| REVEAL | 4 | Claude baseline | "These **magnetic** socks...", "**Click.** That's the sound..." in the hook |
| HOOK_VO_LEN | 4 | Atria, Claude baseline, skill (01) | "Raising three kids means losing three hundred socks a year." (10 words) |
| BANNED | 1 | Atria | "Stop losing socks in the wash **forever**." |
| ONSCREEN_LEN | 1 | Atria | "We need to talk about socks" (6 words) |
| PRICE | 1 | Claude baseline | "Five pairs for **$29** changed my laundry." in the hook |
| DUP_SET + DUP_LIBRARY | 1 | Atria | hook 9 = hook 1 without the question mark (and hook 1 is now in hooks_library) |

In case 06 the skill rewrote all 14 rejected hooks in round 1, and all 14 passed. For the 4 SHOT rejections it
kept the text and moved the hook to a real problem shot of the script (S01 or S02), so no new footage was needed.
For REVEAL it kept the angle and dropped the mechanism ("A tiny magnet ended my sock drama." -> "One tiny thing
ended my sock drama.").

The check.py warnings in case 03 are about the **source** script, not the variants: the original hook says
"magnets" (REVEAL) and runs 14 words (HOOK_VO_LEN). This is correct: the scaling winner's own hook breaks the
rules, and the designer should know.

## Follow-up messages (case 08)

After run 05 (B01, V01-V20), the designer sends three messages in the same run:
1. "5 more in the humor angle, no dryer jokes."
2. "V04: shorter on-screen text. V09: a different first shot."
3. "V12: new scene 3 on-screen text about staying a pair, and the scene 2 line mentions the tiny magnet earlier."

| Message | Change in candidates.json | check.py |
|---|---|---|
| 1 | B01-V21..V25, humor, all on S02 | 25/25 passed |
| 2 | B01-V04-e1 (on-screen "Gave up matching"), B01-V09-e1 (S02 -> S01) | 25/27, 2 replaced by edits |
| 3 | B01-V12-e1: scene_2 VO (10 words, the original line has 11) + scene_3 on-screen | 25/28, 3 replaced, V12-e1 `VO re-record needed` |

Nothing was rejected. In the end: 25 variants for production, 3 old versions under "Superseded by edits".

An earlier run on a previous SKILL.md showed why edits are new entries. There the agent tried new IDs, check.py
rejected them as near-duplicates of V04 and V09, and the agent then **rewrote V04, V09 and V12 in place**. The old
texts were lost, and a `variant_id` that may already be in an ad name pointed to different text. Now an edit is
`<id>-e1` with `"replaces": "<id>"`: check.py does not count it as a duplicate of the variant it replaces, and once
it passes the old one moves to "Superseded by edits".

"5 more humor" puts 7 variants in one angle. Per SKILL.md, an explicit request from the designer is above the
4-per-angle cap.

## Observations

1. **The rules work best inside the prompt.** The skill passes almost everything the first time because brand.md
   and SKILL.md state the same hard rules check.py enforces. The plain Claude chat without them fails half the
   time. check.py is still needed: it caught the skill's own word-count mistakes in case 01, and it is the gate
   for external generators (case 06).
2. **Shots from the script keep variants cuttable.** Every hook either re-uses the script's footage or says
   plainly which scene must be filmed. Atria's 4 invented scenes are exactly what this prevents. The agents used
   NEW sparingly (0-2 per batch) and mostly for humor and mystery ideas set inside the dryer.
3. **Parsing the dirty script is the weakest step.** In case 03 there were no visuals, so every shot was a guess,
   and the 14-word first line had no natural pause, so the agent kept it whole as the hook. With only two problem
   shots in that script, all hooks open on one of them. The confirmation table is where the designer catches this.
4. **What check.py cannot judge:** whether a hook flows into scene_1 (agents flagged scene_1 lines starting with
   "them ... anyway" or "That's my evidence" that need a set-up), how funny it is, whether a hook opens on a
   product shot (it does not know which shots show the product), and whether a number is a made-up statistic.
   That is the designer's pick, and the pilot metric is ">= 5 of 15 taken".

## Changes to SKILL.md from these runs

- Product shot defined: any shot in which the product is visible, including the joined pair in the wash.
- A NEW shot must also be a problem moment; when fixing a SHOT rejection, prefer an existing shot.
- `shot_desc` with "(problem)" / "(product)" is kept in `source`, so a follow-up knows which shots may open a hook.
- Step 4 says "none" when nothing was rejected; brand.md allows first-person counts but no general statistics.

## Reproduce

```
uv run pytest                                             # 52 tests, including the blind test check
uv run python scripts/check.py evals/runs/05_winner_b01/candidates.json --out out/05
uv run python scripts/check.py data/blind_test_labeled.csv --source data/winner_source.json --no-library --out out/blind
```
