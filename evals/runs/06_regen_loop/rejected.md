# Rejected variants

14 rejected.

- SHOT (shot is not in the source script (and not marked NEW)): 4
- REVEAL (product revealed in the hook): 4
- HOOK_VO_LEN (hook VO longer than 8 words): 2
- BANNED (banned word): 1
- ONSCREEN_LEN (on-screen text longer than 5 words): 1
- DUP_SET (repeats another variant in this set): 1
- DUP_LIBRARY (repeats a hook already in hooks_library on the same body): 1
- PRICE (price outside the CTA): 1

| variant_id | replaces | body_id | generator | round | angle | hook_vo | hook_on_screen | hook_shot | other_changes | codes | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AT-02 |  | B01 | atria | 0 | humor | Laundry day turned into a sock funeral. | RIP, left sock | S12 |  | SHOT | hook: S12 not in the source script (it has S01, S02, S03, S04, S05, S06); write "NEW: <scene>" if this needs new footage |
| AT-04 |  | B01 | atria | 0 | hack | Stop losing socks in the wash forever. | No more lonely socks | S01 |  | BANNED | hook vo: 'forever' in "Stop losing socks in the wash forever." |
| AT-05 |  | B01 | atria | 0 | math | I counted my single socks. Forty-one. | 41 lonely socks | S15 |  | SHOT | hook: S15 not in the source script (it has S01, S02, S03, S04, S05, S06); write "NEW: <scene>" if this needs new footage |
| AT-07 |  | B01 | atria | 0 | humor | The dryer is keeping secrets from you. | What the dryer hides | S14 |  | SHOT | hook: S14 not in the source script (it has S01, S02, S03, S04, S05, S06); write "NEW: <scene>" if this needs new footage |
| AT-08 |  | B01 | atria | 0 | question | Nobody talks about the sock problem enough. | We need to talk about socks | S02 |  | ONSCREEN_LEN | hook on-screen has 6 words (max 5): "We need to talk about socks" |
| AT-09 |  | B01 | atria | 0 | mystery | Where did my other sock go this time | Gone again | S01 |  | DUP_SET;DUP_LIBRARY | near-duplicate of AT-01 \| repeats AT-01 on B01 (accepted_blind_test): "Where did my other sock go this time?" |
| AT-11 |  | B01 | atria | 0 | hack | This tiny laundry fix saved my mornings. | Tiny fix, calm mornings | S13 |  | SHOT | hook: S13 not in the source script (it has S01, S02, S03, S04, S05, S06); write "NEW: <scene>" if this needs new footage |
| AT-12 |  | B01 | atria | 0 | question | Your sock drawer doesn't have to look like this. | Sock drawer chaos | S02 |  | HOOK_VO_LEN | hook VO has 9 words (max 8, ~3 s): "Your sock drawer doesn't have to look like this." |
| CL-01 |  | B01 | claude-baseline | 0 | hack | These magnetic socks never lose their partner. | Socks that stay paired | S03 |  | REVEAL | hook vo: 'magnetic' reveals the product before the body does |
| CL-03 |  | B01 | claude-baseline | 0 | hack | Click. That's the sound of never losing socks. | Click. Done. | S01 |  | REVEAL | hook vo: 'Click' reveals the product before the body does \| hook on_screen: 'Click' reveals the product before the body does |
| CL-06 |  | B01 | claude-baseline | 0 | hack | A tiny magnet ended my sock drama. | Sock drama: over | S01 |  | REVEAL | hook vo: 'magnet' reveals the product before the body does |
| CL-07 |  | B01 | claude-baseline | 0 | math | Five pairs for $29 changed my laundry. | 5 pairs, $29 | S02 |  | PRICE | hook vo: price '$29' is allowed only in the CTA \| hook on_screen: price '$29' is allowed only in the CTA |
| CL-09 |  | B01 | claude-baseline | 0 | hack | Socks that click together at the cuff. Finally. | They click together | S01 |  | REVEAL | hook vo: 'click' reveals the product before the body does \| hook on_screen: 'click' reveals the product before the body does |
| CL-10 |  | B01 | claude-baseline | 0 | parent | Raising three kids means losing three hundred socks a year. | 300 socks a year | S02 |  | HOOK_VO_LEN | hook VO has 10 words (max 8, ~3 s): "Raising three kids means losing three hundred socks a year." |
