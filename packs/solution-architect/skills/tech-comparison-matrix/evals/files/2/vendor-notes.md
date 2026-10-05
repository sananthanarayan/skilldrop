# Options: notes from trials and quotes

Compiled by Davide Marchetti, platform. Last touched 29 Sept 2026.

## A. Lumenstack (SaaS)
- Quote ref LS-Q-7731, dated 22 Sept 2026, valid 30 days.
- EUR 18 per host per month. Logs, metrics and traces bundled, 30-day retention included.
- Quote summary line: "140 hosts, 12 months: EUR 25,200".
- Region: Frankfurt, available now. Signed DPA available.
- SAML SSO: included.
- Two-week trial on 20 staging hosts: p95 log query 1.8 s. Pager integration worked out of the box.
- Setup effort in the trial: about 2 days for one engineer.

## B. Graywell (SaaS)
- Pricing from their sales deck of 3 March 2026: EUR 11 per host per month, 12-month commit. No formal quote yet.
- 140 hosts x 11 x 12 = EUR 18,480.
- Region: US-East only today. Sales rep email (18 Sept): "EU region is on the roadmap for Q2 2027."
- SAML SSO: on the Enterprise tier only, price on request.
- Two-week trial on 20 staging hosts: p95 log query 0.9 s. Nicest UI by far, devs loved it.
- Pager integration: via webhook, needed a small script.

## C. Self-hosted (Grafana + Loki + Prometheus on our own cluster)
- No licence cost.
- Davide's estimate of extra infra: EUR 800/month (storage + 3 nodes), so EUR 9,600/year.
- Davide's estimate of people time: 0.4 of an engineer ongoing, plus 4-6 weeks to build.
- Runs in our Amsterdam region, so EU by construction.
- SAML: supported through our identity provider, needs config.
- Not trialled. We never stood it up, so there are no query numbers.
- Bashir is the only one of us who has run Loki in production before.
