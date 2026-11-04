# Tallyhall — billing provider switch (Corvane Payments -> Haldrin Pay)

Merged to main 2–4 Nov 2026. Not deployed yet. Planned deploy: 5 Nov, 07:00 UTC.

| PR | Title | Author | Notes |
|---|---|---|---|
| #840 | Haldrin Pay client and webhook handler | Bea Lindgren | Replaces `CorvaneClient` in `billing/charge.py`. No flag; the switch happens on deploy. |
| #842 | Token import: load Haldrin token map | Bea Lindgren | Loads Haldrin's import file into `card_token_map (legacy_card_token, provider_token)`. Ran against production on 3 Nov. |
| #845 | Migration 0061: switch payment_methods to Haldrin tokens | Bea Lindgren | See `0061_switch_to_haldrin_tokens.sql`. Runs as part of the 5 Nov deploy. |
| #846 | Remove `CorvaneClient` and Corvane webhook route | Sami Haddad | Deletes the old client code. |
| #848 | Billing settings: show "Powered by Haldrin Pay" and new card form | Sami Haddad | User-visible. New card form uses Haldrin's hosted fields. |
| #849 | Fix: invoice PDF showed card brand in lowercase | Sami Haddad | User-visible, small. |
| #850 | Bump `haldrin-sdk` to 3.2.0 | deps bot | Internal. |
