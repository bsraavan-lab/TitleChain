import type { DerivedView, RuleRun } from "../../data/types";
import { OUTCOME_GLYPH, OUTCOME_TONE, OUTCOME_WORD } from "../../data/types";
import { RunRow, RunInputs } from "./RunRow";

export function TabWhatToCheck({ view }: { view: DerivedView }) {
  const runs = view.runs;
  const fail = runs.filter((r) => r.outcome === "FAIL");
  const parents = runs.filter((r) => r.key.startsWith("R4:parent="));
  const review = runs.filter((r) => r.outcome === "REVIEW" && !r.key.startsWith("R4:parent="));
  const notEval = runs.filter((r) => r.outcome === "NOT_EVALUABLE");
  const settled = runs.filter((r) => r.outcome === "PASS" || r.outcome === "NOT_APPLICABLE");
  const passed = settled.filter((r) => r.outcome === "PASS").length;
  const na = settled.length - passed;

  return (
    <section className="section" aria-label="What to check">
      {fail.map((run) => (
        <article className="row row--failed" key={run.key}>
          <span className="row-glyph glyph--seal" aria-hidden="true">
            ▲
          </span>
          <div className="row-body">
            <h2 className="row-title row-title--lead">
              <span className="status-word status-word--seal">{OUTCOME_WORD[run.outcome]}</span>
              {run.title}
              <span className="rule-id mono">{run.rule_id}</span>
            </h2>
            <p className="row-detail row-detail--lead">{run.message}</p>
            <RunInputs run={run} />
          </div>
        </article>
      ))}

      <article className="row row--grouped">
        <span className="row-glyph glyph--stamp" aria-hidden="true">
          ⚑
        </span>
        <div className="row-body">
          <h2 className="row-title">
            <span className="sr-only">Review — </span>
            {parents.length} earlier documents are named that nobody has read
            <span className="rule-id mono">R4</span>
          </h2>
          <p className="row-detail">
            Entry 1 points back to each of these as an earlier document. None is in any certificate
            here, so nobody has read what is inside them.
          </p>
          <ul className="chip-row">
            {parents.map((r) => (
              <li key={r.key}>
                <span className="doc-chip mono">{r.key.replace("R4:parent=", "")}</span>
              </li>
            ))}
          </ul>
          <details className="row-more">
            <summary className="row-more-summary">Each one separately</summary>
            <ul className="row-list">
              {parents.map((r) => (
                <li key={r.key}>
                  <MemberRow run={r} />
                </li>
              ))}
            </ul>
          </details>
        </div>
      </article>

      <ul className="row-list">
        {[...review, ...notEval].map((r) => (
          <li key={r.key}>
            <RunRow run={r} />
          </li>
        ))}
      </ul>

      <details className="quiet">
        <summary className="quiet-summary">
          {passed} passed · {na} not applicable
        </summary>
        <ul className="row-list quiet-list">
          {settled.map((r) => (
            <li key={r.key} className="row row--compact">
              <span className={`row-glyph glyph--${OUTCOME_TONE[r.outcome]}`} aria-hidden="true">
                {OUTCOME_GLYPH[r.outcome]}
              </span>
              <div className="row-body">
                <h3 className="row-title">
                  <span className="sr-only">{OUTCOME_WORD[r.outcome]} — </span>
                  {r.title}
                  <span className="rule-id mono">{r.rule_id}</span>
                </h3>
                <p className="row-detail">{r.message}</p>
              </div>
            </li>
          ))}
        </ul>
      </details>

      {/* There was a filled "Mark N items as checked" button here, and a
          "Rulebook" button, neither with a handler. Both are gone rather than
          wired: a sign-off is a per-finding judgement she puts her name to, so a
          single control that marks eleven of them at once is the wrong shape
          whether or not it works. The real per-finding review UI replaces it. */}
      <p className="meta checklist-foot">
        The same {view.runs.length} checks run on every case, in the same order.
        Each result comes from fixed code, not from a language model's judgement.
        If a check could not run, it says so and says why — it never quietly
        counts as a pass. Rulebook {view.rulebook_version}.
      </p>
    </section>
  );
}

function MemberRow({ run }: { run: RuleRun }) {
  return (
    <div className="row row--compact">
      <span className="row-glyph glyph--stamp" aria-hidden="true">
        ⚑
      </span>
      <div className="row-body">
        <h4 className="row-title">
          <span className="sr-only">Review — </span>
          {run.title}
        </h4>
        <p className="row-detail">{run.message}</p>
      </div>
    </div>
  );
}
