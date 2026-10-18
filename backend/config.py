"""Central config. USE_MOCK=true (the default) runs the whole app with no
cloud credentials: local TF-IDF search instead of Vertex AI Search, a
rule-based diagnosis engine instead of a live Gemini call, canned Kannada
translations instead of Cloud Translation, and a text-only "advisory" instead
of real Cloud Text-to-Speech audio.

Flip USE_MOCK=false and set the real credentials once you have a GCP project
and a Gemini API key — every module below checks this flag at the point where
it would otherwise call out to Google Cloud, and the real call sites are
written and marked `# REAL:` so swapping in live calls is a drop-in change,
not a rewrite.
"""
import os

USE_MOCK = os.environ.get("USE_MOCK", "true").lower() != "false"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
VERTEX_AI_SEARCH_DATASTORE = os.environ.get("VERTEX_AI_SEARCH_DATASTORE", "tomato-disease-guide")
GCP_REGION = os.environ.get("GCP_REGION", "asia-south1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
DISEASE_DOCS_DIR = os.path.join(DATA_DIR, "disease_docs")
