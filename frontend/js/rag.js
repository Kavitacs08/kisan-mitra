/**
 * Ports backend/rag.py 1:1 (Prompts 4 & 6 — knowledge base retrieval), then
 * extends it to index BOTH the English and Kannada disease guides so a
 * Kannada-language symptom description (e.g. from speech recognition) can
 * be grounded natively, instead of failing to match English-only documents.
 * Chunks each doc by its "Sec. N.N — Title" markers, then runs a hand-
 * rolled TF-IDF + cosine similarity search over the resulting ~60-70
 * chunks (English + Kannada). No library needed at this corpus size.
 */

const DISEASE_DOCS = [
  "bacterial_wilt.txt", "blossom_end_rot.txt", "early_blight.txt",
  "fusarium_wilt.txt", "healthy_baseline.txt", "late_blight.txt",
  "leaf_curl_virus.txt", "septoria_leaf_spot.txt", "spider_mite_damage.txt",
  "bacterial_wilt_kn.txt", "blossom_end_rot_kn.txt", "early_blight_kn.txt",
  "fusarium_wilt_kn.txt", "healthy_baseline_kn.txt", "late_blight_kn.txt",
  "leaf_curl_virus_kn.txt", "septoria_leaf_spot_kn.txt", "spider_mite_damage_kn.txt",
];

const SECTION_HEADER_RE = /Sec\.\s*(\d+\.\d+)\s*—[^\n]*/g;
const SECTION_NUM_RE = /Sec\.\s*(\d+\.\d+)/;

// A minimal English stop-word list, matching the effect of sklearn's
// TfidfVectorizer(stop_words="english") closely enough for this corpus.
const STOP_WORDS = new Set([
  "a","about","above","after","again","against","all","am","an","and","any","are","as","at",
  "be","because","been","before","being","below","between","both","but","by","can","could",
  "did","do","does","doing","down","during","each","few","for","from","further","had","has",
  "have","having","he","her","here","hers","herself","him","himself","his","how","i","if",
  "in","into","is","it","its","itself","just","me","more","most","my","myself","no","nor",
  "not","now","of","off","on","once","only","or","other","our","ours","ourselves","out",
  "over","own","same","she","should","so","some","such","than","that","the","their","theirs",
  "them","themselves","then","there","these","they","this","those","through","to","too",
  "under","until","up","very","was","we","were","what","when","where","which","while","who",
  "whom","why","will","with","you","your","yours","yourself","yourselves",
]);

// Kannada script occupies the Unicode block U+0C80-U+0CFF. Matching both
// that range and Latin letters lets the same tokenizer segment either
// language's documents and queries -- without this, a Kannada-script
// query against the (originally English-only) corpus produced zero tokens
// and therefore zero retrieval matches.
const TOKEN_RE = /[a-zಀ-೿]+/g;

function tokenize(text) {
  return (text.toLowerCase().match(TOKEN_RE) || []).filter(
    (w) => w.length > 1 && !STOP_WORDS.has(w)
  );
}

class LocalIndex {
  constructor(docs) {
    // docs: [{filename, text}]
    this.chunks = []; // {text, source_doc, section}
    for (const { filename, text } of docs) {
      const headers = [...text.matchAll(SECTION_HEADER_RE)];
      for (let i = 0; i < headers.length; i++) {
        const header = headers[i][0].trim();
        const sectionNum = header.match(SECTION_NUM_RE)[1];
        const bodyStart = headers[i].index + headers[i][0].length;
        const bodyEnd = i + 1 < headers.length ? headers[i + 1].index : text.length;
        const body = text.slice(bodyStart, bodyEnd).trim();
        if (!body) continue;
        this.chunks.push({
          text: `${header}\n${body}`,
          source_doc: filename,
          section: `Sec. ${sectionNum}`,
        });
      }
    }
    this._buildVectors();
  }

  _buildVectors() {
    const docTokens = this.chunks.map((c) => tokenize(c.text));

    // Document frequency per term, for IDF.
    const df = new Map();
    for (const tokens of docTokens) {
      for (const term of new Set(tokens)) {
        df.set(term, (df.get(term) || 0) + 1);
      }
    }
    const N = docTokens.length;
    this.idf = new Map();
    for (const [term, count] of df.entries()) {
      // Smoothed IDF, matching sklearn's default (smooth_idf=True):
      // idf = ln((1+N)/(1+df)) + 1
      this.idf.set(term, Math.log((1 + N) / (1 + count)) + 1);
    }

    this.vectors = docTokens.map((tokens) => this._vectorize(tokens));
  }

  _vectorize(tokens) {
    const tf = new Map();
    for (const term of tokens) tf.set(term, (tf.get(term) || 0) + 1);

    const vec = new Map();
    for (const [term, count] of tf.entries()) {
      const idf = this.idf.get(term);
      if (idf === undefined) continue; // term never seen in corpus (query-only word)
      vec.set(term, count * idf);
    }
    // L2 normalize, matching sklearn's default norm="l2".
    let normSq = 0;
    for (const v of vec.values()) normSq += v * v;
    const norm = Math.sqrt(normSq) || 1;
    for (const [term, v] of vec.entries()) vec.set(term, v / norm);
    return vec;
  }

  search(query, topK = 3) {
    const qVec = this._vectorize(tokenize(query));
    const scores = this.vectors.map((docVec) => cosineSim(qVec, docVec));
    const ranked = scores
      .map((score, i) => ({ score, i }))
      .filter((s) => s.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
    return ranked.map(({ score, i }) => ({
      ...this.chunks[i],
      score: Math.round(score * 1000) / 1000,
    }));
  }
}

function cosineSim(vecA, vecB) {
  let dot = 0;
  for (const [term, a] of vecA.entries()) {
    const b = vecB.get(term);
    if (b !== undefined) dot += a * b;
  }
  return dot; // both vectors are already L2-normalized
}

let _index = null;

async function getIndex() {
  if (_index) return _index;
  const docs = await Promise.all(
    DISEASE_DOCS.map(async (filename) => {
      const res = await fetch(`data/disease_docs/${filename}`);
      const text = await res.text();
      return { filename, text };
    })
  );
  _index = new LocalIndex(docs);
  return _index;
}

/**
 * Returns the top matching passages with section citations.
 * @param {string} symptomDescription
 * @param {number} topK
 * @returns {Promise<Array<{text: string, source_doc: string, section: string, score: number}>>}
 */
export async function retrieveDiseaseContext(symptomDescription, topK = 3) {
  const index = await getIndex();
  return index.search(symptomDescription, topK);
}
