# Notes from the data team — publishing grain_deliveries

Consumers:
- Finance: pays members weekly from this table (net weight x price_per_tonne). Runs Tuesdays 09:00.
- Logistics: plans haulage from site volumes.

What we want in the contract:
- Weights are in kg.
- moisture_pct is a percentage, 0-100.
- No personal data in this table, so no special handling needed.
- Freshness: Finance asked for deliveries to be in the table within 15 minutes of crossing the weighbridge.
- Owner: not agreed yet. The data team says weighbridge operations own it; weighbridge operations say the data team does.

Please write the contract as data-contract.yaml and give me the open issues in a few lines.
