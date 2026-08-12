import type { DerivedView, Entry, Party } from "../../data/types";
import { EditableCell } from "./EditableCell";
import { ExplainControl } from "./ExplainControl";
import { SourceButton } from "./rail";

function Names({ parties }: { parties: Party[] }) {
  if (parties.length === 0) return <span className="absent">—</span>;
  return (
    <ul className="names">
      {parties.map((p) => (
        <li key={p.name_native} className="tamil">
          {p.name_native}
        </li>
      ))}
    </ul>
  );
}

function Cell({ value, mono }: { value: string | null; mono?: boolean }) {
  if (value === null) return <span className="absent">—</span>;
  return <span className={mono ? "mono" : undefined}>{value}</span>;
}

export function TabWhatWeRead({ view, caseId }: { view: DerivedView; caseId: string }) {
  const doc = view.docs[0];
  if (!doc) return <p className="meta">Nothing has been read from this case yet.</p>;
  return (
    <section className="section" aria-label="What we read">
      <h2 className="section-title">
        {doc.label} · {doc.filename}
      </h2>
      <dl className="order">
        <div className="inputs-pair">
          <dt className="inputs-label">SRO</dt>
          <dd className="inputs-value">{doc.header.sro}</dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Village</dt>
          <dd className="inputs-value">{doc.header.village}</dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Survey</dt>
          <dd className="inputs-value mono">{doc.header.survey_details.join(" · ")}</dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Period</dt>
          <dd className="inputs-value mono">
            {doc.header.search_period_start} → {doc.header.search_period_end}
          </dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Issued</dt>
          <dd className="inputs-value mono">{doc.header.issue_date}</dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Entries declared</dt>
          <dd className="inputs-value mono">{doc.header.declared_entry_count}</dd>
        </div>
      </dl>

      <ul className="row-list entries">
        {doc.entries.map((e) => (
          <li key={e.sr_no}>
            <EntryCard entry={e} caseId={caseId} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function EntryCard({ entry, caseId }: { entry: Entry; caseId: string }) {
  return (
    <article className="entry">
      <header className="entry-head">
        <span className="kicker">Entry {entry.sr_no}</span>
        <span className="mono entry-doc">{entry.doc_no}</span>
        {entry.db_id !== null ? <SourceButton entryId={entry.db_id} /> : null}
      </header>
      {/* Its own block, not a header link: when it opens it is a paragraph and
          a voice, and a paragraph does not belong inside a header row. */}
      {entry.db_id !== null ? <ExplainControl target={{ entryId: entry.db_id }} /> : null}
      <dl className="entry-grid">
        <Field label="Nature">
          <EditableCell
            caseId={caseId}
            entryId={entry.db_id}
            field="nature"
            label="Nature"
            value={entry.nature}
            mono={false}
          />
        </Field>
        <Field label="Document year">
          <Cell value={entry.doc_year === null ? null : String(entry.doc_year)} mono />
        </Field>
        <Field label="Executed">
          <EditableCell
            caseId={caseId}
            entryId={entry.db_id}
            field="date_execution"
            label="Executed"
            value={entry.date_execution}
          />
        </Field>
        <Field label="Presented">
          <Cell value={entry.date_presentation} mono />
        </Field>
        <Field label="Registered">
          {/* The field R9 fires on when the reader could not make it out. It is
              a control, not a blank: absence is a task. */}
          <EditableCell
            caseId={caseId}
            entryId={entry.db_id}
            field="date_registration"
            label="Registered"
            value={entry.date_registration}
          />
        </Field>
        <Field label="Volume / page">
          <Cell value={entry.volume_page} mono />
        </Field>
        <Field label="Consideration">
          <Cell value={entry.consideration_value} mono />
        </Field>
        <Field label="Market value">
          {entry.market_value === null ? (
            <span className="absent">—</span>
          ) : (
            <span className="tamil">{entry.market_value}</span>
          )}
        </Field>
        <Field label="Executants">
          <Names parties={entry.executants} />
        </Field>
        <Field label="Claimants">
          <Names parties={entry.claimants} />
        </Field>
        <Field label="Earlier documents">
          {entry.pr_numbers.length === 0 ? (
            <span className="absent">—</span>
          ) : (
            <span className="mono">{entry.pr_numbers.map((p) => p.doc_no).join(" · ")}</span>
          )}
        </Field>
        <Field label="Remarks">
          <Cell value={entry.remarks} />
        </Field>
      </dl>
    </article>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="inputs-pair">
      <dt className="inputs-label">{label}</dt>
      <dd className="inputs-value">{children}</dd>
    </div>
  );
}
