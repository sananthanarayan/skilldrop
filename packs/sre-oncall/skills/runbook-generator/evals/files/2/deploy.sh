#!/usr/bin/env bash
# deploy.sh: deploy a tagged release of TideFeed to tidefeed-app-01
# Usage: ./deploy.sh <release-tag>      e.g. ./deploy.sh v2.6.1
set -euo pipefail

TAG="${1:?usage: ./deploy.sh <release-tag>}"
HOST="tidefeed-app-01"

echo "Deploying TideFeed ${TAG} to ${HOST}"
ssh "${HOST}" "cd /opt/tidefeed && git fetch --tags && git checkout ${TAG}"
ssh "${HOST}" "cd /opt/tidefeed && ./manage.py migrate"
ssh "${HOST}" "sudo systemctl restart gauge-collector tidefeed-api"
ssh "${HOST}" "curl -fsS http://localhost:8080/health"
echo "Done. Deployed ${TAG}."
