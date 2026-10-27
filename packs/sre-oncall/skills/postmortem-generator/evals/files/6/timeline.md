# INC-0412: paid invoices not marked as paid

Incident lead notes (Rhiannon). All times UTC, Thursday 8 October.

- 14:07 config change to webhook-consumer goes out (Tomasz's PR "tune consumer pool")
- 14:58 monitoring picked it up, queue depth alert
- 15:02 I declared the incident, opened #inc-0412
- 15:06 DB failover from this morning suspected
- 15:19 Kasia spots worker count dropped
- 15:25 decision to roll back #4471
- 15:35 rollback complete, service restored
- 16:20 backlog cleared
- 16:41 closed as mitigated

Detection: monitoring (queue depth alert).

Root cause: Tomasz fat-fingered the pool size (40 -> 4) and pushed it to prod without testing. He broke it. Need to have a word with him about care with prod config.

Impact: invoices paid by card or bank transfer through Paygrove stayed "awaiting payment" in Quillmere until the backlog drained. Some customers' clients may have been sent overdue reminders.

TODO for the write-up: Ade wants customer count and £ figure.
