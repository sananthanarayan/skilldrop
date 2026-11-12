# DD-003: No ORM in services

Status: Accepted
Date: 2022-07-19
Deciders: T. Lindqvist
Governs: services/

Services use hand-written SQL kept in db/queries/. No ORM: we want query plans reviewable in code
review and no lazy-loading surprises on hot paths.
