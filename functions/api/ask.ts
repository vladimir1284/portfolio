// POST /api/ask  →  { ok, answer, citations } | { ok: false, reason }
//
// Same origin as the site, so the CSP stays `connect-src 'self'` and there is
// no CORS to get wrong. Every failure path returns `ok: false` with a reason
// rather than an error status: the UI degrades to precomputed questions, and a
// visitor never sees a stack trace or a 502.

import { CHAT_MODEL, type Env, type Handler, edgeCache, embed, json, search } from "./_rag";

/** Below this the best match is not about the question at all. */
const FLOOR = 0.3;
/** Passages handed to the model. Six keeps the prompt near 2k tokens. */
const TOP_K = 6;
const MAX_QUESTION = 400;
/** Per-IP ceiling. Crude by construction — see `allow()`. */
const PER_MINUTE = 10;
/** Workers AI is the slow part; past this the FAQ is the better answer. */
const TIMEOUT_MS = 12_000;

const SYSTEM = {
  en: `You answer questions about Vladímir Rodríguez Diez using ONLY the numbered passages provided.
Rules, in order of precedence:
1. If the passages do not contain the answer, reply with exactly: NO_ANSWER
2. EVERY sentence ends with a citation marker: [1], or [2][3] when it draws on two passages. A sentence without a marker is a failed answer.
3. Never state a figure, date or name that is not written in a passage, and never compute one. If a passage says "since 2008", say "since 2008" — do not turn it into a number of years. Do not infer, imply, deduce or speculate. If a passage does not state it, it is not an answer.
4. English, at most 120 words, plain prose, no headings, no bullet lists.
Example of the required shape:
He rebuilt the control processor so it presents itself to ORPG as a WSR-88D RDA [2]. The archive format is NEXRAD Level-II [2][4].`,
  es: `Respondes preguntas sobre Vladímir Rodríguez Diez usando SOLO los pasajes numerados que se te dan.
Reglas, por orden de prioridad:
1. Si los pasajes no contienen la respuesta, responde exactamente: NO_ANSWER
2. CADA frase termina con una marca de cita: [1], o [2][3] si se apoya en dos pasajes. Una frase sin marca es una respuesta fallida.
3. Nunca afirmes una cifra, fecha o nombre que no esté escrito en un pasaje, y nunca la calcules. Si un pasaje dice "desde 2008", di "desde 2008" — no lo conviertas en un número de años. No infieras, no deduzcas, no especules. Si un pasaje no lo dice, no es una respuesta.
4. Español, 120 palabras como máximo, prosa, sin títulos ni viñetas.
Ejemplo de la forma exigida:
Reescribió el procesador de control para que se presente ante ORPG como un RDA WSR-88D [2]. El archivo se guarda en NEXRAD Level-II [2][4].`,
};

/** Sent back when the model answered but cited nothing. */
const REPAIR = {
  en: "Your answer had no citation marker. Rewrite it so every sentence ends with [n] pointing at the passage it came from, or reply with exactly NO_ANSWER.",
  es: "Tu respuesta no llevaba marca de cita. Reescríbela de modo que cada frase termine con [n] apuntando al pasaje de donde sale, o responde exactamente NO_ANSWER.",
};

/**
 * Per-IP rate limit on the Cache API. Two requests landing in the same
 * millisecond can both read the old count, so the ceiling is approximate; it
 * exists to stop casual hammering, not a determined attacker. The real budget
 * guard is Workers AI itself, which starts refusing once the daily neuron
 * allowance is spent — and that path lands in the same fallback.
 */
async function allow(request: Request): Promise<boolean> {
  const ip = request.headers.get("cf-connecting-ip") ?? "anon";
  const bucket = Math.floor(Date.now() / 60_000);
  const key = new Request(`https://rate.invalid/${encodeURIComponent(ip)}/${bucket}`);
  const cache = edgeCache;
  const seen = await cache.match(key);
  const count = seen ? Number(await seen.text()) || 0 : 0;
  if (count >= PER_MINUTE) return false;
  await cache.put(
    key,
    new Response(String(count + 1), { headers: { "cache-control": "max-age=120" } })
  );
  return true;
}

export const onRequestPost: Handler = async (ctx) => {
  // Retrieval scores, for tuning the floor. Gated on the admin secret, which
  // only the staging project sets — production never answers with this.
  const debug =
    Boolean(ctx.env.RAG_ADMIN_SECRET) && new URL(ctx.request.url).searchParams.get("debug") === "1";

  let question: string;
  let lang: string;
  try {
    const body = (await ctx.request.json()) as { q?: unknown; lang?: unknown };
    question = String(body.q ?? "").trim();
    lang = body.lang === "es" ? "es" : "en";
  } catch {
    return json({ ok: false, reason: "bad-request" });
  }

  if (!question || question.length > MAX_QUESTION) {
    return json({ ok: false, reason: "bad-request" });
  }
  if (!(await allow(ctx.request))) {
    return json({ ok: false, reason: "rate-limited" });
  }

  const deadline = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error("timeout")), TIMEOUT_MS)
  );

  try {
    return await Promise.race([answer(ctx.env, question, lang, debug), deadline]);
  } catch (err) {
    // Neuron allowance spent, model unavailable, or too slow. All the same to
    // the visitor, who gets the precomputed questions instead.
    console.error("ask failed", err);
    return json({ ok: false, reason: "unavailable" });
  }
};

async function answer(env: Env, question: string, lang: string, debug: boolean): Promise<Response> {
  const [queryVector] = await embed(env, [question]);
  if (!queryVector) return json({ ok: false, reason: "unavailable" });

  const scored = search(queryVector, lang, TOP_K, FLOOR);
  const trace = debug
    ? scored.map((h) => ({ id: h.chunk.id, score: Number(h.score.toFixed(3)) }))
    : undefined;
  const hits = scored.filter((h) => h.score >= FLOOR);
  if (!hits.length) return json({ ok: false, reason: "no-match", trace });

  const context = hits.map((h, i) => `[${i + 1}] ${h.chunk.title}\n${h.chunk.text}`).join("\n\n");

  const messages = [
    { role: "system", content: SYSTEM[lang as "en" | "es"] },
    { role: "user", content: `${context}\n\n---\n${question}` },
  ];

  // An 8B model drops the citation markers often enough that rejecting on the
  // first attempt would throw away good answers. One corrective round is
  // cheap — a few neurons — and it is the difference between a feature that
  // answers and one that mostly shows the fallback.
  for (let attempt = 0; attempt < 2; attempt++) {
    const result = await env.AI.run(CHAT_MODEL, {
      messages,
      max_tokens: 320,
      temperature: attempt === 0 ? 0.1 : 0,
    });
    const text = String(result?.response ?? "").trim();
    if (!text || text.includes("NO_ANSWER")) {
      return json({ ok: false, reason: "no-answer", trace });
    }

    // The invariant: an answer carries a citation and a link, or it is not
    // shown. An uncited paragraph is unverifiable, and unverifiable is the one
    // thing this feature must never put on the page.
    const used = new Set<number>();
    for (const match of text.matchAll(/\[(\d+)\]/g)) {
      const n = Number(match[1]);
      if (n >= 1 && n <= hits.length) used.add(n);
    }

    if (used.size) {
      const citations = [...used]
        .sort((a, b) => a - b)
        .map((n) => ({
          n,
          title: hits[n - 1].chunk.title,
          url: hits[n - 1].chunk.url,
          kind: hits[n - 1].chunk.kind,
        }));
      return json({ ok: true, answer: text, citations, trace });
    }

    messages.push({ role: "assistant", content: text });
    messages.push({ role: "user", content: REPAIR[lang as "en" | "es"] });
  }

  return json({ ok: false, reason: "uncited", trace });
}
