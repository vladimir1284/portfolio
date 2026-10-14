// Sends the pages.dev hostname to the custom domain, so one URL is canonical.
//
// Pages' `_redirects` file matches paths, never hostnames, which is why this is
// a function. Measured on a throwaway project before it shipped: root
// middleware does run for static assets, and the `_headers` file is still
// applied to what `next()` returns — the CSP survives.
//
// The match is the project hostname exactly. Per-deployment hostnames
// (`<hash>.vladimir-portfolio.pages.dev`) are how a single deployment is
// inspected, and Cloudflare already serves them with `x-robots-tag: noindex`,
// so they are left alone.

const PAGES_HOST = "vladimir-portfolio.pages.dev";
const CANONICAL_HOST = "vladimir.ladetec.com";

interface Ctx {
  request: Request;
  next: () => Promise<Response>;
}

export const onRequest = async (ctx: Ctx): Promise<Response> => {
  const url = new URL(ctx.request.url);
  if (url.hostname !== PAGES_HOST) return ctx.next();

  url.hostname = CANONICAL_HOST;
  url.protocol = "https:";
  url.port = "";
  return Response.redirect(url.toString(), 301);
};
