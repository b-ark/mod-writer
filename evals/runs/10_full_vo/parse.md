# B03 "Morning rush" - parse (Step 1)

Mode: project mode. Run folder: `evals/runs/10_full_vo/` (eval override of `runs/<body>-<timestamp>`).
Body ID: `B03` (given in the request).

| segment | VO | on-screen | shot | shot description |
|---|---|---|---|---|
| hook | It's 7:45 and I have exactly one sock. | 7:45. One sock. | S01 | me hopping around the hallway in one sock, kid yelling in the background (problem) |
| scene_1 | Every morning I dig through a basket of strangers. | The basket of strangers | S02 | pile of odd socks on the bed (problem) |
| scene_2 | Then my sister sent me socks that snap together. | Wait, they snap? | S03 | close-up of the cuffs snapping together (product - reveal) |
| scene_3 | Off the feet, snap, into the wash, still a pair. | Still a pair | S04 | joined pair in the washer, comes out connected (product - proof) |
| cta | Take the quiz, five pairs for $29, cancel anytime. | 5 pairs - $29 | S05 | end card with the quiz on a phone (product - end card) |

Problem shots (may open a hook): S01, S02. Product shots: S03, S04, S05.

## Source vs hard rules
- Source hook is 8 words (at the limit) and has no banned words. No hard-rule break in the source.
- "snap" appears in scene_2 / scene_3 (body), which is allowed; it stays out of every new hook.

## Guessed / assumed
- Segments follow the timecodes; the hook is the 0:00-0:03 block as labelled, no cut needed.
- All visuals and on-screen texts were given; nothing guessed there.
- Shot numbering S01-S05 is mine (the script gives no IDs).

## Scope
**Full** - the request says "new hooks, new titles everywhere and new voiceover lines too": new hook (VO, on-screen,
first shot), new on-screen text in scene_1-3 and CTA, and new VO in scene_1-3 and CTA. Every variant is expected to
be marked `VO re-record needed`.

Status: treated as confirmed (non-interactive eval).
