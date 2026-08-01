/* Point the data paths at the Python app, ahead of the SSR catch-all.
 *
 * The nitro Vercel preset writes Build Output API v3, whose `config.json` owns
 * routing outright — `rewrites` in vercel.json are not consulted. Its last route
 * is `/(.*) -> /__server`, so without this every `/api/...` call would be
 * answered by the React server rather than by FastAPI.
 *
 * These have to land BEFORE the `filesystem` handler, or a path that happens to
 * match a built asset would win over the API.
 *
 * Proxying rather than pointing the client at Render directly is what keeps the
 * app and its data on one origin: no CORS, no absolute base URL, and the same
 * relative `/api/...` the dev proxy already serves. app/main.py has no CORS
 * middleware and says so in its docstring — this is why it does not need any.
 *
 * Known limit: uploads now cross Vercel's routing layer, which caps request
 * bodies well below the 50 MB pipeline.py accepts. The bundled samples are all
 * under 1.5 MB so the demo path is unaffected, but a large scan may be refused
 * by the platform — with the platform's error page rather than the app's own
 * sentence about what to do instead.
 */

import { readFileSync, writeFileSync } from "node:fs";

const BACKEND = process.env.TITLECHAIN_BACKEND ?? "https://titlechain.onrender.com";
const CONFIG = process.argv[2] ?? ".vercel/output/config.json";

// /api  — the JSON contract.        /page, /crop, /pageview — the evidence
// images, served straight from FastAPI because provenance needs no envelope.
const PROXIED = ["api", "page", "crop", "pageview", "static"];

const config = JSON.parse(readFileSync(CONFIG, "utf8"));
const routes = config.routes ?? [];

const alreadyPatched = routes.some((r) => typeof r.dest === "string" && r.dest.startsWith(BACKEND));
if (alreadyPatched) {
  console.log("[vercel-routes] already patched, leaving alone");
  process.exit(0);
}

const proxy = {
  src: `^/(${PROXIED.join("|")})/(.*)$`,
  dest: `${BACKEND}/$1/$2`,
  check: false,
};

// Insert ahead of everything, including the asset-caching rule: a request for
// /api/... is never a static asset, and ordering it first makes that explicit.
config.routes = [proxy, ...routes];

writeFileSync(CONFIG, JSON.stringify(config, null, 2));
console.log(`[vercel-routes] ${PROXIED.map((p) => "/" + p).join(", ")} -> ${BACKEND}`);
