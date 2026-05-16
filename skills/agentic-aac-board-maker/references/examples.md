# Examples

These examples show expected agent reasoning and output shape.

## Example 1 — Year 7 English Hero Speech, Eye Gaze

User asks: “Make a Year 7 English hero speech AAC board for an eye-gaze user.”

Agent should infer:

- Pattern: curriculum participation + sentence builder.
- Access: eye gaze/dwell; 3x3 max per page.
- Functions: choose hero, describe, express opinion, explain with because, ask for help, rehearse/finish.
- Output: single-file HTML unless user requests JSON.

Likely pages:

1. Starter page: My hero is, I think, because, important, brave, helps people, Help, Different, Finished.
2. Facts page: born, lives, works, achieved, challenge, community, first, next, back.
3. Speech control page: speak sentence, clear, record note/export if implemented, help, finished.

Do not produce only a quiz about heroes.

## Example 2 — QCIA Community Access Board

User asks: “Build a QCIA community access board for going to the shops.”

Agent should include:

- go/stop/wait/help;
- shop/money/bus/crossing/safe;
- I need, where, thank you, finished;
- teacher evidence note: selections show requesting help, identifying safety, participating in community routine.

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
