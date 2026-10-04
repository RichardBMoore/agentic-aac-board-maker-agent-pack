# Research And Practice Map

Last checked: 2026-05-26.

Use this map to keep the pack grounded when adding prompts, fixtures, validators, or generated classroom supports. It is not clinical, legal, device, or licensing advice. Verify current primary sources before relying on any claim for high-stakes decisions, public release, procurement, or student-specific AAC prescription.

## Core Anchors

- ASHA AAC Practice Portal: AAC is multimodal and should support expression of wants, needs, feelings, ideas, social closeness, information transfer, and participation.
- Communication Bill of Rights: generated boards should preserve dignity, choice, refusal, preference/opinion, response, social interaction, and access to functioning communication supports.
- ISAAC Communication Access: access means time, opportunity, preferred methods, accessible information, and partner support, not merely a visible board.
- Project Core and aided-language resources: classroom boards need reusable core vocabulary plus context-specific fringe vocabulary and partner modelling.
- Light's communicative competence framework: support linguistic, operational, social, and strategic competence.
- CAST UDL: provide multiple means of engagement, representation, and action/expression.
- SETT Framework: make Student, Environment, Task, and Tools visible before choosing layout or technology.
- WCAG 2.2/WAI: keyboard, focus, pointer cancellation, target size, contrast, and reduced motion are web baselines; AAC/gaze targets often need much more generous dimensions.
- Tobii Dynavox access-method guidance: touch, eye gaze, mouse dwell, and scanning need different layouts and timing.
- ARASAAC terms: use open symbols with exact attribution, non-commercial/share-alike conditions, and text fallback.
- Australian Curriculum student diversity, QCAA QCIA, and the Disability Standards for Education: adjustments should support access, participation, and defensible evidence without lowering expectations by default.

## 0.9.0 Additions (checked 2026-10-04)

- Consistent symbol location (Thistle et al. 2018) -> enforced house layout and masked cells instead of reshuffling.
- Colour and grouping research (Thistle & Wilkinson) and the Modified Fitzgerald Key -> word classes, one scheme, grouping first, CVI profile.
- Literacy access (Erickson & Koppenhaver via AssistiveWare) and morphology studies -> ABC keyboard, core words and word endings by default.
- Partner instruction evidence and pause-time research (Mathis et al. 2011) -> partner cards with model words, wait time, comments and a least-to-most ladder.
- Scope communication access -> How I talk on community boards.
- Web Speech API facts (localService; Edge online voices) -> installed-voice preference and pinned voices.
- Automated logging literature (logs miss context; consent) -> opt-in on-device log with partner-model tagging and function counts.

## How This Changes The Pack

- Canonical IR 0.4.0 adds executable schema integrity, access/control limits and `systemFit` while retaining `sett`, `udl`, `differentiation`, `participationBarriers`, and `evidencePlan`.
- Validators fail noun grids, quiz-only boards, over-dense untested gaze layouts, missing repair routes, missing privacy, and missing attribution.
- Validators warn when differentiation/evidence metadata is thin, because legacy boards still need to load but new boards should be stronger.
- Generated fixtures must demonstrate agency, repair, modelling notes, access-aware density, privacy, attribution, and evidence routes.
- Open AAC Studio rendering preserves IR design metadata in `metadata.ir` even when the app ignores it.

## Practical Rule

If a board looks polished but the student can only label nouns or answer adult questions, it is not done. Add communication functions, repair/escape vocabulary, access-specific layout, partner modelling, and an evidence route.
