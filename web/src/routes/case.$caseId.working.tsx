import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Loading, LoadError } from "../components/LoadState";
import { Masthead } from "../components/Masthead";
import { caseStatusQuery } from "../data/api";

export const Route = createFileRoute("/case/$caseId/working")({
  head: () => ({
    meta: [
      { title: "Reading the certificate — TitleChain" },
      {
        name: "description",
        content:
          "TitleChain is reading the certificate: pages parsed, entries lifted, checks queued. Nothing is reported until it has been read.",
      },
      { property: "og:title", content: "Reading the certificate — TitleChain" },
      {
        property: "og:description",
        content: "Live progress while the certificate is read, entry by entry.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: WorkingPage,
});

function WorkingPage() {
  const { caseId } = Route.useParams();
  const navigate = useNavigate();
  const q = useQuery({
    ...caseStatusQuery(caseId),
    refetchInterval: (query) => (query.state.data?.processing === false ? false : 2000),
  });
  const processing = q.data?.processing;
  // Straight to the reason it stopped, rather than through a workspace that
  // would only bounce her here — a case that ended FAILED has no derivation to
  // show, which is the whole point of the refusal screen.
  const refused = q.data?.status === "FAILED" || q.data?.status === "REFUSED";

  useEffect(() => {
    if (processing === false) {
      void navigate({
        to: refused ? "/case/$caseId/refusal" : "/case/$caseId",
        params: { caseId },
      });
    }
  }, [processing, refused, caseId, navigate]);

  return (
    <div className="page">
      <Masthead />

      <main>
        <section className="section" aria-labelledby="working-title">
          <p className="kicker">Case {caseId}</p>
          <h1 className="hero-title" id="working-title">
            Reading the certificate.
          </h1>
          <p className="hero-sub">
            Nothing is reported until it has been read. What is below is what has actually happened
            so far.
          </p>
        </section>

        {q.isPending ? <Loading what="the progress" /> : null}
        {q.isError ? (
          <LoadError what="The progress" error={q.error} onRetry={() => void q.refetch()} />
        ) : null}

        {q.data ? (
          <>
            <section className="section" aria-label="Progress">
              <h2 className="section-title">Where it has got to</h2>
              <ul className="row-list">
                <li className="row row--two">
                  <span
                    className={`row-glyph ${q.data.processing ? "glyph--stamp is-working" : "glyph--fee"}`}
                    aria-hidden="true"
                  >
                    {q.data.processing ? "●" : "✓"}
                  </span>
                  <div className="row-body">
                    <h3 className="row-title">
                      <span className="sr-only">
                        {q.data.processing ? "Running — " : "Done — "}
                      </span>
                      {q.data.status}
                    </h3>
                    <p className="row-detail">
                      {q.data.status_detail ?? "No further detail has been recorded."}
                    </p>
                  </div>
                </li>
              </ul>
            </section>

            <section className="section" aria-label="Read so far">
              <h2 className="section-title">Read so far</h2>
              <ul className="register">
                <li className="figure">
                  <span className="figure-value mono">{q.data.pages_total ?? "—"}</span>
                  <span className="figure-label">Pages in the file</span>
                </li>
              </ul>
            </section>
          </>
        ) : null}

        <section className="section" aria-label="Next">
          <Link to="/case/$caseId" params={{ caseId }} className="btn btn--filled">
            Open the case
          </Link>
        </section>
      </main>
    </div>
  );
}
