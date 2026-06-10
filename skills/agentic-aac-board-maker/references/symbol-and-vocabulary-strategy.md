# Symbol And Vocabulary Strategy

This file guides how the agent chooses words and symbols.

## Vocabulary Principles

1. **Start from communication functions, not pictures.** Decide what the student needs to say/do before searching for symbols.
2. **Blend core and fringe.** Core words give flexibility; fringe words connect to the actual task.
3. **Keep labels speakable.** Prefer short labels that sound natural through TTS.
4. **Respect age and dignity.** Avoid babyish language for older students.
5. **Keep teacher customisation easy.** Use clear labels and search terms that can be changed.

## Core Vocabulary Bank

Choose only what fits:

- want
- more
- help
- stop
- go
- finished
- again
- different
- like
- don't like
- yes
- no
- wait
- my turn
- your turn
- I think
- because
- first
- next
- same
- different
- big/small
- good/bad
- easy/hard
- show me
- I don't know

## Fringe Vocabulary

Fringe words should come from:

- lesson topic;
- actual classroom routine;
- student interests if safely provided;
- real equipment/places/actions;
- QCIA goal context;
- curriculum content.

Avoid making a board mostly nouns. Add verbs, adjectives, comments, and reasons.

## Symbol Sources

### ARASAAC

Default open symbol source for non-commercial educational use when appropriate. Use:

- symbol IDs when known;
- search terms when IDs are unknown;
- text fallback always;
- attribution in generated file/resource.

Attribution template:

```text
The pictographic symbols used are the property of the Government of Aragon and have been created by Sergio Palao for ARASAAC (https://arasaac.org), that distributes them under Creative Commons License BY-NC-SA. (ARASAAC's required wording: author, owner, origin, licence. Keep the licence unversioned. Boards embedding ARASAAC symbols stay CC BY-NC-SA and must not be sold, e.g. on Teachers Pay Teachers. The ARASAAC logo is required on public-area signage.)
```

Check current ARASAAC licence requirements if publishing outside local classroom use.

## Other Open Symbol Sources

- **Mulberry Symbols** (https://mulberrysymbols.org/) - CC BY-SA 2.0 UK, no non-commercial restriction; designed for adults and older users, so often the better fit for secondary students where ARASAAC imagery reads young. Attribution: "Mulberry Symbols, copyright Steve Lee, CC BY-SA 2.0 UK".
- **Sclera** (https://www.sclera.be/) - CC BY-NC; ~11,400 high-contrast white-on-black symbols, valuable for students with CVI or low vision.
- **OpenMoji** (https://openmoji.org/) - CC BY-SA 4.0; the principled choice when a board uses emoji-style placeholders.
- **Global Symbols** (https://globalsymbols.com/) - free aggregator API serving Mulberry, ARASAAC, Sclera, OpenMoji and others under each set's own licence; useful fallback when api.arasaac.org is blocked on the school network.
- **Smarty Symbols is proprietary** (subscription) - treat like Boardmaker/PCS: do not copy.

For print-quality output, request ARASAAC pictograms at `resolution=2500` (the default 500 px is soft at A4 cell sizes); the API's skin and hair parameters help boards reflect the student.

### Teacher-owned custom images

Use for:

- local people/places;
- classroom equipment;
- actual routines;
- student-specific meaningful objects.

Privacy rule: do not upload custom student/class photos to AI vision or remote services unless the user explicitly approves.

### Text-only symbols

A text-only board can be valid if:

- symbols are unavailable;
- student reads or recognises words;
- print/offline constraints make symbols impractical;
- labels are large and high-contrast.

## Symbol Search Terms

For each button, include a `searchTerm` even if final output does not fetch symbols. Good search terms are concrete and simple:

- label `I need help` → search `help`
- label `Too loud` → search `noise` or `ear`
- label `I think` → search `think`
- label `because` → search `because` or `reason`
- label `Community` → search `people` or `community`

## Symbolate-Style Phrases

Use symbolated word/phrase layouts only for short phrases:

- I think
- I like
- I need help
- My turn
- Too loud
- I don't know

Avoid symbolating long sentences or paragraphs. It becomes visual clutter.

## Vocabulary QA

Check:

- Does the board include core/agency vocabulary?
- Are topic words relevant and not generic filler?
- Can the student say no/help/finished/different when appropriate?
- Are labels short enough for the target size?
- Are labels respectful for the student's age?
- Is every symbol backed by a text label?
- Is attribution included?
