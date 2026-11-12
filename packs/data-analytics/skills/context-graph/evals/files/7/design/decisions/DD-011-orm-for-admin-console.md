# DD-011: Allow SQLAlchemy in the admin console

Status: Accepted
Date: 2024-05-08
Deciders: R. Vidal
Amends: DD-003
Governs: services/admin-console/

The admin console is internal, low-traffic CRUD over ~40 tables. Hand-written SQL there cost more
than it saved. SQLAlchemy is allowed in services/admin-console/ only. Every other service keeps
DD-003's no-ORM rule.
