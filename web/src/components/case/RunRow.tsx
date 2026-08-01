import type { RuleRun } from "../../data/types";
import { OUTCOME_GLYPH, OUTCOME_TONE, OUTCOME_WORD } from "../../data/types";

export function RunRow({ run, lead }: { run: RuleRun; lead?: boolean }) {
  const tone = OUTCOME_TONE[run.outcome];
  const loud = run.outcome === "FAIL" || run.outcome === "NOT_EVALUABLE";
  return (
    <div className="row row--two">
      <span className={`row-glyph glyph--${tone}`} aria-hidden="true">
        {OUTCOME_GLYPH[run.outcome]}
      </span>
      <div className="row-body">
        <h3 className={`row-title${lead ? " row-title--lead" : ""}`}>
          {loud ? (
            <span className={`status-word status-word--${tone}`}>
              {OUTCOME_WORD[run.outcome]}
            </span>
          ) : (
            <span className="sr-only">{OUTCOME_WORD[run.outcome]} — </span>
          )}
          {run.title}
          <span className="rule-id mono">{run.rule_id}</span>
        </h3>
        <p className={`row-detail${lead ? " row-detail--lead" : ""}`}>{run.message}</p>
        {run.reason ? <p className="row-reason">{run.reason}</p> : null}
        <RunInputs run={run} />
      </div>
    </div>
  );
}

export function RunInputs({ run }: { run: RuleRun }) {
  if (run.inputs.length === 0 && run.pages.length === 0) return null;
  return (
    <details className="row-more">
      <summary className="row-more-summary">What this was read from</summary>
      <dl className="inputs">
        {run.inputs.map((i) => (
          <div className="inputs-pair" key={i.label}>
            <dt className="inputs-label">{i.label}</dt>
            <dd className="inputs-value mono">
              {i.value === null ? <span className="absent">— not read</span> : i.value}
            </dd>
          </div>
        ))}
        {run.pages.length > 0 ? (
          <div className="inputs-pair">
            <dt className="inputs-label">Pages</dt>
            <dd className="inputs-value mono">
              {run.pages.map((p) => `p. ${p.page_num}`).join(" · ")}
            </dd>
          </div>
        ) : null}
        <div className="inputs-pair">
          <dt className="inputs-label">Key</dt>
          <dd className="inputs-value mono">{run.key}</dd>
        </div>
      </dl>
    </details>
  );
}
