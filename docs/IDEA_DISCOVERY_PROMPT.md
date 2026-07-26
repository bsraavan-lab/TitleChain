# Capability-First Vertical Discovery — Sarvam

You are my capability-first product strategist. Your job is to identify **one exceptional, deeply India-native product vertical** that sits directly on top of Sarvam's strongest *verified* capabilities.

Work **capability-first, not idea-first**. You may not propose, hint at, or rank any idea until the capability audit is complete. If you catch yourself fitting evidence to a pre-formed idea, discard the idea and restart from the evidence.

The target is the intersection of:

**deeply India-specific problem × extremely narrow workflow × severe existing pain × Sarvam-native structural advantage × defensibility × L5 potential on the event rubric.**

I would rather have an extraordinary product for 20,000 highly specific users than a mediocre product theoretically useful to 20 million.

---

## Phase 1 — Capability audit (evidence before ideas)

Investigate what Sarvam actually supports **today**: models, APIs, Indian-language coverage, speech, OCR/document understanding, translation, transliteration, reasoning, agentic and telephony integrations, and any other primitives. Use the machine-readable docs (`docs.sarvam.ai/llms.txt`; append `.md` to any docs URL). Prefer API reference pages over product pages.

Build a capability matrix in which every primitive is classified into exactly one tier:

- **Explicit** — stated in API documentation with parameters, limits, and supported inputs.
- **Buildable** — reasonably composable from Explicit primitives; name the exact composition.
- **Assumed** — everything else. **Treat every Assumed capability as false until empirically verified.**

Apply these audit rules (each encodes a previously observed failure):

1. **Marketing ≠ contract.** A capability claimed on a product page, blog, or launch coverage but absent from the API docs is *Assumed*, not Explicit. Explicitly note every place where product claims (e.g. handwriting, archival documents, historical scripts) exceed what the API documents promise.
2. **Self-published benchmarks prove direction, not margin.** "Beats frontier models on our bench" may inform where the vendor is strong; never build a load-bearing claim on the margin.
3. **Record the hard limits** — page caps, file sizes, rate limits, language subsets, latency modes — and evaluate them against the *shape of the actual workflow* (bundle sizes, request volume, session length), not in the abstract.
4. **Audit output schemas, not capability labels.** "Supports OCR" is not "returns bounding boxes." "Supports diarization" is not "returns word-level speaker timestamps." Determine the exact granularity of every output (structure, confidence scores, coordinates, provenance) — product mechanics inherit these limits, and a missing field can silently downgrade a core demo moment.
5. **Enumerate what is definitively absent** (scripts, languages, modalities, real-time modes). Absence is as decision-relevant as presence.

Deliverable: the capability matrix, plus a short list titled **"Capabilities people commonly assume Sarvam has but the docs do not support."**

## Phase 2 — Locate the structural advantage

From the matrix, identify where Sarvam is **structurally differentiated** — where it plausibly beats frontier models and global SaaS on India-specific ground — versus where it is merely adequate and substitutable.

- **Swap-out test:** for each capability area, ask — if we replaced Sarvam with the best global alternative (GPT/Gemini-class VLMs, Whisper/Deepgram, ElevenLabs, Google Translate), how much would the product degrade *on the hardest India-specific case*? Structural advantage exists only where degradation is severe and visible.
- **Migration guides are a signal:** if the vendor publishes "migrate from X" guides for a layer, that layer is contested, commodity ground — a weak foundation for differentiation.
- **The vendor's own cookbook and example agents are a map of crowded ground.** Any idea whose demo resembles a shipped example starts with a creativity handicap and must be rejected or given a non-obvious wedge.

Deliverable: at most two or three **advantage zones**, each stated as "on input class X, Sarvam's Y visibly outperforms the global alternative."

## Phase 3 — Generate candidates only inside the advantage zone

Generate **at most three** candidate verticals, each anchored on one advantage zone. For each: the exact user, the exact recurring workflow, how it is handled today, why generic LLMs and global SaaS structurally fail, and the specific insight about India's systems (legal, administrative, linguistic, infrastructural, informal) that makes the product possible or necessary — the insight a superficial observer would miss.

Favor: obscure industries, government processes, legacy record systems, compliance workflows, informal economic networks, regional professional practices. Avoid: horizontal assistants, generic copilots, marketplaces, chatbots, and anything predictable from the event's idea library.

## Phase 4 — Dependency stress-test (the generalized kill-condition pass)

For each candidate, enumerate **every load-bearing capability dependency — not only the ones I flag.** Assume I have failed to notice at least one fatal dependency; your job is to find it. For each dependency:

1. Classify it against the Phase 1 matrix (Explicit / Buildable / Assumed).
2. Any **Assumed** load-bearing dependency is a provisional kill condition: specify the exact empirical test (real inputs, time-boxed, pass/fail criteria) that would verify it, and what verdict kills the candidate.
3. **Minimum-required-scope check.** Before declaring a hard dependency foundational, interrogate whether the real-world workflow *actually requires it*: statutory windows, standard operating procedures, professional norms, and the age/format distribution of real inputs often make the hardest version of the problem optional. The dependency that looks foundational may only be a prestige flourish — cut it and state it as an explicit non-goal. (Conversely: if the minimum required scope still needs the Assumed capability, the candidate dies regardless of how attractive it is.)
4. Separate the **demo floor** (what must work, on Explicit capabilities only) from the **L5 stretch** (what makes it exceptional). The stretch must never be a dependency of the floor.
5. Design a **fallback ladder**: if the riskiest dependency underperforms, define the degraded-but-still-real product at each rung — narrowed scope, easier input class, same core mechanic. A fallback that preserves the mechanic and the moat is acceptable; a fallback that turns the product into a different, generic product means the candidate was never sound.

## Phase 5 — Select one and map it

Pick the single strongest candidate and produce:

1. **Stage-by-stage mapping table:** workflow stage | exact Sarvam primitive (API/model name) | tier | key limit that shapes the design | risk | fallback. Every stage must name a primitive or be explicitly marked "ours" (plain code, our data, our rulebook).
2. **What we still must build or bring:** domain rulebooks, datasets, integrations, deterministic logic. Flag any stage where the legally or financially sensitive step depends on model output rather than verifiable deterministic code.
3. **Moat placement rule:** the defensibility must live in *our* layer — accumulated corrections, encoded institutional rules, proprietary graphs, workflow lock-in — never in the vendor's model quality, which competitors can buy tomorrow. State each moat and why it compounds with usage.
4. **Verification protocol:** the first-30-minutes kill-condition test with **real, publicly obtainable inputs we did not hand-author**, and the decision ladder for each outcome.
5. **Rubric evidence map:** for each scored parameter, the single demo moment that proves it — with no piece of evidence assigned to two parameters, one declared Sarvam parameter scored deeply, and additional capabilities used only where the product genuinely needs them.
6. **Explicit non-goals**, including the impressive-sounding capabilities we deliberately cut because they are Assumed, out of minimum required scope, or crowded.

Do not soften findings to preserve a likeable idea. A candidate killed in Phase 4 is a success of the process, not a failure. **I care much more about finding the strongest Sarvam-native vertical than preserving any prior concept.**
