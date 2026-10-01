# cloud-cost-review: reference

## 1. Getting a usable export

The script needs **line items in long format**: one row per resource, usage type and period, at daily granularity for preference.

| Provider | Export to use | Notes |
|---|---|---|
| AWS | Cost and Usage Report (legacy CUR) or CUR 2.0 through Data Exports, daily granularity, with resource IDs | Cost Explorer's "Download CSV" is a summary table by your chosen grouping, not line items. Use it only after reshaping into the generic layout. |
| GCP | Cloud Billing export to BigQuery (the detailed usage cost export if you want resource names), queried into a CSV | The export is nested. Flatten it with a query like the one below. |
| Azure | Cost Management export, "cost and usage details", **amortized** dataset | Amortized data spreads reservation and savings plan purchases over the usage they cover, and shows unused commitment as its own charge type. The actual-cost dataset shows purchases as one lump. |
| Anything else | The generic layout (section 2) | Rename your columns to match. |

GCP flattening query (adjust the table name; group by day to keep the file small):

```sql
SELECT
  DATE(usage_start_time)            AS usage_start_time,
  project.id                        AS project_id,
  service.description               AS service_description,
  sku.description                   AS sku_description,
  location.region                   AS location_region,
  resource.global_name              AS resource_global_name,   -- detailed export only
  TO_JSON_STRING(labels)            AS labels,
  cost_type,
  SUM(cost)                         AS cost,
  SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS credits_total
FROM `billing_project.billing_dataset.gcp_billing_export_resource_v1_XXXXXX`
WHERE usage_start_time >= TIMESTAMP('2026-08-01')
GROUP BY 1,2,3,4,5,6,7,8
```

## 2. Field mapping

The script matches headers case-insensitively and prints the mapping it used. Export schemas change between versions, so check that section of the output against your header.

| Field | AWS CUR (legacy) | AWS CUR 2.0 | GCP (flattened) | Azure cost details | Generic |
|---|---|---|---|---|---|
| Date | `lineItem/UsageStartDate` | `line_item_usage_start_date` | `usage_start_time` | `date` (or `UsageDateTime`) | `date` |
| Cost | `lineItem/UnblendedCost`, replaced by the effective cost columns for covered usage (section 3) | `line_item_unblended_cost`, same rule | `cost` + `credits_total` | `costInBillingCurrency` (or `CostInBillingCurrency`, `PreTaxCost`, `Cost`) | `cost` |
| Service | `product/ProductName`, else `lineItem/ProductCode` | `product_product_name`, else `line_item_product_code` | `service_description` | `meterCategory` (or `ServiceName`) | `service` |
| Account | `lineItem/UsageAccountId` | `line_item_usage_account_id` | `project_id` | `subscriptionName` (or `subscriptionId`) | `account` |
| Region | `product/region` (or `product/regionCode`) | `product_region_code` | `location_region` | `resourceLocation` | `region` |
| Usage type | `lineItem/UsageType` | `line_item_usage_type` | `sku_description` | `meterSubCategory` + `meterName` | `usage_type` |
| Resource | `lineItem/ResourceId` | `line_item_resource_id` | `resource_global_name` (or `resource_name`) | `resourceId` (or `InstanceId`) | `resource_id` |
| Line type | `lineItem/LineItemType` | `line_item_line_item_type` | `cost_type` | `chargeType` | `line_type` |
| Pricing | from line type | from line type | not available (see section 3) | `pricingModel` | `pricing_model` (`on_demand`, `commitment`, `spot`, `unused_commitment`) |
| Tags | `resourceTags/user:<key>` columns | `resource_tags` (JSON map) or `resource_tags_user_<key>` columns | `labels` (JSON list of key/value) or `label_<key>` columns | `tags` (JSON; the brace-less form older exports use is handled) | `tags` (JSON) or `tag_<key>` columns |

## 3. How line items are treated

The analysis basis is **usage at effective cost**. Everything else is listed separately, so totals here won't match the invoice line for line.

| Line | AWS | GCP | Azure | Treatment |
|---|---|---|---|---|
| On-demand usage | `Usage` | regular usage | `Usage` + `OnDemand` | Usage, on demand |
| Usage covered by a commitment | `SavingsPlanCoveredUsage` (uses `savingsPlan/SavingsPlanEffectiveCost`), `DiscountedUsage` (uses `reservation/EffectiveCost`) | not separable in the export | `Usage` + `Reservation`/`SavingsPlan` | Usage, commitment. The unblended cost is kept as the on-demand equivalent for coverage. |
| Commitment charges | `SavingsPlanRecurringFee`, `SavingsPlanUpfrontFee`, `RIFee`, `Fee` | SKUs starting "Commitment" | `Purchase` | Listed as commitment fees, not added to usage (that would double-count the effective cost) |
| Unused commitment | derived: fees minus covered effective cost | n/a | `UnusedReservation`, `UnusedSavingsPlan` | Usage, `unused_commitment`. This is waste. |
| Savings plan negation | `SavingsPlanNegation` | n/a | n/a | Excluded, and the amount is shown |
| Spot | usage type contains `SpotUsage` | SKU mentions Spot or Preemptible | `Spot` | Usage, spot |
| Tax, credits, discounts, refunds | `Tax`, `Credit`, discount types, `Refund` | `cost_type` tax; credits netted into cost | `Refund` | Listed separately (GCP credits are netted into usage cost) |

**Utilisation estimate** = covered effective cost ÷ commitment fees. This is exact for no-upfront savings plans. For partial or all-upfront commitments, use the provider's utilisation report.

**Coverage** = covered on-demand equivalent ÷ (covered + on-demand), over compute usage types: EC2, Fargate and Lambda usage, RDS and ElastiCache instance hours, Azure Virtual Machines, GCP instance core and RAM SKUs. The script splits on-demand cost by service, because a Compute Savings Plan doesn't cover RDS, which needs reserved instances. GCP coverage isn't computed from the export. Use the committed use discount analysis report in the console.

## 4. Evidence each category needs

| Category | Bill signal (script section) | Evidence before acting | How to get it |
|---|---|---|---|
| Idle public IP | `idle address` hot spot (AWS usage type `PublicIPv4:IdleAddress` or `ElasticIP:IdleAddress`) | None: the usage type is the proof | `aws ec2 describe-addresses` (no `AssociationId`) |
| Unattached volume | steady storage line on a volume id | Attachment state | `aws ec2 describe-volumes --filters Name=status,Values=available`; `az disk list --query "[?diskState=='Unattached']"`; `gcloud compute disks list --filter="-users:*"` |
| Old snapshots | `snapshot` hot spot growing month over month | Retention policy, and which snapshots back an AMI or image | Snapshot list with creation dates. Check the lifecycle policy. |
| Oversized instance | top resources, instance type | CPU **and** memory over at least two weeks that include the busiest period | AWS Compute Optimizer or CloudWatch (memory needs the agent), Azure Advisor, GCP machine-type recommendations |
| Non-prod running 24×7 | instance cost flat every day in a non-prod account or `env` | That nobody uses it out of hours, including batch jobs | Ask the owner. Check scheduled jobs and login history. |
| Storage tiering | storage-class line (for example `TimedStorage-ByteHrs`, standard tier) large and growing | Access frequency, object sizes, and the retrieval and minimum-duration charges of the target class | S3 Storage Lens or access logs, Azure blob access tracking, GCS storage insights |
| NAT and data transfer | `nat gateway` and `data transfer` hot spots, top movers | Source and destination of the bytes | VPC flow logs. Bytes to S3 or DynamoDB through a NAT gateway can go through a gateway VPC endpoint, which AWS doesn't charge for. |
| Logging and metrics | `observability` hot spot | Which log groups or metric namespaces drive it | Per-log-group ingestion. Hand off to `observability-plan`. |
| Commitments | coverage, utilisation, daily on-demand floor by service | That the floor workload will run for the term, and that waste in the floor is removed first | Owner confirmation, plus the provider's recommendation report |
| Untagged | tag section: shares and top untagged services | Owner for each untagged account or resource | Account and project ownership records. Enforce with tag policies. |

## 5. Saving formulas

Use only rates from the user's bill, the provider's recommendation output, or a price the user gives. Write the rate's source next to the number.

| Finding | Monthly saving |
|---|---|
| Delete idle or unattached resource | Its current monthly cost |
| Schedule non-prod | monthly cost × (1 − scheduled hours ÷ hours in month) |
| Rightsize | current cost × (1 − target price ÷ current price), with both prices from the same price source |
| Storage tier change | GB-month × (current rate − target rate) − expected retrieval charges |
| Commitment | covered on-demand equivalent × discount rate. Size it on the **daily on-demand floor** after waste removal, not the monthly average. |
| Data transfer re-route | bytes moved × (current per-GB rate − new path rate). Requires flow log evidence of the bytes. |

## 6. Scales

- **Confidence:** High (the bill proves it), Medium (one fact to check), Low (depends on evidence not yet collected).
- **Ease:** 3 = config change or deletion with no service impact. 2 = needs a test or maintenance window. 1 = re-architecture or a purchase needing approval.
- **Rank** = monthly saving × ease, showing confidence alongside. For a range, use the low end.
