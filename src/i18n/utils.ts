// i18n helpers. Pure module (no `astro:*` imports) so it can be used anywhere.
// Locale URL building (switcher href, hreflang, canonical) uses the native
// `astro:i18n` helpers directly inside .astro files — see Layout/Header.

import { ui, defaultLang, languages, type Lang, type UIKey } from "./ui";

export const localeList = Object.keys(languages) as Lang[];

/** Normalize `Astro.currentLocale` to a known locale, defaulting to `defaultLang`. */
export function resolveLang(currentLocale: string | undefined): Lang {
  return currentLocale && currentLocale in ui ? (currentLocale as Lang) : defaultLang;
}

/**
 * Translator bound to a locale. Falls back to the default locale for any key
 * missing in the target locale, so a half-translated dictionary never ships an
 * empty string.
 */
export function useTranslations(lang: Lang) {
  return function t(key: UIKey): string {
    return ui[lang][key] ?? ui[defaultLang][key];
  };
}

/** The other locale to offer in the switcher (first locale that isn't `lang`). */
export function otherLang(lang: Lang): Lang {
  return localeList.find((l) => l !== lang) ?? defaultLang;
}

/**
 * Strip the locale prefix from a pathname, returning the locale-agnostic route
 * as a relative path (no leading slash) suitable for `getRelativeLocaleUrl` /
 * `getAbsoluteLocaleUrl`. The default locale is unprefixed (`prefixDefaultLocale:
 * false`), so only non-default locales carry a prefix to strip.
 * Home → '' . `/es/about` → 'about'.
 */
export function getRouteFromPathname(pathname: string, lang: Lang): string {
  const segments = pathname.split("/").filter(Boolean);
  if (lang !== defaultLang && segments[0] === lang) segments.shift();
  return segments.join("/");
}
