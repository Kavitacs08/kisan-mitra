#!/usr/bin/env bash
# Prompt 21 — deploy the backend to Cloud Run. Not run in this session (no
# GCP project configured) — fill in PROJECT_ID and run this from the repo root.
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID first}"
REGION="${GCP_REGION:-asia-south1}"
SERVICE_NAME="kisan-mitra-backend"

gcloud config set project "$PROJECT_ID"

gcloud builds submit --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" -f deploy/Dockerfile .

gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "USE_MOCK=false,GCP_PROJECT_ID=${PROJECT_ID},VERTEX_AI_SEARCH_DATASTORE=tomato-disease-guide" \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest"

echo "Deployed. Fetch the service URL with:"
echo "  gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)'"
