# mod-writer

Text variations for modifications of a winning SockLock video ad, plus a checker that drops the defective ones.
The designer pastes a winner script and gets ~20 checked variants: hook VO, on-screen text and first shot, plus
scene and CTA text if asked. Needs no access to SockLock systems and no server.

## Run it

### In the Claude app (claude.ai / desktop), no setup

1. Build the skill archive: `python scripts/build_skill.py` (writes `dist/mod-writer.zip`).
2. In the Claude app open **Settings > Capabilities**, turn on **Code execution and file creation**.
3. Under **Skills** click **Upload skill**, choose `mod-writer.zip` and turn it on.
4. In a new chat paste the winner script (brief, table, VO only; with or without timecodes) and ask:
   > New hooks for this one please, body B03

After changing the skill, rebuild the ZIP and upload it again: the app copy does not update by itself.

### In Claude Code

Open this folder in Claude Code and paste the script with the same request (or type `/mod-writer`).
The run goes to `runs/<body>-<timestamp>/`.

### check.py alone, on output from any generator (Atria, ChatGPT, a copywriter)

Python 3.10+, standard library only:

```
python scripts/check.py atria_hooks.csv --source data/winner_source.json --out out/atria
```

CSV: one row per changed segment, columns `variant_id, body_id, segment, vo, on_screen, shot` (optional
`angle, generator, round, replaces`). `segment` is `hook` (default), `scene_N` or `cta`. `shot` is a shot ID of
the source script, `NEW: <scene>`, or a description in words (both marked `New footage needed`). Without
`--source` only the text is checked. Exit code 0 = checked (rejections included), 2 = input could not be read.

### Tests

```
uv sync && uv run pytest      # 76 tests
```

## How it works

1. **Parse.** The skill splits the script into hook / scenes / CTA, numbers its visuals S01, S02, ... and marks
   each as problem or product. The designer confirms the table and the scope: hook only, hook + all on-screen
   text (default, nothing to re-record), or full (new VO too, marked `VO re-record needed`).
2. **Generate.** ~40 ideas, the obvious ones crossed out, ~20 kept across at least 5 known and 5 new angles.
   Every variant is cut from the script's own shots; up to a quarter may ask for new footage.
3. **Check.** `scripts/check.py` rejects what breaks a hard rule. A separate reviewer then reads every variant
   as one ad and judges whether the hook leads into the script (`flow.json`). Rejected variants are rewritten,
   2 rounds at most.
4. **Hand over.** The designer gets one file, `passed.xlsx`: every variant as the whole ad, part by part, with
   columns for the picture, the voice-over and the on-screen text; new text is highlighted, notes say what to
   record or film. Counts and rejection reasons stay in `summary.json` / `rejected.md`; `passed.csv` keeps the
   `variant_id`s for matching ad results later.

| Code | Rule |
|---|---|
| `ONSCREEN_LEN` | on-screen text at most 5 words |
| `HOOK_VO_LEN` / `SCENE_VO_LEN` | hook VO at most 8 words; scene VO not longer than the original |
| `BANNED` / `PRICE` | no "guaranteed", "forever", "100%"; price only in the CTA |
| `REVEAL` / `HOOK_SHOT` | the hook names no mechanism ("magnet", "click") and does not open on a product shot |
| `SHOT` | shot IDs only from the source script |
| `EMPTY` | no emptied text; the hook has VO or on-screen text |
| `DUP_SET` | not a near-duplicate of another variant |
| `FLOW` | the reviewer found the hook does not lead into the script |
| `MISSING_ID`, `DUP_ID`, `NO_CHANGE`, `BAD_SEGMENT`, `BAD_REPLACES` | input sanity |

Warnings (do not reject): more than 25% of the batch needs new footage, hook on the same shot as scene_1,
variants still pending the flow review, problems in the source script itself.

## Layout

```
.claude/skills/mod-writer/   SKILL.md + reference/ (brand.md, angles.md, flow.md)
scripts/check.py             the checker (stdlib only)
scripts/build_skill.py       packs the skill + check.py into dist/mod-writer.zip
data/                        winner script, blind test (Atria vs Claude baseline, labeled by hand)
evals/                       test scripts, skill runs, results.md, runs/REPORT_v3.md
tests/                       pytest
```

## Validation

- **Blind test** (12 Atria + 12 Claude-baseline hooks on one body, labeled by hand): check.py finds exactly the
  labeled violations, and all 8 hooks the designer accepted pass. Atria passed 4 of 12, plain Claude 6 of 12.
- **Skill runs** on 5 scripts, including a dirty VO-only one: [evals/results.md](evals/results.md); the latest
  runs with the requests and outputs: [evals/runs/REPORT_v3.md](evals/runs/REPORT_v3.md).

Whether the hooks are good is for the designer to judge. The pilot (2 weeks, 1-2 designers) measures time per
modification, how many variants go into production, and ROMI against manual modifications.
