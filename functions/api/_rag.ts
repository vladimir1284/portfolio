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
/**
 * How close a second PDF has to come to take the slot a second window of the
 * PDF already cited would have had. Relative, because the absolute scores move
 * with the question. Measured over the corpus: of the 30 queries where one PDF
 * takes both slots, the best rival from another PDF is behind by between 0.008
 * and 0.304 — never ahead, since the picker walks in score order. At 0.9 the
 * near-ties change hands and a rival 0.3 behind does not.
 */
export const DOCUMENT_SPREAD = 0.9;
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

/** Walk the ranking in score order, letting through only the chosen windows. */
function take(hits: Hit[], k: number, keep: Set<Hit>): Hit[] {
  const picked: Hit[] = [];
  for (const hit of hits) {
    if (hit.chunk.kind === "paper" && !keep.has(hit)) continue;
    picked.push(hit);
    if (picked.length >= k) break;
  }
  return picked;
}

const cited = (picked: Hit[]) => picked.filter((hit) => hit.chunk.kind === "paper").length;

/**
 * The best `limit` paper windows, preferring a second document to a second
 * window of the first when the two are close.
 *
 * The three PDFs are nothing like the same size — the thesis is 126 of the 148
 * windows — so it is far likelier than the others to hold two passages near the
 * question and take both slots. It never takes one it did not outscore: the
 * picker walks in score order, so a better rival window is never displaced.
 * What it does take is a slot to a near-duplicate of its own neighbouring page,
 * and a different document only slightly behind says more than that does.
 *
 * A straight cap of one window per document was measured and rejected: it took
 * the second slot off paper altogether in 27 of 80 site-text queries, because
 * the rival it would promote sits at rank 40 to 150 and never reaches `k`.
 */
function spreadByDocument(papers: Hit[], limit: number, floor: number): Hit[] {
  // Windows of one PDF differ only by the page fragment.
  const document = (hit: Hit) => hit.chunk.url.split("#")[0];
  const taken: Hit[] = [];
  const seen = new Set<string>();
  for (const hit of papers) {
    if (taken.length >= limit) break;
    if (taken.includes(hit)) continue;
    if (seen.has(document(hit))) {
      // `papers` is sorted, so the first match is the best rival there is.
      const rival = papers.find(
        (other) =>
          !seen.has(document(other)) && other.score >= Math.max(hit.score * DOCUMENT_SPREAD, floor)
      );
      if (rival) {
        taken.push(rival);
        seen.add(document(rival));
        continue;
      }
    }
    taken.push(hit);
    seen.add(document(hit));
  }
  return taken;
}

/**
 * Brute-force cosine over the whole corpus. A hundred-odd vectors is a few
 * hundred thousand multiply-adds — a managed vector index would be
 * infrastructure for its own sake at this size.
 */
export function search(query: Float32Array, lang: string, k: number, floor = 0): Hit[] {
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
  const papers = hits.filter((hit) => hit.chunk.kind === "paper");
  const byScore = take(hits, k, new Set(papers.slice(0, PAPERS_PER_ANSWER)));
  const spread = take(hits, k, new Set(spreadByDocument(papers, PAPERS_PER_ANSWER, floor)));
  // A promoted rival can sit deep enough in the ranking that `k` fills before
  // the walk reaches it, which would spend the slot on nothing at all. Measured
  // on 4 of 80 site-text queries. Whichever selection actually seats more paper
  // wins, so spreading can only ever cost the ordering, never a citation.
  return cited(spread) >= cited(byScore) ? spread : byScore;
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
