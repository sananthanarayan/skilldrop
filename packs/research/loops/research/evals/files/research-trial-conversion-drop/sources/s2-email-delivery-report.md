# Lifecycle email: incident note — onboarding sequence deliverability

Author: Ines Carvalho (Lifecycle marketing) · 2026-09-22

## What happened

On 2 September we moved lifecycle email to a new sending provider and a new sending subdomain (mail.tallyfold.example). The DKIM record for the new subdomain was published with a typo, so messages failed DKIM signing checks at the major mailbox providers.

The onboarding sequence (day 1 "Set up your books", day 3 "Connect your bank", day 7 "Your first VAT return") goes to every new trial user. It was the only sequence moved on 2 September; billing and password emails stayed on the old provider.

## Impact on the onboarding sequence

| Period | Delivered (accepted by receiving server) | Open rate |
|---|---|---|
| 1–31 Aug (old provider) | 98.1% | 52% |
| 2–19 Sep (new provider, DKIM broken) | 97.4% | 6% |
| 20–30 Sep (DKIM fixed) | 98.0% | 49% |

"Delivered" stayed high because the receiving servers accepted the messages; seed tests on 18 September showed them landing in spam folders.

The DKIM record was corrected on the evening of 19 September.

## Not known

We have not measured whether trial users who never opened the onboarding emails convert at a lower rate. That join between email events and billing has not been built.
