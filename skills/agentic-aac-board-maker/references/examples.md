# Examples

These examples show expected agent reasoning and output shape.

## Example 1 — Year 7 English Hero Speech, Eye Gaze

User asks: “Make a Year 7 English hero speech AAC board for an eye-gaze user.”

Agent should infer:

- Pattern: curriculum participation + sentence builder.
- Access: eye gaze/dwell; 3x3 max per page, so use multiple pages instead of one dense grid.
- Functions: choose hero, describe, express opinion, explain with because, ask for help, rehearse/speak, repair.
- Output: single-file HTML unless user requests JSON.

A real sentence builder must actually build a sentence: include a message bar that accumulates selected words plus Speak sentence, Undo, and Start again controls. Speaking each word in isolation is not enough.

Likely pages (each 3x3, with Help and Speak sentence on every page):

1. Sentence starters page: My hero is, I think, because, For example, and also, plus a navigation button to the describing-words page, Speak sentence, Undo, Help.
2. Describing words page: brave, kind, helps others, never gives up, plus a navigation button back, Speak sentence, Undo, Start again, Help. Undo and Help appear on both pages so the most likely error - a wrong word just added - is repairable wherever the student is; the describing words are placeholders for the class text.

Use `navigation` buttons with `next-page`/`previous-page` actions so a gaze or switch user never faces more than nine targets at once. The shipped reference build lives in the repository's `generated/curriculum-sentence-builder/` folder.

Do not produce only a quiz about heroes, and do not collapse the sentence builder into a single grid of words with no way to assemble or speak a sentence.

## Example 2 — QCIA Community Access Board

User asks: “Build a QCIA community access board for going to the shops.”

Agent should include:

- go/stop/wait/help;
- Hello / I want to buy this / Pay now / Where is it? / I choose this / Too expensive (matching the shipped reference pack in `generated/qcia-community-shops/`; community-safety words such as crossing, bus, and money are natural customisations);
- I need, where, thank you, finished;
- teacher evidence note: selections show requesting help, safety language (Stop / wait, Help please), and participating in a community routine.

Access choice determines density.

## Example 3 — Visual Schedule

User asks: “Make a morning routine visual schedule.”

Agent should remember visual schedules are mostly receptive supports. Add expressive options if appropriate:

- Wait
- Help
- Finished
- Change
- I need more time

Do not describe it as the student's complete AAC system.

## Example 4 — HPE Respectful Relationships

User asks: “Make an HPE respectful relationships board.”

Good vocabulary:

- safe / unsafe
- kind / unkind
- stop
- help
- my body
- respect
- friend
- I feel
- I think
- because
- tell adult
- finished

Include refusal/stop language and avoid forcing disclosure of sensitive personal experiences.

## Example 5 — Science Sorting Living / Non-Living

Good board structure:

- Page 1: living, non-living, once living, not sure, because, same, different, help, finished.
- Page 2: animal, plant, rock, toy, water, grow, move, need food, back.

Preserves classification and explanation, not just picture naming.

## Example 6 — Needs/Repair Board

For a general support board:

- Help
- Stop
- Break
- Toilet
- Drink
- Pain
- Too loud
- Too hard
- Wait
- I don't understand
- Different
- Finished

If older student, use respectful labels and clean design, not childish clipart.

## Bad Example Pattern

User: “Make a board for The Very Hungry Caterpillar.”

Weak result: apple, pear, plum, strawberry, orange, cake, pickle, cheese, sausage.

Better result: I see, eat, more, finished, hungry, different, first, next, because, caterpillar, butterfly, help.

Reason: the better board supports commenting, sequencing, requesting, and repair, not only labelling story nouns.
