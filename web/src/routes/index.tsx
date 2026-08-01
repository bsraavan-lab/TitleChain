import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Loading, LoadError } from "../components/LoadState";
import { ApiRejection, casesQuery, samplesQuery, startSample, uploadCertificate } from "../data/api";
import type { CaseSummary } from "../data/types";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "TitleChain — Does this land certificate actually prove anything?" },
      {
        name: "description",
        content:
          "TitleChain checks whether a property certificate covers the ownership history it was bought to prove, and shows the exact spot on the page behind every finding.",
      },
      {
        property: "og:title",
        content: "TitleChain — Does this land certificate actually prove anything?",
      },
      {
        property: "og:description",
        content:
          "3 of 4 certificates in our sample could not support the search they were ordered for. TitleChain finds the gap before the signature.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function caseState(c: CaseSummary): { glyph: string; tone: string; word: string } {
  if (c.processing) return { glyph: "○", tone: "stamp", word: "Being read" };
  if (c.status === "FAILED" || c.status === "REFUSED")
    return { glyph: "⊘", tone: "muted", word: "Not usable" };
  if (c.coverage?.sufficient === false) return { glyph: "▲", tone: "seal", word: "Falls short" };
  if (c.coverage?.sufficient === true) return { glyph: "✓", tone: "fee", word: "Covered" };
  return { glyph: "●", tone: "muted", word: "Open" };
}

/* Where a case belongs, from the state it is actually in. The three screens
   already existed; only the workspace was ever linked to, so a case still being
   read and a case that broke both opened an empty one. */
function caseRoute(c: CaseSummary) {
  if (c.processing) return "/case/$caseId/working" as const;
  if (c.status === "FAILED" || c.status === "REFUSED")
    return "/case/$caseId/refusal" as const;
  return "/case/$caseId" as const;
}

function caseChip(c: CaseSummary): string {
  if (c.processing) return c.status_detail ?? "Reading it now";
  if (c.status === "FAILED" || c.status === "REFUSED") return "Needs a hand";
  if ((c.open_count ?? 0) > 0) return `${c.open_count} to look at`;
  return "Nothing left";
}

function caseSub(c: CaseSummary): string | null {
  const h = c.header;
  if (!h) return null;
  const parts: string[] = [];
  if (h.sro) parts.push(`${h.sro} SRO`);
  if (h.search_period_start && h.search_period_end)
    parts.push(`${h.search_period_start} → ${h.search_period_end}`);
  return parts.length ? parts.join(" · ") : null;
}

function Index() {
  const navigate = useNavigate();
  const cases = useQuery(casesQuery());
  const samples = useQuery(samplesQuery());
  const fileInput = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const open = (caseId: string) => navigate({ to: "/case/$caseId", params: { caseId } });

  /* A case that was just started has a header but no entries yet, so the case
     screen would render every meter at zero and every tab empty — a certificate
     that proves nothing, rather than one still being read. The working screen
     exists for exactly this minute and forwards here on its own when the
     pipeline finishes; it was simply never routed to. */
  const openWorking = (caseId: string) =>
    navigate({ to: "/case/$caseId/working", params: { caseId } });

  const upload = useMutation({
    mutationFn: uploadCertificate,
    onSuccess: (r) => void openWorking(String(r.case_id)),
  });
  const sample = useMutation({
    mutationFn: startSample,
    onSuccess: (r) => void openWorking(String(r.case_id)),
  });

  const dropError = upload.error ?? sample.error;
  const rejection = dropError instanceof ApiRejection ? dropError : null;

  return (
    <div className="page">
      <header className="masthead">
        <span className="wordmark">TitleChain</span>
        <span className="masthead-note">Property record checks</span>
      </header>

      <main>
        {/* 1 — Hero */}
        <section className="section section--hero" aria-labelledby="hero-title">
          <h1 className="hero-title" id="hero-title">
            A property search can come back clean and still prove nothing.
          </h1>
          <p className="hero-sub">
            Drop in an encumbrance certificate. In about a minute: the years it can vouch for, the
            years it cannot, and what to order to close the gap.
          </p>

          {/* The words said "Drop your certificate here" and there were no drop
              handlers, so dropping a file navigated the browser to the PDF and
              lost the upload. Either the words go or the handlers do; the
              handlers are three lines. */}
          <div
            className={`dropzone${dragging ? " is-over" : ""}`}
            onDragEnter={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragOver={(e) => e.preventDefault()}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              const f = e.dataTransfer.files?.[0];
              if (f) upload.mutate(f);
            }}
          >
            <p className="dropzone-title">Drop your certificate here</p>
            <p className="dropzone-meta">
              PDF, JPEG or PNG, up to 50 MB · reading starts the moment you pick it
            </p>
            <input
              ref={fileInput}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="sr-only"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload.mutate(f);
              }}
            />
            <button
              type="button"
              className="btn btn--filled"
              disabled={upload.isPending}
              onClick={() => fileInput.current?.click()}
            >
              Choose a file
            </button>
          </div>

          {rejection ? (
            <p className="reject-notice" role="alert">
              <span className="row-glyph glyph--seal" aria-hidden="true">
                ▲
              </span>
              <span>{rejection.detail}</span>
            </p>
          ) : dropError ? (
            <div className="reject-notice reject-notice--plain" role="alert">
              <LoadError
                what="The certificate"
                error={dropError}
                onRetry={() => {
                  upload.reset();
                  sample.reset();
                }}
              />
            </div>
          ) : null}



          {/* A div, not a p: this holds Loading (a <p>) and LoadError (a <div>),
              and isPending is true during SSR — so the server always emitted a
              <p> inside a <p> and hydration could never match. */}
          <div className="samples">
            <span className="samples-lead">Haven't got one to hand?</span>
            {samples.isPending ? <Loading what="the samples" /> : null}
            {samples.isError ? (
              <LoadError
                what="The samples"
                error={samples.error}
                onRetry={() => void samples.refetch()}
              />
            ) : null}
            {(samples.data ?? []).map((s) => (
              <button
                key={s.key}
                type="button"
                className="btn btn--ghost"
                disabled={sample.isPending}
                onClick={() => sample.mutate(s.key)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </section>

        {/* 2 — Your cases */}
        <section className="section" aria-labelledby="cases-title">
          <h2 className="section-title" id="cases-title">
            Your cases
          </h2>
          {cases.isPending ? <Loading what="your cases" /> : null}
          {cases.isError ? (
            <LoadError what="Your cases" error={cases.error} onRetry={() => void cases.refetch()} />
          ) : null}
          <ul className="caselist">
            {(cases.data ?? []).map((c) => {
              const state = caseState(c);
              const sub = caseSub(c);
              return (
                <li key={c.id}>
                  {/* A row that says "Being read" has to open the screen that
                      shows it being read, and one that says "Not usable" has to
                      open the one that says why — neither is an empty
                      workspace, which is what both used to get. */}
                  <Link
                    to={caseRoute(c)}
                    params={{ caseId: String(c.id) }}
                    className="caselist-item"
                  >
                    <span className={`row-glyph glyph--${state.tone}`} aria-hidden="true">
                      {state.glyph}
                    </span>
                    <span className="sr-only">{state.word} — </span>
                    <span className="caselist-prop">{c.property_key ?? "New case"}</span>
                    {sub ? <span className="caselist-meta mono">{sub}</span> : null}
                    <span className="chip chip--stamp caselist-chip">{caseChip(c)}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>

        {/* 3 — Measured */}
        <section className="section" aria-labelledby="measured-title">
          <h2 className="section-title" id="measured-title">
            Measured on real certificates
          </h2>
          <ul className="register">
            <li className="figure">
              <span className="figure-value mono figure-value--seal">3 of 4</span>
              <span className="figure-label">
                Certificates in our sample could not support the search they were ordered for
              </span>
            </li>
            <li className="figure">
              <span className="figure-value mono">~60s</span>
              <span className="figure-label">
                To read one, for under ₹5 — against 2.5–3 hours with a highlighter
              </span>
            </li>
            <li className="figure">
              <span className="figure-value mono">5–10 yrs</span>
              <span className="figure-label">
                How late these gaps normally surface today: at resale or foreclosure
              </span>
            </li>
          </ul>
        </section>

        {/* 4 — The problem */}
        <section className="section" aria-labelledby="problem-title">
          <h2 className="section-title" id="problem-title">
            Why a clean certificate can prove nothing
          </h2>
          <ul className="row-list">
            <li className="row row--one">
              <span className="row-glyph glyph--seal" aria-hidden="true">
                ▲
              </span>
              <p className="row-body">
                <span className="row-lead">Chosen blind.</span> You pick the years to search before
                you know anything.
              </p>
            </li>
            <li className="row row--one">
              <span className="row-glyph glyph--seal" aria-hidden="true">
                ▲
              </span>
              <p className="row-body">
                <span className="row-lead">Trails run off the edge.</span> Entries point to deeds
                outside the years you paid for.
              </p>
            </li>
            <li className="row row--one">
              <span className="row-glyph glyph--seal" aria-hidden="true">
                ▲
              </span>
              <p className="row-body">
                <span className="row-lead">Clean and useless look alike.</span> "Nothing found"
                reads the same as "wrong years".
              </p>
            </li>
          </ul>
          <p className="aside">
            An encumbrance certificate is a bank statement for a plot: every registered transaction
            in a date range you chose in advance.
          </p>
        </section>

        {/* 5 — What you get back */}
        <section className="section" aria-labelledby="output-title">
          <h2 className="section-title" id="output-title">
            What you get back
          </h2>
          <ul className="row-list">
            <li className="row row--one">
              <span className="row-glyph glyph--endorse" aria-hidden="true">
                ●
              </span>
              <p className="row-body">
                <span className="row-lead">The gap, named.</span> What this certificate leaves out,
                dated and ranked.
              </p>
            </li>
            <li className="row row--one">
              <span className="row-glyph glyph--endorse" aria-hidden="true">
                ●
              </span>
              <p className="row-body">
                <span className="row-lead">One errand, pre-filled.</span> The exact plot and years
                to order next.
              </p>
            </li>
            <li className="row row--one">
              <span className="row-glyph glyph--endorse" aria-hidden="true">
                ●
              </span>
              <p className="row-body">
                <span className="row-lead">A record, not a promise.</span> A dated handover you can
                file and forward.
              </p>
            </li>
          </ul>
        </section>

        {/* 6 — Why you can rely on it */}
        <section className="section" aria-labelledby="trust-title">
          <h2 className="section-title" id="trust-title">
            Why you can rely on it
          </h2>
          <ul className="row-list">
            <li className="row row--one">
              <span className="row-glyph glyph--fee" aria-hidden="true">
                ✓
              </span>
              <p className="row-body">
                <span className="row-lead">Nothing is guessed.</span> Fixed rules, so the same file
                gives the same answer.
              </p>
            </li>
            <li className="row row--one">
              <span className="row-glyph glyph--fee" aria-hidden="true">
                ✓
              </span>
              <p className="row-body">
                <span className="row-lead">Show me where.</span> Every finding points at its spot on
                the scanned page.
              </p>
            </li>
            <li className="row row--one">
              <span className="row-glyph glyph--fee" aria-hidden="true">
                ✓
              </span>
              <p className="row-body">
                <span className="row-lead">It admits doubt.</span> Anything unreadable is flagged,
                never quietly passed.
              </p>
            </li>
          </ul>
        </section>

      </main>

      <footer className="footnote">
        TitleChain shows what a certificate does and does not evidence. It does not give an opinion
        on title.
      </footer>
    </div>
  );
}
