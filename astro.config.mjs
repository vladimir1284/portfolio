// @ts-check
import { defineConfig } from "astro/config";

import tailwindcss from "@tailwindcss/vite";
import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
  // canonical + hreflang URLs (getAbsoluteLocaleUrl) and og:url/og:image.
  site: "https://vladimir.ladetec.com",
  i18n: {
    defaultLocale: "en",
    locales: ["en", "es"],
    routing: {
      // Default locale (en) is served UNPREFIXED at root: / = English, /es/ = Spanish.
      // Root is a real 200 page (no redirect).
      prefixDefaultLocale: false,
    },
  },
  // /en is not a real route (English is at /). Redirect it so it resolves cleanly
  // instead of 404→404.astro bounce (which logs a console 404). Other unknown
  // routes still fall through to src/pages/404.astro → /.
  redirects: {
    "/en": "/",
  },
  integrations: [
    sitemap({
      i18n: {
        defaultLocale: "en",
        locales: { en: "en", es: "es" },
      },
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
    server: {
      allowedHosts: [".trycloudflare.com"],
    },
  },
});
