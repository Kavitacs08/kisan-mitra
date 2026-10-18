"""Prompts 4 & 6 — knowledge base retrieval.

Mock mode: TF-IDF search over the local disease_docs/ text files, standing in
for Vertex AI Search. Same function signature either way, so swapping to the
real service later only touches the inside of `_vertex_ai_search_query`.
"""
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import DISEASE_DOCS_DIR, USE_MOCK, GCP_PROJECT_ID, VERTEX_AI_SEARCH_DATASTORE

_SECTION_RE = re.compile(r"Sec\.\s*(\d+\.\d+)")


class _LocalIndex:
    """Chunks each disease doc by its 'Sec. N.N' markers, embeds with TF-IDF."""

    def __init__(self, docs_dir):
        self.chunks = []       # list of {"text": ..., "source_doc": ..., "section": ...}
        for fname in sorted(os.listdir(docs_dir)):
            if not fname.endswith(".txt"):
                continue
            path = os.path.join(docs_dir, fname)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            parts = re.split(r"(Sec\.\s*\d+\.\d+\s*—[^\n]*)", text)
            # parts alternates: [preamble, header1, body1, header2, body2, ...]
            current_header = None
            for part in parts:
                m = _SECTION_RE.search(part)
                if m and "—" in part:
                    current_header = part.strip()
                    continue
                if current_header and part.strip():
                    section_num = _SECTION_RE.search(current_header).group(1)
                    self.chunks.append({
                        "text": current_header + "\n" + part.strip(),
                        "source_doc": fname,
                        "section": f"Sec. {section_num}",
                    })
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in self.chunks])

    def search(self, query, top_k=3):
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        ranked = sims.argsort()[::-1][:top_k]
        return [
            {**self.chunks[i], "score": round(float(sims[i]), 3)}
            for i in ranked if sims[i] > 0
        ]


_index = None


def _get_index():
    global _index
    if _index is None:
        _index = _LocalIndex(DISEASE_DOCS_DIR)
    return _index


def _vertex_ai_search_query(query, top_k=3):
    # REAL: replace this body with a call to the Vertex AI Search
    # `search` REST/SDK method against VERTEX_AI_SEARCH_DATASTORE under
    # GCP_PROJECT_ID, returning the same shape: text, source_doc, section, score.
    raise NotImplementedError(
        "Vertex AI Search is not wired up yet. Set USE_MOCK=false only after "
        "configuring GCP_PROJECT_ID and ingesting disease_docs/ into "
        f"the '{VERTEX_AI_SEARCH_DATASTORE}' data store."
    )


def retrieve_disease_context(symptom_description: str, top_k: int = 3):
    """Prompt 6 — returns the top matching passages with section citations."""
    if USE_MOCK:
        return _get_index().search(symptom_description, top_k=top_k)
    return _vertex_ai_search_query(symptom_description, top_k=top_k)


if __name__ == "__main__":
    for q in ["leaves curling upward and stunted growth",
              "dark concentric ring spots on lower leaves",
              "sudden wilting whole plant still green"]:
        print(f"\nQuery: {q}")
        for hit in retrieve_disease_context(q):
            print(f"  [{hit['score']}] {hit['source_doc']} {hit['section']}")
