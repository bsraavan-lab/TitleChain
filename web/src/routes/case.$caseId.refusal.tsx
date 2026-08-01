import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { caseQuery, samplesQuery, startSample } from "../data/api";
import { Loading, LoadError } from "../components/LoadState";

/* When there is nothing to report, and why.
 *
 * This screen used to read `view.coverage.headline`, list blocked runs, and end
 * on `view.requests[0]!` — a derivation, in other words. But the state it is
 * named after is precisely the one where no derivation exists: REFUSED means
 * nothing could be read out of the file, FAILED means the pipeline broke, and in
 * both cases `derive_case()` is never run, so the headline was blank, the list
 * was empty and the order block threw to the error boundary.
 *
 * What does exist is `case.status_detail` — the sentence the pipeline wrote when
 * it stopped. That is the whole content of this screen, and it is what the
 * rendered `_refusal.html` has always shown.
 *
 * Refusing with its reasons is on-message: the product's thesis is that it says
 * what it cannot establish rather than hiding it. Never soften the sentence.
 */

export const Route = createFileRoute("/case/$caseId/refusal")({
  head: () => ({
    meta: [
      { title: "We could not read this — TitleChain" },
      {
        name: "description",
        content:
          "Why TitleChain stopped, in the words of the step that stopped, and what is worth trying next.",
      },
      { property: "og:title", content: "We could not read this — TitleChain" },
      {
        property: "og:description",
        content: "The reason this certificate produced no findings, and the next useful thing to do.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: RefusalPage,
});

function RefusalPage() {
  const { caseId } = Route.useParams();
  const navigate = useNavigate();
  const q = useQuery(caseQuery(caseId));

  // A case that read fine has findings to show, so this screen has no business
  // holding it — someone followed a stale link.
  const refused =
    q.data?.case.status === "REFUSED" || q.data?.case.status === "FAILED";
  const settled = q.data !== undefined && !q.data.case.processing;
  useEffect(() => {
    if (settled && !refused) void navigate({ to: "/case/$caseId", params: { caseId } });
  }, [settled, refused, caseId, navigate]);

  if (q.isPending)
    return (
      <div className="page">
        <Loading what="the case" />
      </div>
    );
  if (q.isError)
    return (
      <div className="page">
        <LoadError what="The case" error={q.error} onRetry={() => void q.refetch()} />
      </div>
    );

  return <RefusalScreen status={q.data.case.status} detail={q.data.case.status_detail} />;
}

/* Exported so both faults can be rendered without a router: the two apologies
   are the point of this screen and they are worth checking. */
export function RefusalScreen({ status, detail }: { status: string; detail: string | null }) {
  const navigate = useNavigate();
  const samples = useQuery(samplesQuery());
  const sample = useMutation({
    mutationFn: startSample,
    onSuccess: (r) =>
      void navigate({ to: "/case/$caseId/working", params: { caseId: String(r.case_id) } }),
  });

  // Two different apologies, because these are two different faults. REFUSED
  // means we read the file and found no certificate in it — worth suggesting a
  // better scan. FAILED means something broke at our end, and telling her to
  // rescan a perfectly good document would be blaming her for our bug.
  const nothingRead = status === "REFUSED";

  return (
    <div className="page">
      <header className="masthead">
        <span className="wordmark">TitleChain</span>
      </header>

      <main>
        <section className="section answer answer--muted" aria-labelledby="refusal-title">
          <p className="kicker">
            <span aria-hidden="true">⊘ </span>
            {nothingRead ? "Nothing read" : "Did not finish"}
          </p>
          <h1 className="answer-title" id="refusal-title">
            {nothingRead
              ? "We could not read anything from this file."
              : "Something went wrong while we were reading this."}
          </h1>
          {detail ? <p className="answer-detail">{detail}</p> : null}
        </section>

        <section className="section" aria-label="What this means">
          <p className="row-detail">
            {nothingRead
              ? "This is as often about the scan as about the certificate. A faint copy or a page photographed at an angle will do it, and a sharper scan of the same document usually reads straight through."
              : "This one is on us, not on your file. Nothing you did caused it and nothing has been lost, so the same file is worth another go in a moment."}
          </p>

          {/* An error state is still a screen with a job: get her to the next
              useful action in one click. These carry the same weight here that
              the order block carries on a case that worked. */}
          <div className="findings-actions">
            <Link to="/" className="btn btn--filled">
              Try another file
            </Link>
            {(samples.data ?? []).map((s) => (
              <button
                type="button"
                key={s.key}
                className="btn btn--ghost"
                disabled={sample.isPending}
                onClick={() => sample.mutate(s.key)}
              >
                See {s.label} working
              </button>
            ))}
          </div>
          {sample.isError ? (
            <p className="review-error" role="alert">
              That sample would not start either. The app may be restarting — try again in a
              moment.
            </p>
          ) : null}
        </section>
      </main>

      <footer className="footnote">
        TitleChain shows what a certificate does and does not evidence. It does not give an opinion
        on title.
      </footer>
    </div>
  );
}
