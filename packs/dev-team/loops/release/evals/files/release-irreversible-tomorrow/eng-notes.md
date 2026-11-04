# #billing-switch — notes copied from the channel, 4 Nov 2026

**Bea Lindgren** 10:12
Token import done. 31,640 cards in payment_methods, 31,228 matched in Haldrin's file. 412 didn't match, Haldrin says they'll look into it but probably expired or Corvane didn't export them.

**Sami Haddad** 10:20
those 412 get flagged needs_reentry by 0061 so the app will prompt them

**Priya Natarajan (Eng Manager)** 11:03
what's the rollback if Haldrin charges start failing?

**Bea Lindgren** 11:05
revert the deploy I guess

**Sami Haddad** 11:06
CorvaneClient is deleted in #846 but we can revert that too

**Priya Natarajan** 11:30
runbook?

**Bea Lindgren** 11:31
TODO, will write tonight

**Sami Haddad** 13:45
haven't load-tested the Haldrin client. sandbox was fine for the ~50 test charges I ran

**Priya Natarajan** 14:02
alerts?

**Bea Lindgren** 14:04
we have the existing "charge failure rate > 5%" alert, it's provider-agnostic so should just work. nothing for Haldrin webhooks yet

**Leo Marchetti (Marketing)** 15:40
heads up, the "new faster checkout" email to all customers went out at 15:00, says live from 9am tomorrow. blog post scheduled for 09:00.

**Priya Natarajan** 15:52
ok. who's on call tomorrow morning for billing?

**Sami Haddad** 15:53
me until 12, then nobody until Bea's back on Thursday
