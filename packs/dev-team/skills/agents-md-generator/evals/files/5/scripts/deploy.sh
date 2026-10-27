#!/usr/bin/env bash
# Deploy sensor-ingest to the production ingest host and restart the service.
# Run by the on-call engineer only, from main, over the operations VPN.
set -euo pipefail
rsync -az --delete src/ ingest-prod.tidewater.test:/opt/sensor-ingest/src/
ssh ingest-prod.tidewater.test 'sudo systemctl restart sensor-ingest'
