import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { caseQuery, saveReview } from "../../data/api";

/* Her own record against one finding.
 *
 * The four states are the backend's (store.REVIEW_STATES) and the wording is
 * hers, not the system's — "I have checked this", not "REVIEWED". Accepting a
 * risk is a different act from having checked something, and waiting on a
 * document is a different act again; one "done" checkbox would flatten all
 * three into a lie.
 *
 * Marking a finding reviewed feeds back into derive_case, which changes the open
 * set — so the checklist, the tab counts, the "Checked by you" meter and the
 * readiness gate all move. That is why this invalidates the whole case query
 * rather than patching a row: seeing the meters move IS the proof that the
 * findings were computed rather than written.
 *
 * Nothing here is ever overwritten. The backend appends, so a correction to a
 * note is a new note and the old one stays readable.
 */

const STATES: Array<[string, string]> = [
  ["reviewed", "I have checked this"],
  ["accepted", "I am accepting the risk"],
  ["awaiting_document", "Waiting on a document"],
  ["open", "Still open"],
];

export function ReviewForm({ caseId, runKey }: { caseId: string; runKey: string }) {
  const qc = useQueryClient();
  const [state, setState] = useState("reviewed");
  const [note, setNote] = useState("");

  const save = useMutation({
    mutationFn: saveReview,
    onSuccess: () => qc.invalidateQueries({ queryKey: caseQuery(caseId).queryKey }),
  });

  return (
    <form
      className="review-form"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate({ case_id: Number(caseId), key: runKey, state, note });
      }}
    >
      <p className="inputs-label">Your call</p>

      <div className="review-states">
        {STATES.map(([value, label]) => (
          <label className="radio" key={value}>
            <input
              type="radio"
              name={`state-${runKey}`}
              value={value}
              checked={state === value}
              onChange={() => setState(value)}
            />
            {label}
          </label>
        ))}
      </div>

      <label className="sr-only" htmlFor={`note-${runKey}`}>
        Your note on this check
      </label>
      <textarea
        id={`note-${runKey}`}
        rows={2}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Add a note for the file — it appears in the report you hand over"
      />

      <p className="review-actions">
        <button className="btn" type="submit" disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save to the file"}
        </button>
        {save.isSuccess ? <span className="review-flag">Saved to the file</span> : null}
        {save.isError ? (
          <span className="review-error" role="alert">
            That did not save. Nothing was recorded — try again.
          </span>
        ) : null}
      </p>
    </form>
  );
}
