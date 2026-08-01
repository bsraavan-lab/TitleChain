import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <main className="stateful">
      <div className="stateful-card">
        <p className="kicker">Not found</p>
        <h1 className="stateful-title">This page is not here.</h1>
        <p className="stateful-body">
          No case matches this address. The case list is on the home screen.
        </p>
        <p className="stateful-actions">
          <Link to="/" className="quiet-link">
            Go to the case list
          </Link>
        </p>
      </div>
    </main>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <main className="stateful">
      <div className="stateful-card">
        <p className="kicker">Error</p>
        <h1 className="stateful-title">This screen could not be drawn.</h1>
        <p className="stateful-body">
          Something failed while rendering this page. Nothing was lost — no document, finding or
          case was changed.
        </p>
        <p className="stateful-actions">
          <button
            type="button"
            className="quiet-link"
            onClick={() => {
              router.invalidate();
              reset();
            }}
          >
            Try again
          </button>
          <Link to="/" className="quiet-link">
            Go to the case list
          </Link>
        </p>
      </div>
    </main>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "TitleChain" },
      {
        name: "description",
        content:
          "TitleChain reads an encumbrance certificate and tells you whether it covers the ownership chain it was bought to verify.",
      },
      { property: "og:site_name", content: "TitleChain" },
      { property: "og:title", content: "TitleChain" },
      {
        property: "og:description",
        content:
          "TitleChain reads an encumbrance certificate and tells you whether it covers the ownership chain it was bought to verify.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      {/* Required: nested routes render here. Removing <Outlet /> breaks all child routes. */}
      <Outlet />
    </QueryClientProvider>
  );
}
