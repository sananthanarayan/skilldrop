# ADR-0006: Retry failed notification sends with exponential backoff

Status: Accepted
Date: 2024-09-30
Deciders: Hana Oduya
Governs: services/notifications/retry.py

Failed sends are retried up to 5 attempts in total, with exponential backoff starting
at 2 seconds (2s, 4s, 8s, 16s). After the last attempt the message goes to the
dead-letter store.
