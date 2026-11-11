# Schema (PostgreSQL 16)

- `visits(visit_id, household_id, site_id, visit_at timestamptz, travel_km numeric NULL)` - one
  row per household visit. A household can visit up to once a week. `travel_km` is the distance
  from the household's postcode to the site, NULL when the postcode is unknown.
- `parcel_items(item_id, visit_id, sku, qty)` - one row per item in the parcel handed over at a
  visit. A parcel has about 14 items.
- `sites(site_id, name, district)` - 11 sites across 5 districts.
- `sessions(session_id, site_id, session_date date, ran_out_before_close boolean)` - one row per
  opening session at a site.
