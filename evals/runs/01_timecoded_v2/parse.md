# B03 "Morning rush" - Step 1 parse (treated as confirmed)

Body ID: **B03** (given by the designer).
Mode: project mode (check.py at `scripts/check.py`), run folder `evals/runs/01_timecoded_v2/` (per eval instructions).

| segment | VO | on-screen | shot | shot description |
|---|---|---|---|---|
| hook (0:00-0:03) | It's 7:45 and I have exactly one sock. | 7:45. One sock. | S01 | me hopping around the hallway in one sock, kid yelling in the background (problem) |
| scene_1 (0:03-0:08) | Every morning I dig through a basket of strangers. | The basket of strangers | S02 | pile of odd socks on the bed (problem) |
| scene_2 (0:08-0:13) | Then my sister sent me socks that snap together. | Wait, they snap? | S03 | close-up of the cuffs snapping together (product) |
| scene_3 (0:13-0:19) | Off the feet, snap, into the wash, still a pair. | Still a pair | S04 | joined pair in the washer, comes out connected (product) |
| cta (0:19-0:24) | Take the quiz, five pairs for $29, cancel anytime. | 5 pairs - $29 | S05 | end card with the quiz on a phone (product) |

Problem shots (may open a hook): S01, S02. Product shots (never open a hook): S03, S04, S05.

## Guesses
- None material: the script gives timecodes, VO, text and shot for every segment. Hook = 0:00-0:03 block as labelled.
- Segment names: the unlabeled blocks 0:03-0:08, 0:08-0:13, 0:13-0:19 became scene_1..scene_3.

## Source rule breaks
- No hard-rule break. Hook VO is exactly 8 words ("7:45" = one word), on-screen 3 words; "snap" appears only in the body (scene_2/3), price only in the CTA.
- Note (not a hard rule): the source hook's idea (7:45 + one sock) overlaps library hook CL-05 on B01 ("7:45 a.m. One sock. Zero matches.", accepted_blind_test) and AT-06 ("POV: you're late and find one sock."). New hooks avoid re-using that exact idea.

## Scope
**Hook only** (hook VO, hook on-screen text, first shot). Reason: the designer's message says "New hooks for this winner, please" - it names hooks explicitly and nothing else, so per Step 1.6 that is taken as the answer and the default (hook + all on-screen) is not used. Scene and CTA text/VO stay as in the source, so every hook must read into the original scene_1 "Every morning I dig through a basket of strangers."
