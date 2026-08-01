import type { RuleRun } from "../../data/types";
import { OUTCOME_GLYPH, OUTCOME_TONE, OUTCOME_WORD } from "../../data/types";
import { PageButton, SourceButton } from "./rail";
import { ReviewForm } from "./ReviewForm";

export function RunRow({
  run,
  lead,
  caseId,
}: {
  run: RuleRun;
  lead?: boolean;
  caseId?: string | undefined;
}) {
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
        <RunInputs run={run} caseId={caseId} />
      </div>
    </div>
  );
}

export function RunInputs({
  run,
  caseId,
}: {
  run: RuleRun;
  caseId?: string | undefined;
}) {
  const hasEvidence = run.evidence_entry_ids.length > 0 || run.pages.length > 0;
  if (run.inputs.length === 0 && !hasEvidence && !caseId) return null;
  return (
    <details className="row-more">
      <summary className="row-more-summary">What this was read from</summary>

      <dl className="inputs">
        {run.inputs.map((i) => (
          <div className="inputs-pair" key={i.label}>
            <dt className="inputs-label">{i.label}</dt>
            <dd className="inputs-value mono">
              {i.value === null ? <span className="absent">— not read</span> : i.value}
              {/* Every value the rule read carries its own way back to the page,
                  so a finding is never asserted without the crop behind it. */}
              {i.source_entry_id !== null ? (
                <> <SourceButton entryId={i.source_entry_id} /></>
              ) : null}
            </dd>
          </div>
        ))}
        <div className="inputs-pair">
          <dt className="inputs-label">Key</dt>
          <dd className="inputs-value mono">{run.key}</dd>
        </div>
      </dl>

      {hasEvidence ? (
        <p className="rule-evidence">
          <span className="inputs-label">See it for yourself</span>{" "}
          {run.evidence_entry_ids.map((id) => (
            <SourceButton key={id} entryId={id}>
              This entry on the page
            </SourceButton>
          ))}
          {run.pages.map((p) => (
            <PageButton key={`${p.ec_id}-${p.page_num}`} ecId={p.ec_id} page={p.page_num} />
          ))}
        </p>
      ) : null}

      {caseId ? <ReviewForm caseId={caseId} runKey={run.key} /> : null}
    </details>
  );
}
