# QLearn Approval And Privacy

## The token

- A QLearn personal access token lets a program act **as the teacher**, including anything the teacher can see. Treat it like a password.
- It is created by the teacher (Account → Settings → Approved Integrations → New Access Token) with a purpose and an expiry date of 6–12 months. If the button is missing, tokens may be switched off for the account; ask the school's QLearn administrator.
- It is stored only in the operating system's password vault via Python `keyring` (service `qlearn-token`, account `qlearn`). It is saved by the teacher pasting it into a terminal prompt, so it never passes through the agent or the chat. Code reads it at the moment of each request.
- It must never appear in code, `.env` files, git, logs, prompts, tests, screenshots, SCORM packages or chat. `scripts/check_pack.py` and `validate_scorm.py` scan for token-shaped strings.
- **If it leaks** (pasted into chat, email or a document), delete it on the same Settings page and make a new one. The agent must not use a leaked token.

## Least privilege, enforced in code

`scripts/canvas_client.py` refuses, before sending anything:

- any host other than the configured QLearn hosts, and plain `http`;
- student areas: users, enrolments, submissions, grades, gradebook history, discussion replies (entries), conversations, analytics, page views, peer reviews and outcome results;
- any write other than creating a page or updating an unpublished `[WORKING FILE]` page;
- any payload that would publish, notify or set a front page;
- any write without `confirmed=True`, which an agent sets only after the teacher says yes.

It cannot delete. Deleting, publishing and module changes stay with the teacher in QLearn.

## What goes to the AI provider

Anything the agent reads is sent to the AI provider. Keep reads to the course content needed for the task. Never read student work, names, grades or messages. Before working on material the department classifies as protected, check the AI-use guidance that applies to you.

## Approval for student use

- Visibility of a SCORM link in a course is **not** approval for every active script or every use. Before students use an uploaded interactive activity, confirm expectations with the school's QLearn administrator or EQ ICT.
- Do not host protected learning material on public services (GitHub Pages, Netlify and similar) for student use without EQ approval. The offline/USB route in `skills/accent-display-fit/references/eq-delivery-playbook.md` remains available.
- A longer-term hosted or LTI tool needs a departmental security and integration review. Prepare a precise request; never assume approval.

## Student information

- No real student names, diagnoses, NCCD records, behaviour notes, grades or submissions in packages, fixtures, file names, logs, issues or this public repository.
- Board IR must stay `privacy.containsSensitiveData: false`. `validate_scorm.py` fails a package that says otherwise and warns on any level other than `anonymous`.
- Use anonymous slugs (`--identifier`) because the package identifier and title are visible to everyone in the course.

## Licences

The bundled house symbols are ARASAAC pictograms (CC BY-NC-SA, Government of Aragón). Packages that embed them carry `licences/ARASAAC-symbols-LICENCE.md`. Non-commercial classroom use inside QLearn is consistent with that licence; do not sell or relicense packages that contain them.
