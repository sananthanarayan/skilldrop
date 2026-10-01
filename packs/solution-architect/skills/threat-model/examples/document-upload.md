# Worked example — document-upload feature → 6 ranked findings

## Input (design-doc excerpt, verbatim)

> New feature: customers upload contract PDFs for e-signing. Browser gets a presigned S3 URL from `upload-api` (authenticated), uploads directly to the `contracts` bucket, then `upload-api` enqueues a message; `doc-processor` consumes it, runs OCR via a third-party API, and writes extracted text to Postgres. Support staff can view any customer's documents in the admin panel to help with signing issues. Multi-tenant SaaS, tenant ID in the JWT.

## Output

### System summary

**Assets (ranked):** customer contracts (legal PII — top asset), extracted contract text in Postgres, S3 credentials / presigned-URL minting capability, OCR API key.
**Entry points:** `upload-api` (authn'd HTTP), direct browser→S3 upload, SQS queue into `doc-processor`, third-party OCR API responses, admin panel.
**Trust boundaries:** internet→upload-api, internet→S3 (presigned), upload-api→queue→doc-processor, doc-processor→OCR vendor (data leaves our trust domain), doc-processor→Postgres, support-staff→admin panel, tenant→tenant throughout.
[assumption] Presigned URLs are PUT-only. [assumption] OCR vendor is contractually approved for PII.

### Findings

**🟥 TM-1 — Cross-tenant document read via unscoped presigned URLs** (boundary: internet→S3; STRIDE: I, E)
Scenario: a tenant inspects their presigned URL, finds object keys are `contracts/{uuid}.pdf` with no tenant prefix; any later GET-capable URL or a key-guessing bug exposes other tenants' contracts — compromise of the top asset.
Existing mitigation: none stated in the design. Recommended: keys become `contracts/{tenant_id}/{uuid}.pdf`, minted only from the JWT's tenant claim, GET URLs scoped to prefix and ≤5 min. **Verify:** CI test fetches tenant B's key with tenant A's session — must 403.

**🟥 TM-2 — Malicious file detonates in doc-processor** (boundary: queue→doc-processor; STRIDE: T, E)
Scenario: attacker uploads a crafted PDF (parser exploit, zip bomb, SSRF-triggering embedded URL); doc-processor parses it with vendor-library defaults and processor credentials. RCE here reaches Postgres and the OCR key.
Existing mitigation: none stated. Recommended: validate content-type + size at presign and on consume; parse inside a sandboxed, least-privilege worker (no Postgres write role until post-parse); pin and patch the parser. **Verify:** corpus of hostile PDFs in CI lands in DLQ, not crash-loop or exec.

**🟧 TM-3 — Support staff can browse any tenant's contracts with no audit trail** (boundary: human→system; STRIDE: I, R; insider pass)
Scenario: a support login (insider or phished) bulk-reads contracts across tenants; the design grants "view any customer's documents" with no purpose-binding or logging — undetectable until external disclosure.
Existing mitigation: admin panel is authenticated. Recommended: case-bound access (support sees a document only via an open ticket reference), immutable audit log of every view, MFA on support accounts. **Verify:** admin-action integration test asserts the audit row; access without ticket reference → denied.

**🟧 TM-4 — Queue accepts unauthenticated/poisoned messages** (boundary: upload-api→queue; STRIDE: S, T)
Scenario: any internal workload (or attacker post-TM-2) enqueues `{tenant_id: victim, s3_key: attacker_file}`; doc-processor trusts the message and writes attacker text into the victim tenant's Postgres rows.
Existing mitigation: queue is network-internal `[assumption: flat internal trust]`. Recommended: doc-processor re-derives tenant from the S3 key prefix (post-TM-1) instead of trusting the message field; schema-validate on consume; producer allow-list via IAM. **Verify:** message with mismatched tenant/key → rejected with alert.

**🟨 TM-5 — Contract PII leaves trust domain to OCR vendor unminimized** (boundary: doc-processor→vendor; STRIDE: I)
Scenario: full contracts ship to the vendor; a vendor breach exposes the top asset with no detection on our side. Requires the vendor's failure, hence 🟨 not 🟧.
Existing mitigation: `[assumption]` contractual DPA. Recommended: confirm the DPA covers this data class; disable vendor-side retention; log per-document egress so exposure is enumerable after a vendor incident. **Verify:** vendor account settings reviewed + egress log row asserted in tests.

**🟨 TM-6 — Unbounded uploads as cost/availability attack** (boundary: internet→S3; STRIDE: D)
Scenario: a scripted tenant requests thousands of presigned URLs and uploads max-size files; S3 cost spike and OCR-queue saturation delay every tenant's processing (noisy-neighbor DoS).
Existing mitigation: authn required. Recommended: per-tenant presign rate limit + size cap at presign time; queue depth alarm with per-tenant fairness. **Verify:** load test on the presign endpoint shows throttling before queue saturation.

### n/a ledger
Repudiation at internet→S3: n/a beyond TM-3's audit log — S3 access logging assumed on. DoS at admin panel: internal user base, marginal.

### Authz / insider pass
Authz: TM-1, TM-4 (tenant→tenant). Insider: TM-3. Sweeps produced findings — no all-clear claimed.

### Questions for the team
1. Are presigned URLs PUT-only, and is there any GET path today? (confirms or escalates TM-1)
2. Does the OCR vendor contract cover contract PII, and is vendor-side retention off? (resolves TM-5's assumptions)

### Out of scope
E-signing flow itself (separate design); S3 bucket-policy review (assumed account-standard); browser-side threats (XSS) — covered by the web app's existing model.

### Revisit trigger
New entry point (e.g. email-in ingestion), new document consumer, or any change to support-access rules.
