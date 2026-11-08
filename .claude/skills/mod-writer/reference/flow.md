# Flow review: does the hook lead into the script?

You review variants you did not write. For each variant in `flow_review.md`, read the "Read aloud" line out loud
as one ad, then look at the table (new text is in **bold**, the rest is the original winner). Judge only how the
pieces fit together. Word counts, banned words, price and shots are already checked by check.py, so ignore them.

## Verdict `break` - a viewer would notice one of these

1. **Dangling join.** The first body line leans on something the hook does not give it. Its "but", "so", "then",
   "that", "them", "it", "they", "like who needs that" have nothing to refer to, or refer to the wrong thing.
   Example: hook "My dog only steals one sock." + scene_1 "like who needs that" (needs what?).
2. **Broken promise.** The hook asks a question, sets up a mystery or makes a claim that the rest of the ad never
   answers or pays off. The body must be the answer to the hook. Example: hook "Why does my son hide his socks?"
   when nothing in the body is about the son or hiding.
3. **Contradiction.** The hook states a fact that the body denies: a different time, place, person, number or
   attitude. Example: hook "I loved these socks from day one." + body "I ordered them to prove a point"
   (the body is a skeptic story).
4. **Different speaker.** The hook sounds like another person than the narrator of the body (another age,
   role, relation to the problem), and nothing explains the switch. Example: hook in a teen's voice + body
   "my drawer actually looks like an adult lives here now" with a parent's life.
5. **Text against picture or VO.** A new on-screen text contradicts its own VO line or the shot it sits on, or
   the hook VO describes something that clearly cannot be on the first shot (e.g. "the bus is honking" over a
   close-up of socks on a bed is fine; "my dog ran off with it" over a talking head is not).
6. **Thread lost (when scene texts are changed).** The new on-screen texts of the scenes do not continue the
   hook's idea; they read like texts from another variant.

## Verdict `ok`

Everything else, including hooks that are only fine, not great. A hook does not have to name what the body says
next. A jump in time is fine ("Late again." -> "Every morning I dig through a basket of strangers."). Do not judge
how funny or strong a hook is: that is the designer's pick.

When you are unsure, read hook + scene_1 aloud twice. If you had to add a word in your head to make it make sense,
it is a `break`.

## Output

One entry per variant, appended to `flow.json` next to `candidates.json` (keep entries already there):

```json
{"reviewer": "flow-review", "verdicts": [
  {"variant_id": "B03-V01", "verdict": "ok", "reason": ""},
  {"variant_id": "B03-V07", "verdict": "break", "reason": "dangling join: scene_1 'like who needs that' has no referent after the hook"}
]}
```

For a `break`, `reason` names the rule (1-6) and quotes the words that do not fit, so the writer can fix it.
