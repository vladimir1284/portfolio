// i18n config + types. Translation STRINGS live in per-locale JSON files
// (`en.json`, `es.json`) so they can be edited without touching code.
// This module only wires them together and derives the key type.

import en from "./en.json";
import es from "./es.json";

export const languages = {
  en: "English",
  es: "Español",
} as const;

export type Lang = keyof typeof languages;

export const defaultLang = "en" satisfies Lang;

/** Short code shown in the header language switcher. */
export const localeCode = {
  en: "EN",
  es: "ES",
} as const satisfies Record<Lang, string>;

/** Open Graph `og:locale` value per language. */
export const ogLocale = {
  en: "en_US",
  es: "es_ES",
} as const satisfies Record<Lang, string>;

/** Valid translation keys — derived from the default-locale dictionary. */
export type UIKey = keyof typeof en;

// Compile-time parity guard: build fails if es.json is missing any en.json key.
// (Extra keys in es.json are allowed; missing ones are not.)
es satisfies Record<UIKey, string>;

export const ui = { en, es } as const satisfies Record<Lang, Record<UIKey, string>>;
