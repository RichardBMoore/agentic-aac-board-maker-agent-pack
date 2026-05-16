# Copy/Paste Agent Review Prompt

Please review this local project folder:

```text
/Users/richardbrucemoore/Desktop/Agentic-AAC-Board-Maker-Agent-Pack
```

## Context

I am building an agentic AAC board-making workflow for students with complex communication needs.

The vision is:

> Teacher intent in → AI agent directly generates evidence-informed, accessible AAC board/resource out.

This is not mainly about cloning Boardmaker or making teachers use another app. I built an Open AAC Studio / Boardmaker-style prototype as a reference laboratory so I could distil the hidden knowledge of AAC board-making into reusable agent skills: board patterns, symbol workflows, access rules, eye-gaze/dwell rules, switch scanning, printable layouts, offline classroom constraints, curriculum/QCIA translation, and QA checks.

The main skill to review is:

```text
skills/agentic-aac-board-maker/SKILL.md
```

Please also review the supporting reference files in:

```text
skills/agentic-aac-board-maker/references/
skills/agentic-aac-board-maker/templates/
skills/agentic-aac-board-maker/scripts/
skills/agentic-aac-board-maker/fixtures/
```

Then compare with the related skills:

```text
skills/open-aac-studio-board-builder/
skills/build-aac-student-supports/
```

## What I Need From You

Please give constructively critical feedback. I want the best results for students, not just a technically neat system.

Check:

1. Does the skill architecture make sense for an AI agent?
2. Are the reference files cohesive, or is there duplication/confusion?
3. Are the AAC principles strong enough?
4. Does it protect student agency and communication rights?
5. Does it avoid reducing AAC to quiz answering or compliance?
6. Does it properly distinguish visual supports from expressive AAC?
7. Are the eye-gaze/dwell and switch-scanning principles practical?
8. Are the curriculum/QCIA translation rules strong enough?
9. Are the output contracts clear enough for an agent to generate usable files?
10. Is the canonical AAC Board IR clear enough to stop schema drift?
11. Is the QA rubric strict enough?
12. What is missing for real classroom use?
13. What should be rewritten, merged, split, or expanded?
14. Does the plugin + standalone-skill packaging make sense?
15. Do `scripts/check_pack.py`, `validate_board_ir.py`, and `render_open_aac_studio.py` give enough enforcement?

## Response Format

Please respond with:

A. Overall assessment  
B. Major strengths  
C. Major risks or gaps  
D. File-by-file feedback  
E. Suggested revised architecture  
F. Specific wording or sections to add  
G. Priority next actions  
H. Evidence, ethics, accessibility, privacy, or classroom-practicality concerns  

Please be honest and specific. Focus on whether this will help an AI agent make better AAC boards for real students.
