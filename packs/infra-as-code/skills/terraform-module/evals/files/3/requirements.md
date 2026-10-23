# Ashgrove County Record Office — digital archive storage module

We need a reusable Terraform module for the S3 bucket that holds the record office's high-resolution scans (TIFF masters and JPEG web derivatives). Region eu-west-2.

From the collections team:
- The public website shows the JPEG derivatives, so the bucket must be publicly readable.
- Keep scans forever.
- To save money, move everything to Glacier Deep Archive after 90 days.
- Turn on versioning, and delete noncurrent versions after 30 days to keep costs down.

From the web team:
- The website is served through a CloudFront distribution that the web team manages. They will pass in its distribution ARN.

From information security (policy SEC-4):
- No S3 bucket may allow public access. Block Public Access must be on at bucket level.
- Encryption at rest with a customer-managed KMS key.

From the accessions policy:
- Every version of a master scan must be kept for 7 years after it is replaced.

Platform constraints:
- Our root configurations are pinned to AWS provider 4.x (~> 4.67) and Terraform 1.5 because of other modules; this module has to work with them.
- Tag everything with our standard tags (owner, cost_centre, environment), passed in by the caller.
