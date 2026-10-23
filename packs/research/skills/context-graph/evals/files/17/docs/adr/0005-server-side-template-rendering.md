# ADR-0005: Render notification templates server-side

Status: Accepted
Date: 2024-08-14
Deciders: Joaquin Ferreira, Hana Oduya
Governs: services/notifications/templates/

Templates are Jinja2 files rendered inside the notifications service before sending.
Callers send a template name and variables, never pre-rendered HTML, so that every
message goes through the same escaping and branding.
