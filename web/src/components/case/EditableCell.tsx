import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { caseQuery, saveCorrection } from "../../data/api";
import { SourceButton, useRail } from "./rail";

/* A value the reader could not make out is a task, not a blank.
 *
 * So an unread field renders as a button showing "—". Pressing it opens the
 * editor AND pins that entry's crop in the rail, because a registry value should
 * never be typed from memory — the page it came from is right there.
 *
 * There is no cancel button: Enter commits, Escape restores the cell untouched.
 * No cancel means no unsaved state, which means nothing to warn her about when
 * she navigates away.
 *
 * Saving re-derives server-side, so the correction visibly moves the meters, the
 * gate line and the checklist. That movement is the memory proof, not a stand-in
 * for it — it is the only way she will believe the findings were computed rather
 * than written.
 */

const EDITABLE = new Set([
  "doc_no",
  "date_registration",
  "date_execution",
  "nature",
  "market_value",
  "remarks",
]);

export function EditableCell({
  caseId,
  entryId,
  field,
  label,
  value,
  mono = true,
}: {
  caseId: string;
  entryId: number | null;
  field: string;
  label: string;
  value: string | null;
  mono?: boolean;
}) {
  const qc = useQueryClient();
  const { show } = useRail();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value ?? "");

  const save = useMutation({
    mutationFn: saveCorrection,
    onSuccess: () => {
      setEditing(false);
      void qc.invalidateQueries({ queryKey: caseQuery(caseId).queryKey });
    },
  });

  // Nothing to correct against without a database row, and the backend only
  // accepts the fields it whitelists.
  const canEdit = entryId !== null && EDITABLE.has(field);
  if (!canEdit) {
    return value === null ? (
      <span className="absent">—</span>
    ) : (
      <span className={mono ? "mono" : undefined}>{value}</span>
    );
  }

  if (editing) {
    return (
      <form
        className="edit"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate({ entry_id: entryId, field, value: draft });
        }}
      >
        <label className="sr-only" htmlFor={`v-${entryId}-${field}`}>
          {label}
        </label>
        <input
          id={`v-${entryId}-${field}`}
          value={draft}
          autoFocus
          autoComplete="off"
          placeholder={label}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setDraft(value ?? "");
              setEditing(false);
            }
          }}
        />
        <button className="btn btn-sm" type="submit" title="Enter" disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save"}
        </button>
        {save.isError ? (
          <span className="review-error" role="alert">
            Not saved
          </span>
        ) : null}
      </form>
    );
  }

  return (
    <span className="cell">
      <button
        type="button"
        className={value === null ? "absent-btn" : `cell-btn${mono ? " mono" : ""}`}
        title={value === null ? `${label} was not read — type in what the page says` : `Edit ${label}`}
        onClick={() => {
          setDraft(value ?? "");
          setEditing(true);
          // Opening the editor pins this entry's crop. A registry value is
          // never typed from memory — the page it came from arrives with the
          // input, which is the whole reason the rail is a pane and not a modal.
          show({ kind: "entry", entryId, close: true });
        }}
      >
        {value ?? "—"}
      </button>{" "}
      <SourceButton entryId={entryId} />
    </span>
  );
}
