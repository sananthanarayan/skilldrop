# Constraints for the observability plan

From the Head of Engineering and the Information Governance lead.

- **Budget**: our observability vendor bill is currently about $2,100 a month. Finance has capped it at $1,500 a month from January. The two biggest lines are log ingestion (about $1,300) and custom metrics (about $500); traces are about $300.
- **Health data**: patient identifiers, prescription identifiers and medication names are health data and must not be written to logs, metric labels or trace attributes. This is an Information Governance rule, not a preference.
- **On-call**: two engineers share a weekly rotation. They have asked for no more than two pages a week on average.
- **Volume for costing**: plan for about 40,000 refill requests a day.
- **Review**: we'll go through the plan in a 30-minute meeting, so keep it to about three pages.
