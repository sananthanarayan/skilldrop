# Eng notes: offline mode discussion, 1 Oct 2026

Present: Ines Moreau, Kwabena Asante, Halvard Nystrom (eng lead). Notes: Halvard.

## Numbers we pulled
- Last quarter (Jul-Sep 2026): 8,400 inspections submitted. 1,120 of them had at least one failed save or sync error logged. We don't log "no signal" directly; this is the closest proxy we have.
- 310 active inspectors. 64 of them are Calder County.
- Support tickets tagged "lost work" last quarter: 187.
- Device split: 71% Android tablets, 29% iPads.

## Approaches we talked through
1. Outbox queue. Keep the app as it is, but writes go to a local queue and replay when online. Smallest change. Doesn't let you open an inspection you haven't already loaded.
2. Local-first replica. Sync each inspector's assigned inspections to an on-device database, work against that, background sync both ways. Covers the full ask. More work, and needs a conflict policy.
3. CRDT-based sync library. Handles merges automatically. None of us has shipped one, and the library we looked at has no Kotlin bindings.
4. Export to a PDF form and re-key later. Support suggested it. Nobody likes it; re-keying is where errors come from.

Leaning towards 2.

## Estimate
- Option 2: 14 weeks for Ines + Kwabena, Android only. Option 1 alone would be about 5 weeks.
- They can't start until the auth migration finishes, currently planned for 14 Dec 2026.
- Needs a new server-side sync endpoint (delta pull + batched push). That's in Platform's codebase. Nobody from Platform was in this meeting and nobody has been asked yet.

## Things that worry us
- Compliance (Roisin, by email 30 Sept): "A signed inspection is a legal record. Once signed it must never be modified or overwritten, by anyone, including by sync. Countersigning by a supervisor is added as a separate record." Supervisors do open the same inspection as the inspector, usually the same day.
- Photos are the bulk of the data. We haven't measured how much space 72 hours of inspections takes on a tablet.
- No idea yet what the sync endpoint does to backend load.

## Pilot idea
Start with 12 Calder County inspectors who volunteered, then the rest of Calder, then everyone.
