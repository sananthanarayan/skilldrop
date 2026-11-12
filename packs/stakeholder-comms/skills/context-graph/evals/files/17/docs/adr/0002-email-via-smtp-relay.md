# ADR-0002: Send email through the internal SMTP relay

Status: Superseded by ADR-0004
Date: 2024-03-11
Deciders: Mara Lindqvist
Governs: services/notifications/email/

Notifications sends email by connecting to the shared SMTP relay at
`smtp.internal.example.invalid`.
