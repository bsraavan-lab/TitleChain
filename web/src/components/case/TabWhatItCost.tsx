import type { CaseMeta, CostLine, CostPayload, CostReport } from "../../data/api";
import type { DerivedView } from "../../data/types";

/* Estimated before, actual after — from the ledger, not from a summary.
 *
 * The honesty rule is app/cost.py's and it is the whole design of this panel:
 * Sarvam publishes billing UNITS but says the per-unit rate depends on the plan,
 * so when no rate card is configured this shows units and NO rupee column at
 * all. A total filled in with a rate somebody guessed would be the one
 * fabrication in a product whose whole argument is that nothing here is guessed.
 *
 * This tab previously printed "No money figure is recorded against this case" as
 * a literal sentence while the ledger sat unread in the response — which was
 * that same fabrication with the sign flipped: an assertion about the data,
 * made without looking at it.
 *
 * Every derived value below is recomputed exactly as cost.py computes it. Those
 * are @property values on a dataclass and so never reach the JSON; recomputing
 * them is the only way this tab and the rendered one can agree.
 */

const ran = (l: CostLine) => l.calls > 0;
const tokens = (l: CostLine) => l.tokens_in + l.tokens_out;
const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
const signed = (n: number) => `${n > 0 ? "+" : ""}${n}%`;

/* Pinned to en-US because that is what Python's `{:,}` produces, and these
   figures have to match the rendered panel exactly. Bare toLocaleString() reads
   the browser's locale, and this product's readers are in India: en-IN groups
   1234567 as 12,34,567. Correct for the reader, but it would mean one case
   quoting two different numbers depending on which surface she opened. */
const group = (n: number) => n.toLocaleString("en-US");

/** cost.py Line.quantity — the unit the step is billed in, not a generic count. */
function quantity(l: CostLine) {
  if (l.stage === "digitise") return plural(l.pages, "page");
  if (l.stage === "transliterate" || l.stage === "speak") return `${group(l.chars)} chars`;
  return `${group(tokens(l))} tokens`;
}

/** cost.py RateCard.configured — any band set at all. */
const configured = (r: CostReport["rates"]) =>
  Object.keys(r.per_page).length > 0 ||
  Object.keys(r.per_million_tokens).length > 0 ||
  Object.keys(r.per_character).length > 0;

const money = (n: number, currency: string) => `${currency === "INR" ? "₹" : ""}${n.toFixed(2)}`;

/** Signed percentage, and only where both sides have a figure to compare. */
function delta(actual: CostLine, est: CostLine) {
  if (!ran(actual) || !ran(est)) return "—";
  if (tokens(est) && tokens(actual))
    return signed(Math.round(((tokens(actual) - tokens(est)) / tokens(est)) * 100));
  if (est.pages && actual.pages)
    return signed(Math.round(((actual.pages - est.pages) / est.pages) * 100));
  return "—";
}

export function TabWhatItCost({
  view,
  cost,
  meta,
}: {
  view: DerivedView;
  cost: CostPayload;
  meta: CaseMeta;
}) {
  const { estimate: est, actual: act, ledger } = cost;
  const live = act.calls > 0;
  const priced = configured(act.rates);

  // Across every document, not just the first. A case gains certificates — that
  // is what the add-a-document loop is for — and reading `docs[0]` alone both
  // under-reported the moment a second one joined and threw to the error
  // boundary on a case that had none yet.
  const pages = meta.pages_total ?? act.pages;
  const entries = view.docs.reduce((n, d) => n + d.entries.length, 0);

  return (
    <section className="section" aria-label="What it cost">
      <h2 className="section-title">What it cost</h2>

      <div className="table-scroll">
        <table className="cost">
          <thead>
            <tr>
              <th>Step</th>
              <th>Charged by</th>
              <th>We expected</th>
              <th>It actually took</th>
              <th>Difference</th>
              {priced ? <th>Cost</th> : null}
            </tr>
          </thead>
          <tbody>
            {act.lines.map((a, i) => {
              const e = est.lines[i];
              return (
                <tr key={a.stage} className={!ran(a) && !(e && ran(e)) ? "row-idle" : undefined}>
                  <td>
                    {a.label}
                    {a.models.filter(Boolean).length > 0 ? (
                      <span className="meta">{a.models.filter(Boolean).join(" · ")}</span>
                    ) : null}
                  </td>
                  <td className="meta">{a.unit}</td>
                  <td>{e && ran(e) ? quantity(e) : "—"}</td>
                  <td>
                    {ran(a) ? (
                      <>
                        {quantity(a)}
                        <span className="meta">{plural(a.calls, "call")}</span>
                        {a.cached_calls ? (
                          <span className="cached">{a.cached_calls} cached</span>
                        ) : null}
                      </>
                    ) : live ? (
                      <span className="meta">did not run</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="delta">{e ? delta(a, e) : "—"}</td>
                  {priced ? (
                    <td className="money">
                      {a.amount !== null ? (
                        <>
                          {money(a.amount, act.rates.currency)}
                          {a.cached_saving ? (
                            <span className="cached">
                              cached · would have been{" "}
                              {money(a.amount + a.cached_saving, act.rates.currency)}
                            </span>
                          ) : null}
                        </>
                      ) : (
                        <span className="meta">no rate set</span>
                      )}
                    </td>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr>
              <th>Total</th>
              <th />
              <td>
                {est.calls} calls · {group(Math.round(est.tokens))} tokens
              </td>
              <td>
                {live ? (
                  <>
                    {plural(act.calls, "call")} · {group(act.tokens)} tokens
                  </>
                ) : (
                  <span className="meta">nothing recorded yet</span>
                )}
              </td>
              <td />
              {priced ? (
                <td className="money">
                  {act.total !== null ? (
                    money(act.total, act.rates.currency)
                  ) : (
                    <span className="meta">—</span>
                  )}
                </td>
              ) : null}
            </tr>
          </tfoot>
        </table>
      </div>

      <dl className="order cost-facts">
        <div className="inputs-pair">
          <dt className="inputs-label">Pages</dt>
          <dd className="inputs-value mono">{pages || "—"}</dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Certificates</dt>
          <dd className="inputs-value mono">{view.docs.length}</dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Entries read</dt>
          <dd className="inputs-value mono">{entries}</dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Requests made</dt>
          <dd className="inputs-value mono">
            {live ? act.calls : "—"} <span className="meta">retries counted</span>
          </dd>
        </div>
        <div className="inputs-pair">
          <dt className="inputs-label">Time spent waiting</dt>
          <dd className="inputs-value mono">
            {act.wall_ms ? `${(act.wall_ms / 1000).toFixed(1)} s` : "—"}
          </dd>
        </div>
      </dl>

      {!priced ? (
        <p className="rate-warning">
          <strong>No rates set yet</strong> — so we leave the rupee columns out rather than guess at
          them. Add your per-unit rates from dashboard.sarvam.ai → Billing to{" "}
          <code>config/rates.yml</code> and this table prices itself.
        </p>
      ) : (
        <p className="meta">
          Rates from {act.rates.source ?? "an unnamed source"}
          {act.rates.retrieved ? ` · fetched ${act.rates.retrieved}` : ""}.
        </p>
      )}

      <p className="meta">
        Where the estimate comes from: {est.basis}. The actual figures are one row per real request,
        retries included. A case that needed eleven requests for four blocks cost eleven requests —
        we would rather show you that than round it off.
      </p>

      {ledger.length > 0 ? (
        <details className="ledger">
          <summary className="meta">Every request, one by one ({ledger.length})</summary>
          <div className="table-scroll">
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Step</th>
                  <th>Model</th>
                  <th>Attempt</th>
                  <th>In</th>
                  <th>Out</th>
                  <th>Pages</th>
                  <th>ms</th>
                  <th>Cached</th>
                </tr>
              </thead>
              <tbody>
                {ledger.map((r, i) => (
                  <tr key={r.id}>
                    <td>{i + 1}</td>
                    <td>{r.stage}</td>
                    <td>{r.model || "—"}</td>
                    <td>{r.ladder_rung || "—"}</td>
                    <td className="mono">{r.tokens_in ?? 0}</td>
                    <td className="mono">{r.tokens_out ?? 0}</td>
                    <td className="mono">{r.pages ?? 0}</td>
                    <td className="mono">{r.ms ?? 0}</td>
                    <td>{r.cached ? "✓" : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </section>
  );
}
