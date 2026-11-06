# Security review - tenant-support agent (June 2026)

Reviewed the tenant-support agent design.

- Outbound email is restricted to the tenant's email address on file, so data can only go to the
  tenant it belongs to.
- The agent cannot access ID documents.
- Contractor tickets contain repair details only.

Outcome: approved for launch, provided the live configuration matches the above.
