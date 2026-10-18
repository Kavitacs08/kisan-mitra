#!/usr/bin/env bash
# Deploys the current branch's committed state to Firebase Hosting.
# Run this from the repo root (kisan_mitra_app/) after pulling the latest
# changes you want live. Requires:
#   - firebase login already done (see README.md "Going live")
#   - .env present locally with a real GEMINI_API_KEY (never committed --
#     each machine deploying this repo needs its own .env, see .env.example)
set -euo pipefail

echo "==> Pulling latest from origin..."
git pull --ff-only

echo "==> Regenerating frontend/js/config.js from .env..."
python scripts/generate_config.py

echo "==> Refreshing district dashboard snapshot..."
python scripts/export_dashboard_json.py

echo "==> Deploying to Firebase Hosting..."
firebase deploy --only hosting

echo "==> Done."
