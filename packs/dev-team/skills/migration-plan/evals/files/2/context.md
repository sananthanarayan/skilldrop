# Donor records migration: DonorTrack 4 -> Haemora Cloud

Northvale Blood Service is replacing its donor records system.

## Legacy: DonorTrack 4 (on-premises)
- No API and no change-data capture. The only way out is a full CSV export, which runs
  nightly at 01:00 and takes about 3 hours.
- Vendor support ends 31 January 2027.

## New: Haemora Cloud
- Bulk import endpoint; upserts by donor_id.
- Staging and production tenants.

## How the service works
- 23 fixed donor centres, online all day.
- 6 mobile collection vans run DonorTrack 4 offline on laptops and sync to the central
  DonorTrack database when they are back at the depot, which can be up to 3 days later.
- Clinical rule: a donor with an active deferral must never be bled. Nurses check deferral
  status on screen at registration.

## Notes from the IT lead
"Deferral codes map 1:1 between the two systems, so there's no work needed there. Trial import
was a success (see trial-import-summary.txt)."

## The ask
Leadership wants a cutover date of 1 December. Field mapping is in field-mapping.csv and the
deferral code table is in deferral-codes.csv.
