#!/usr/bin/env bash
# Deploys the fully client-side frontend to Firebase Hosting's free Spark
# plan -- no backend, no billing, no credit card needed. Create a brand-new
# Firebase project directly at https://console.firebase.google.com first
# (do NOT import an existing GCP project that already has billing linked --
# that inherits the paid Blaze plan). Then from the deploy/ directory:
#   firebase login
#   firebase use <project-id>
#   bash deploy_firebase.sh
#
# Before deploying, refresh the district dashboard snapshot if the
# underlying data changed: `python ../scripts/export_dashboard_json.py`
set -euo pipefail
firebase deploy --only hosting --config firebase.json
