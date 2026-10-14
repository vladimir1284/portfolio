// Shared pieces of the retrieval endpoint. Underscore-prefixed files are not
// routed by Pages, so this is a module and not an endpoint.

import corpus from "../../rag/corpus.json";
import vectors from "../../rag/vectors.json";

export interface Chunk {
  id: string;
  /** `en`, `es`, or `*` for a source citable from either language. */
  lang: string;
  kind: string;
  title: string;
  url: string;
  text: string;
}

/** The slice of the Pages Functions context these endpoints use. */
export interface Ctx {
  request: Request;
  env: Env;
}

export type Handler = (ctx: Ctx) => Promise<Response>;

/** `caches.default` is a Workers extension, absent from the DOM lib. */
export const edgeCache = (caches as unknown as { default: Cache }).default;

export interface Env {
  AI: {
    run(
      model: string,
      input: Record<string, unknown>
    ): Promise<{ data?: number[][]; response?: string }>;
  };
  /** Bearer token for /api/reindex. Unset means the endpoint is closed. */
  RAG_ADMIN_SECRET?: string;
}

/** Multilingual by necessity: the site is English and Spanish. */
export const EMBED_MODEL = "@cf/baai/bge-m3";
export const DIMS = 1024;
/** Most windows of the published PDFs one answer may draw on. */
export const PAPERS_PER_ANSWER = 2;
/** Cheapest instruct model that follows a citation format reliably. */
export const CHAT_MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8-fast";

export const CHUNKS = corpus as Chunk[];

/**
 * Corpus vectors, L2-normalised then quantised to int8. Ranking only needs the
 * ordering, and the quantisation scale is the same for every row, so it
 * cancels out and is never divided back out here.
 */
export const MATRIX: Int8Array | null = (() => {
  const index = vectors as { b64?: string; ids?: string[] };
  if (!index.b64 || !index.ids) return null;
  // A corpus rebuilt without re-running the index would silently shift every
  // row, and the answer would cite the wrong passage — the one failure mode
  // this feature cannot be allowed to have. Refuse the matrix instead, which
  // degrades to the precomputed questions.
  if (index.ids.length !== CHUNKS.length) return null;
  for (let i = 0; i < CHUNKS.length; i++) {
    if (index.ids[i] !== CHUNKS[i].id) return null;
  }
  const bin = atob(index.b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Int8Array(bytes.buffer);
})();

export function normalise(vector: number[]): Float32Array {
  const out = new Float32Array(vector.length);
  let sum = 0;
  for (let i = 0; i < vector.length; i++) sum += vector[i] * vector[i];
  const norm = Math.sqrt(sum) || 1;
  for (let i = 0; i < vector.length; i++) out[i] = vector[i] / norm;
  return out;
}

export async function embed(env: Env, texts: string[]): Promise<Float32Array[]> {
  const result = await env.AI.run(EMBED_MODEL, { text: texts });
  const data: number[][] = result?.data ?? [];
  return data.map(normalise);
}

export interface Hit {
  chunk: Chunk;
  score: number;
}

/**
 * Brute-force cosine over the whole corpus. A hundred-odd vectors is a few
 * hundred thousand multiply-adds — a managed vector index would be
 * infrastructure for its own sake at this size.
 */
export function search(query: Float32Array, lang: string, k: number): Hit[] {
  if (!MATRIX) return [];
  const hits: Hit[] = [];
  for (let row = 0; row < CHUNKS.length; row++) {
    const chunk = CHUNKS[row];
    if (chunk.lang !== "*" && chunk.lang !== lang) continue;
    const base = row * DIMS;
    let dot = 0;
    for (let i = 0; i < DIMS; i++) dot += MATRIX[base + i] * query[i];
    // Back to roughly a cosine, so the floor the caller applies means something.
    hits.push({ chunk, score: dot / 127 });
  }
  hits.sort((a, b) => b.score - a.score);

  // A paper is split into twenty-odd overlapping windows that all score alike,
  // so without a cap they take most of the slots and push out the one passage
  // that actually answers. Measured: "¿Qué sustituyó en la cadena de radar?"
  // lost the RCP stage — the passage naming Gematronik — to four windows of
  // the same PDF.
  const picked: Hit[] = [];
  let papers = 0;
  for (const hit of hits) {
    if (hit.chunk.kind === "paper") {
      if (papers >= PAPERS_PER_ANSWER) continue;
      papers++;
    }
    picked.push(hit);
    if (picked.length >= k) break;
  }
  return picked;
}

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}
