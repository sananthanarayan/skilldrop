# invoice-export — service notes

Owner: billing-platform team (Pellmoor)
Status: soft launch since 2026-10-06, enabled for all customers on the Business plan

## What it does

Customers click "Export invoices" in the web app and pick a date range and a format (CSV or PDF bundle). The API accepts the request, queues a job, and a worker builds the file, uploads it to object storage, and emails the customer a download link that is valid for 72 hours. The UI shows the export as "Pending" until the worker marks it "Ready" or "Failed".

## Components

- `export-api` — 3 pods behind the internal gateway. Endpoints: `POST /v1/exports`, `GET /v1/exports/{id}`.
- `export-worker` — Kubernetes deployment, 6 pods, each pod runs N concurrent jobs (setting: `WORKER_CONCURRENCY`, currently 8). Memory limit 2 GiB per pod.
- Job queue — the shared platform job queue, queue name `invoice-export`.
- Postgres read replica `billing-replica-2` — workers read invoice rows from here.
- Object storage bucket `exports.pellmoor.example`.
- Email — the shared notifications service sends the "your export is ready" email.

## Traffic

- About 12,000 export requests a day.
- Peak is Monday 09:00–10:00 UTC (month-end and Monday morning are the busiest).
- Typical CSV export finishes in under 1 minute; PDF bundles of 500+ invoices can take 3–4 minutes.

## What product has told customers

The help-centre article says "most exports are ready within 5 minutes". There is no contractual SLA for exports.

## Current monitoring

- Grafana dashboard "export-worker" with CPU and memory per pod.
- One alert: `ExportWorkerHighCPU` — worker CPU > 80% for 5 minutes, pages the on-call. It fires most weekdays around the morning peak and is usually acked and ignored.
- No alert on queue depth, job age, or failed exports.
- Logs go to the central log store; no tracing yet.

## Deploy and rollback

- Deploys go out through CI to production with Helm. No canary; all worker pods are replaced in one rolling update.
- Rollback: `helm rollback invoice-export <revision> -n billing`
- Current release cadence: 2–3 deploys a week.

## On-call

- Primary: billing-platform weekly rota in the paging tool.
- Escalation: billing-platform team lead (Dana Okafor), then the platform on-call for queue or database problems.
- Support raise issues in #billing-incidents.
