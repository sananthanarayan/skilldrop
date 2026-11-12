# Traffic and platform numbers (from Dan, Oct 2026)

Monthly, last 90 days averaged:
- Public pageviews: 2.4M total
  - marketing (/, /pricing, /customers): 0.9M
  - docs: 1.3M
  - blog: 0.2M
- App: 180k sessions/month, avg 14 page navigations per session

Stratus Functions pricing (our plan):
- $0.40 per 1M invocations
- $0.000018 per GB-second
- functions configured at 1024 MB
- static/CDN-served requests: no per-request charge, bandwidth included up to 1 TB/month

Measured on staging with SSR on:
- avg SSR duration: 220 ms per page
- cold start p95: 900 ms
