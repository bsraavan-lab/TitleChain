# Sarvam Epoch Buildathon — Handbook & Rubric

Source: `Rubric.pdf` (GrowthX x Sarvam Buildathon Builder Handbook). Canonical public source: https://growthx.club/docs/sarvam

---

## 1. Event shape

| Time | What |
|---|---|
| 10:00 AM | Kickoff — context, rules, Sarvam platform walkthrough, pick your problem |
| 10:30 AM | Build — six hours, solo or teams, on Sarvam |
| 4:30 PM | Submit — entries locked for the demo lineup |
| 5:30–6:30 PM | Demo — top teams on stage, winners announced, top 10 present at Sarvam Epoch |

Idea checkpoints: **commit by 11:30**, **running by 12:15**.

Principles the organisers state up front: everyone ships something working; you get the exact scoring parameters before you write a line, so build straight at what wins.

---

## 2. Rules

| # | Rule |
|---|---|
| 01 | **Build on Sarvam.** The platform is the constraint; everything else is your choice. Main layers are Doc AI and Voice. Use Sarvam Agents for complex workflows between systems — or just write the backend logic yourself. Sarvam Conversations is real-time voice (call and speak, much lower latency). |
| 02 | **Solo or teams** of up to 5. Every member registers and is approved individually. |
| 03 | **Build on-site.** No remote participation. |
| 04 | **No company demos.** If your company builds in this space, you can't demo your existing product. |
| 05 | **Submit on time.** Late submissions are not considered. |
| 06 | **One submission per team.** |
| 07 | **Judges' decision is final.** |

### Valid starting point

**Qualifies:** project started from zero today · a Sarvam product/model configured from scratch during the buildathon · an idea sketched but never deployed · helper tools and BaaS (Supabase, Sheets, Firebase, Clerk) · AI coding assistants writing the code · standard starter scaffolding (Next.js, Vite, FastAPI).

**Does not qualify:** a finished build with only cosmetic changes · a pre-built agent with minor tweaks · your existing product in original form · remote contributors or code written off the floor · a build already demoed or pitched elsewhere · builds on a stack other than Sarvam.

Borderline → submit and flag "borderline starting point" in notes. **Hiding the origin is auto-disqualification.**

---

## 3. Scoring architecture

Two groups of parameters.

**Product parameters — every team is scored on all five:**
1. Job-to-be-done completion
2. Memory and Context
3. Creativity
4. Impact
5. Delight

**Sarvam parameters — exactly three alternatives, OR logic. Pick ONE:**
1. Voice Experience
2. Document Intelligence
3. Dubbing

You choose the single Sarvam capability most central to completing the user's job. Judges score *that one*. **Additional capabilities add no points** — use them only if the product genuinely needs them. There is no API/DX branch and Dubbing does not merge into a generic "language" branch. API count is never rewarded.

### Level handling

L1–L5 are scored **independently per parameter**. There is no overall "this project is L3."

| L | Label | Meaning |
|---|---|---|
| L1 | Floor | Parameter absent, unproven, or present only in its most obvious form |
| L2 | Baseline | A basic attempt is visible, but important gaps limit the claim |
| L3 | Working | A credible middle standard demonstrated with relevant evidence |
| L4 | Strong | Distinctly strong; survives realistic challenge |
| L5 | Exceptional | A benchmark that is difficult to reproduce or dismiss |

Plan with a target vector, not a global level:

| Parameter | Current evidence | Target | Next proof |
|---|---|---|---|
| Job-to-be-done completion | L3 | L5 | Pass three repeated cases end to end |
| Memory and Context | L2 | L4 | Resume the same governed case after handoff |
| Creativity | L3 | L4 | Add a second reinforcing non-obvious workflow choice |

The one-hour MVP should aim for at least **JTBD L3**: a useful part of the declared job plus one real usable artifact.

### Anti-double-counting rule

**The same piece of evidence must not raise two parameters.** Ask what the behaviour actually proves and assign it to that parameter. Specifically:
- Conversational flow *within one exchange* is **Voice**, not Memory.
- Basic competence in Voice / Documents / Dubbing belongs to the **Sarvam parameter** and cannot be reused as **Delight**.
- Language swaps, visual polish, avatars, implementation difficulty, and API count **do not create Creativity**.
- Impact is the value of solving the problem, **not** whether the current prototype works.

---

## 4. Sarvam parameter ladders

### Voice Experience
*Does the voice feel human-grade and appropriate for the declared job?*
Pro tip: test real accents, code-switching, noise, interruptions, corrections, emotional shifts. Strong voice follows the real ask, builds each follow-up on the last answer, and changes pace and tone without losing the task.

- **L1 — works, but feels like a generic phone tree.** STT breaks on anything outside neutral speech. Accents, Hindi-English code-switching and background noise produce garbled transcripts the agent answers anyway. Intent detection is literal — latches onto the first phrase, misses the real ask. No emotional read: a calm caller and a panicked caller get the same flat reply. Turn-taking broken; agent talks over the user or freezes on interruption; a correction forces a restart from the top. Fixed question list, no logic between items, robotic prosody, stock phrases like "I understand your concern."
- **L2 — usable, but scripted and shallow.** Handles neutral speech on a happy path. Heavy accents, code-switching or noisy lines trip the transcript. Intent works for direct asks but misses hedged or layered ones. Says the right words for a complaint but doesn't sound like it senses one. Basic turn-taking; interruptions throw it off, only clean corrections recover. Obvious follow-ups, repeated confirmation lines, flat voice, generic word choice.
- **L3 — functional and domain-aware, not yet polished.** Handles most clean speech and some accent variation. Layered complaints, mixed-language sentences or unclear speech still break it. Picks up obvious emotion or urgency and shifts slightly. Decent turn-taking: simple interruptions and clean corrections recover, but loses context on mid-stream redirects. Useful role-specific follow-ups; script seams show under pushback; stock phrases leak under pressure.
- **L4 — a competent operator for the declared job.** Handles accents, most code-switching, noisy phone lines without breaking the transcript. Catches the real ask under hedging or rambling. Strong emotional read — picks up frustration, urgency, hesitation, mild anger, adjusts tone in-call. Clean turn-taking, barge-in without losing context, recovers from corrections without restarting. Pacing varies by moment. Each follow-up builds on the last answer. Doesn't over-talk.
- **L5 — human-grade for the declared job.** Holds up on real Indian speech: accents, Hindi-English code-switching, noisy lines, partial words, self-corrections. Sharp emotional read; adapts mid-call without sounding theatrical. Handles barge-in, knows when to stop talking, recovers fluidly from "no wait, actually" moments. Deliberate pacing shifts, real pauses. Knows when to comfort, when to be firm, when to ask one more question, when to wrap, when to escalate. No filler, no jargon dump, no repeated stock phrases. *Example:* a payments caller asks about a failed ₹4,200 UPI payment, fumbles for the UTR, and the agent offers to find it by amount and timestamp, picks up rising frustration, softens, confirms the dispute reference in one clean line, and offers to send the case ID on WhatsApp.

### Document Intelligence
*How well does the product understand and represent real Indian documents?*
Pro tip: use documents that look like the ones users actually have. Preserve reading order and structure, keep outputs traceable to the source, and expose uncertainty instead of guessing. Combine hard conditions to prove L4–L5.

- **L1 — works only when the document is already easy.** Depends on clean digital text-layer PDFs or copied text. Loses reading order, headings, tables, checkboxes, page relationships. Scans, photographs, handwriting and mixed scripts make the output unusable.
- **L2 — handles clean scans and simple layouts.** A legible scan/photo with one language and conventional formatting works. Basic paragraphs survive, but handwriting, low light, skew, stamps, multi-column reading order or dense tables break the representation. Output needs significant manual cleanup.
- **L3 — handles representative real-world documents with one meaningful difficulty.** Preserves usable reading order and structure across ordinary scans/phone photos and handles at least one hard class relevant to the use case: handwriting, tables, mixed scripts, degraded scans, or complex forms. Extracted regions stay connected to their source page or location. A harder combination still causes visible errors.
- **L4 — robust across the difficult conditions the user actually encounters.** Handles combinations of handwriting, mixed Indic scripts, multilingual text, complex layouts, tables, stamps, folds, skew, poor lighting, faded print, overwriting — without flattening meaning or structure. **Uncertain regions are visibly identified and easy to inspect against the source.**
- **L5 — expert-grade understanding on the hardest Indian material.** Holds up on severely degraded, handwritten, historical or heritage documents; mixed scripts and languages; dense tables; marginalia; corrections; seals; damaged originals. Produces a structured, searchable representation that preserves relationships and provenance, not a text dump. Knows which regions are uncertain and makes review precise. *Example:* a handwritten archival ledger with faded ink, Marathi and English entries, margin corrections, stamps, damaged corners and tables spanning pages becomes a searchable structured record preserving page/row/column/source region for every entry, with competing readings kept visible as uncertainty.

### Dubbing
*Does the dubbed media feel authored and performed for this audience?*
Pro tip: test with fluent listeners on representative media. Preserve meaning, speaker identity, pronunciation, emotion, pace, timing, music and cuts. L5 should be publishable without a full rewrite, re-recording or remix.

- **L1 — audio replaced, media no longer works.** Literal or broken conversion. Meaning, names, numbers or key terms damaged. Robotic voices or wrong speaker assignment. Timing ignores the source, dialogue runs across cuts, music or original speech competes with the dub.
- **L2 — understandable on a simple clip, but overlaid.** Straightforward speech translated and voiced well enough to follow. Domain terms, code-mixing, idiom, jokes, names or emotional passages produce obvious mistakes. Basic speaker separation, inconsistent pronunciation, approximate timing. Feels like audio placed on top of a video.
- **L3 — natural and audience-aware on representative media.** Preserves essential meaning, tone and important terminology in spoken language fitting the declared audience. Speakers distinguishable, common names and code-mixed terms pronounced credibly, dialogue broadly follows segment timing. Emotion, rapid exchanges, overlaps, music or difficult cuts still reveal synthetic seams.
- **L4 — native to the audience and faithful to the performance.** Preserves intent, register, terminology, idiom, code-mixing and regional phrasing without copying source-language syntax. Speaker identity, pronunciation, emotion, emphasis, pace and temporal alignment stay consistent across varied scenes. Dialogue sits cleanly with music and effects; uncertain names or phrases are isolated for targeted review.
- **L5 — publication-ready across real Indian language and media complexity.** Handles regional variation, code-mixing, incomplete speech, idiom, cultural references, domain language and audience-specific register with native judgment. Preserves each speaker's identity, intention, humour, restraint and emotional arc. Rapid exchanges, overlaps, music, ambience, scene cuts and difficult timing remain coherent. Publishable without a full human rewrite, re-recording or remix.

---

## 5. Product parameter ladders

### Job-to-be-done completion
*Did the product produce the correct, usable outcome?*
Pro tip: declare the exact job, run the common path, inspect the final artifact or write-back. Get the common path working before a rare edge case consumes the sprint. Repeated difficult cases without builder rescue distinguish L5.

| L | Standard |
|---|---|
| L1 | **0 completed tasks. Demo only.** Canned responses or talking through the workflow without completing the declared job. |
| L2 | **<30% task success.** It runs, but output is broken, fake, incomplete or unusable. |
| L3 | **50–70% task success on mocked, sandbox or staged surfaces.** Completes a useful part of the declared job and creates **at least one usable artifact**. Staged WordPress, sandbox Gmail, dummy ATS, mocked CRM, Airtable, Notion or Google Sheets sit here. |
| L4 | **70–85% task success on a production-like demo workflow.** Completes most of the declared job across a realistic workflow. Human review may still be needed for final approval. |
| L5 | **85%+ success across a minimum of three repeated test cases.** Completes the job end to end on mocked/sandbox/staged/live demo surfaces and produces a final usable output **without judge intervention**. |

### Memory and Context
*Does the product carry forward the right identity, history, task state, permissions and business rules?*
Pro tip: test what survives a restart, channel switch, or handoff.

| L | Standard |
|---|---|
| L1 | **Every interaction starts from zero.** No retention of task, identity, prior answers, document state or business context. |
| L2 | **Remembers identifiers, but not the working context.** Holds a name, phone number, case ID, document ID or preferred language. Doesn't retain the user's actual goal, prior decisions, permission scope or job state. Handoffs pass identity at best. |
| L3 | **Maintains the complete current task for an authenticated user.** Knows who the user is, what they can access, what's been supplied and what remains. Uses earlier answers instead of repeating questions. Current-task context survives ordinary steps — but older history, a new session, a new channel or a handoff is incomplete or lost. |
| L4 | **Uses relevant history and carries context across sessions, channels or handoffs.** Combines current task with prior tickets, documents, transactions, corrections, preferences, decisions or unresolved actions. A handoff receives concise accurate state rather than a raw transcript; the next component continues without a restart. Authentication and permissions remain intact. |
| L5 | **Governed business continuity across the whole product.** Reliably combines three layers: current task, relevant history of this user/case, and the business rules governing the next step. Context survives every demonstrated session, channel, tool and handoff. Corrections propagate, stale information is distinguishable from current, and access stays within the authenticated user's permissions and organisation boundaries. |

### Creativity
*How uniquely and non-obviously was the problem solved?*
Pro tip: remove the styling and API count. Is the *way the problem is solved* still non-obvious? **One meaningful product choice is L3; several reinforcing choices are L4; a coherent reframing is L5.**

| L | Standard |
|---|---|
| L1 | **The obvious first implementation.** Closely reproduces a reference agent, idea card, tutorial or generic wrapper. The problem statement predicts the entire demo. Changing logo, persona, language or UI theme is not a creative contribution. |
| L2 | **A twist, but cosmetic or loosely attached.** One variation beyond the obvious build that doesn't materially change how the problem is understood or solved. May create a demo moment without making the product more coherent or useful. |
| L3 | **One meaningful, non-obvious choice.** A recognisable point of view. At least one mechanic, workflow choice, or use of the Sarvam stack changes how the user solves the problem rather than decorating the expected solution. The rest may still be conventional. |
| L4 | **Distinctive end to end.** Several original choices reinforce one another across problem framing, interaction and workflow. Use of Sarvam is purposeful rather than ornamental. Another competent team given the same problem would be unlikely to arrive at the same product. |
| L5 | **Reframes what people thought the product could be.** Produces a genuine "I did not know you could solve it that way" reaction, yet feels coherent and inevitable once demonstrated. The non-obvious approach unlocks a materially better possibility. A memorable product category or interaction that cannot be inferred from the idea card alone. |

### Impact
*If this product did not exist — or was taken away — whose outcome gets worse, by how much, and how often?*
Pro tip: name who is affected, how many and how often, what the problem costs or breaks today, and which metric should move. Show data, explicit assumptions, or a back-of-the-envelope calculation. **Market size alone is not impact.**

| L | Standard |
|---|---|
| L1 | **No credible impact case.** Describes technology or broad social good but can't name who experiences the problem, how often, what it costs, or which outcome changes. ("Empower Bharat with AI.") |
| L2 | **The problem is real, but the value case is weak or unproven.** Names a user and a metric, but frequency, current cost, or path to the outcome is mostly assumed. Likely movement is small, below 5%, or limited to a convenience metric. |
| L3 | **A clear case for meaningful value.** Can defend who benefits, how often the problem occurs, what the current process costs, and a plausible **5% to below 10%** movement on one meaningful metric. For public-service or everyday-life products, an equivalent movement in access, completion, turnaround time, error rate, or avoidable loss counts. |
| L4 | **Targets a major, measurable bottleneck.** Defensible path to **10–30%** movement on an important operating, revenue, cost, risk, access or service metric. Affected user or payer is explicit, baseline is credible, and the value survives reasonable challenge to the assumptions. |
| L5 | **A top-priority problem with transformational value.** Tied to a critical metric or previously inaccessible outcome, with a credible path to **more than 30%** movement or an equivalent step-change in cost, revenue, risk, access or service delivery. Can show why this is a priority now, why the organisation or user would act, and what adoption at meaningful scale looks like. |

### Delight
*At the user's real point of friction, does the product create confidence, clarity and forward movement?*
Pro tip: identify the user's highest-friction moment. Show what they fear, what a trusted human does today, and how the product creates honest confidence and a clear next step. **Animation or "don't worry" copy is not Delight.**

| L | Standard |
|---|---|
| L1 | **Mishandles the moment of friction.** User becomes more confused, anxious or stuck. Hides uncertainty, offers false reassurance before it knows the answer, exposes raw system output, or ends without a usable next step. |
| L2 | **Usable, but the care is generic.** Completes the happy path and may add polite language, a friendly voice, animation or "don't worry" copy. Doesn't respond to the user's actual concern, explain why the situation is or isn't serious, or adapt the next step to the case. |
| L3 | **Removes the obvious friction.** A first-time user completes the main flow without builder intervention. Communicates status honestly, presents the result in the right form and language, gives a concrete next action. Context-aware on the common path, but care stops at the immediate result or becomes generic when the case is uncertain. |
| L4 | **Handles the user's hardest moment with judgment.** Identifies the real point of anxiety and responds with the correct emotional weight. Tells the truth without alarming, reassures only where the evidence supports it, explains what happens next, and recovers without discarding progress. The user feels the product understands both the job and the situation. |
| L5 | **Anticipates the pain point and stays with the user through resolution.** Everything L4 requires, then goes beyond the immediate interaction: predicts the next concern, preserves continuity, makes follow-up effortless, keeps the user informed until the difficult job has a controlled path forward. Support is specific to the user's situation — not a pile of extra features — and every demonstrated edge feels intentional. |

---

## 6. Idea-selection principles (from the Idea & Scope Copilot prompt)

### Asymmetric fit
A strong idea sits at the intersection of: a real and consequential job; this team's unusual knowledge, access, speed or lived experience; a differentiated sponsor capability; an uncrowded or poorly solved opportunity; and a scope that fits the available time.

> *Why are we unusually capable of building this, and why does this event make now the right moment?*

### Decisive proof
Design backwards from what judges can see and verify. A strong idea has: a difficult or unseen input; visible processing or interaction; a completed job; a final usable artifact or changed system state; one memorable creative or delightful behaviour; repeatable success without builder intervention.

> *What exact 60–120 second demonstration would prove that this works, matters, and is meaningfully different?*

### Guardrails
- Don't reward API count, architectural complexity, "multi-agent" labels, or feature quantity.
- Don't claim a sponsor capability is unique without evidence — identify the *hard case* where the Sarvam stack gives a material advantage.
- The creative mechanic must change how the job is completed, understood, trusted, coordinated or experienced. A visual effect, extra agent, animated avatar, voice skin or dashboard is not sufficient by itself.
- Copying a library idea earns no rubric advantage.
- Don't assume arbitrary speaker cloning, same-speaker dubbing, or real-time latency — verify the available APIs first.
- A document product must do more than OCR: reconstruct, trace, explain, preserve, compare, make accessible, or complete a meaningful job.
- A cross-language product must preserve corrections, names, numbers, intent and shared task state — not merely translate isolated sentences.

### Adversarial checks for any direction
- Urgent job, or interesting capability demo?
- Does it finish the job, or stop at advice/extraction/conversation?
- Would the product be essentially the same if the sponsor tech were swapped out?
- Is the differentiated hard case visible in the demo?
- Is it already an obvious sponsor example or crowded hackathon pattern?
- Is the creativity structural or cosmetic?
- Does Delight arise from meaningful product behaviour?
- Can the core loop work in one hour?
- Can it succeed three times on inputs we did not hand-author for the happy path?
- What is most likely to fail live? What must be removed to make it stronger?

### Idea Lock (fill before building)

| Decision | Locked answer |
|---|---|
| One-sentence product | |
| User | |
| Job completed | |
| Hard input | |
| Final output / state change | |
| Sarvam parameter | Voice Experience / Document Intelligence / Dubbing |
| Additional capability | None unless the product genuinely requires it |
| Exact sponsor APIs | |
| Supported language / input subset | |
| Team advantage | |
| Creativity thesis | |
| Delight thesis | |
| Demo proof | |
| Non-goals | |

### Scope requirements
First end-to-end milestone achievable **within one hour**; it must de-risk the hardest dependency and complete one ugly, hardcoded, end-to-end job before any breadth or polish. Every milestone needs exact build tasks, an acceptance test, and an "if we are behind, cut to this" fallback. Maintain a parking lot to prevent feature drift. Reserve the final milestone for repeated tests, reset state, fallback inputs, public-link verification, submission assets and **two timed rehearsals**. End with a time-boxed demo script and an evidence map showing which exact moment supports each claimed rubric parameter.

---

## 7. Exploration lenses (Phase 4)

1. **Living documents and cultural memory** — museum collections; heritage manuscripts; inscriptions, registers, marginalia, seals, damaged originals; government archives; family/community documents in regional scripts.
2. **Oral, cultural, and spiritual life** — prayers and devotional material; oral histories; pronunciation and recitation support; disappearing spoken traditions; accessibility for elders, children, migrants, and non-text users.
3. **Cross-language human communication** — two people speaking different languages in real time; multilingual teams, classrooms, families, public services, field work; preserving corrections, tone, intent, names, numbers, canonical meaning.
4. **Media adaptation and Dubbing** — educational, cultural, civic, creator and public-information media; audience-aware adaptation; speaker separation, pronunciation, emotion, pace, timing, music, scene cuts.
5. **Commercial and institutional workflows** — physical work, care, insurance, compliance, hiring, finance, education, public-service completion.

Impact for cultural/spiritual products may be measured through access, preservation, comprehension, participation, time, error, or reach — not only revenue.

---

## 8. Idea Library (sparks, not specifications)

**Business:** GST notice interpretation for regional small traders · Overdue invoice recovery for MSMEs · Offline machine diagnostics for factory floors · Multilingual documentation for Indian SaaS · Pre-signing contract comprehension for small businesses · Section 138 notice drafting for cheque bounces · Supplier verification calls for large orders · Financial report explanation for small business owners · Handwritten wage register digitisation for informal labour · Regional-language customer support for consumer brands

**Public Services:** Voice-guided government form completion · Court order interpretation for litigants · Voice-drafted police complaints · Voice-first RTI application drafting · Pension continuation calls for elderly claimants · Generic medicine substitution at the pharmacy counter · Pre-submission EPF claim verification · Cybercrime complaint filing for scam victims · Consumer forum complaint drafting · Voice data entry for community health workers · Scholarship eligibility matching for rural families · Bank and asset succession navigator for heirs

**Health and Education:** Cross-hospital medical records digitisation for chronic patients · Pre-purchase insurance policy comprehension · Cross-language interpretation between nurses and patients · Plain-language explanation of lab reports · Comparing conflicting medical opinions across languages · Personalised mock tests for competitive exam students · Career counselling for tier 3/4 town students · Plain-language explanation of property documents

---

## 9. Sarvam stack reference

Get the API key and make the first call **in the first 15 minutes** — everything else depends on it.

| Layer | What |
|---|---|
| **Saaras v3** | STT, 23 languages. Five output modes: transcribe, translate, verbatim, transliterate, codemix. REST for clips, Streaming for live voice, Batch for long files. Speaker diarization available. |
| **Bulbul v3** | TTS, 30+ voices. Tune pitch, pace, loudness. Stream over WebSocket for live agents. |
| **Sarvam-30B / Sarvam-105B** | Chat. 30B for speed, 105B for hard reasoning turns. Escalate 30B → 105B on hard turns if latency matters. |
| **Mayura / Sarvam-Translate** | Translation. Mayura: 11 languages with context preservation. Sarvam-Translate: all 23, long-form. Transliteration and language detection live here — detect on the first utterance to auto-switch. |
| **Sarvam Vision** | Documents. 200 MB per file, 10-page PDF cap. |
| **Doc AI Studio** | Two workflows: **Extract** (locates named fields) and **Digitise** (converts every page, printed or handwritten, to structured text). Accepts PDF, JPEG, PNG up to 50 MB and 10 pages per project. |
| **Voice agent integrations** | Twilio, Exotel, LiveKit, Pipecat — use the official guides instead of wiring telephony from scratch. Cookbook has full example agents (collections, government schemes, tutoring, loan advisory). |
| **Creative studio** | Agentic document translation across languages; video dubbing with the original speaker's voice preserved. |
| **AI-assisted building** | Sarvam MCP server, llms.txt index, agent skills. Append `.md` to any docs URL for the markdown version. |

⚠️ Cookbook example agents (collections, government schemes, tutoring, loan advisory) are explicitly named — reproducing them is a crowded-pattern risk.
