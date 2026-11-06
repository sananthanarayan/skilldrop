# ADR-0004: Send email through the provider's HTTP API

Status: Accepted
Date: 2024-07-22
Deciders: Joaquin Ferreira
Supersedes: ADR-0002
Governs: services/notifications/email/

The SMTP relay could not give us per-message delivery status. Notifications now sends
email through the provider's HTTPS send API and records the provider message id for
every send.
