import type { DerivedView } from "../../data/types";

export function TabWhatItCost({ view }: { view: DerivedView }) {
  const doc = view.docs[0]!;
  const rows = [
    { label: "Certificates read", value: String(view.completeness.documents) },
    { label: "Pages read", value: String(doc.page_count) },
    { label: "Pages unread", value: String(view.completeness.unread_pages) },
    { label: "Entries read", value: String(doc.entries.length) },
    { label: "Checks run", value: String(view.runs.length) },
    { label: "Rulebook", value: view.rulebook_version },
  ];
  return (
    <section className="section" aria-label="What it cost">
      <h2 className="section-title">What it cost</h2>
      <table className="table">
        <tbody>
          {rows.map((r) => (
            <tr key={r.label}>
              <th scope="row">{r.label}</th>
              <td className="mono">{r.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="row-reason">
        No money figure is recorded against this case, so none is shown.
      </p>
    </section>
  );
}
