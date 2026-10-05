# Pawsley Vets: booking rebuild, working notes

Written by Imogen Tarrant (practice systems lead), last touched 22 Sept 2026.

## Who we are

- 6 clinics. Four around Sydney (Marrickville, Newtown, Manly, Parramatta) and two in
  Brisbane (Paddington, West End).
- About 38 vets. Seven of them work at two clinics on different days of the week.
- Roughly 450 appointments a day across the group.
- About 21,000 active pets belonging to about 15,000 owners. An owner can have several pets.

## Appointment types

| Type | Length |
|---|---|
| Consult | 15 min |
| Vaccination | 15 min |
| Extended consult | 30 min |
| Surgery consult | 60 min |

Lengths will probably change (we are talking about 20-minute consults). Each type has a price,
and the price is different at each clinic.

## What the new system has to do

1. **A vet's day.** Reception pulls up every appointment for one vet on one date, in time
   order. This is the screen that is open all day at every front desk and refreshes every few
   seconds. It has to feel instant.
2. **A clinic's day.** Same thing but for every vet working at one clinic that day.
3. **Owner portal.** An owner logs in and sees the upcoming appointments for all of their pets.
4. **Free slots.** Given a vet (or a clinic) and a date, what times are still open.
5. **Monthly report.** No-show rate per clinic per month. The directors ask for this every
   month and today somebody counts it by hand from the paper diary.
6. **No double-booking a vet. Ever.** It happened 11 times last quarter. The current app checks
   whether the slot is free and then inserts, and two receptionists at different desks can both
   get through. If an appointment is cancelled, that time has to become bookable again.

## Stack

Database: Postgres 15 on the managed service (that is what the hosting invoice says).

Pasted from Devraj (contractor who maintains the current app), 18 Sept:

> the current booking app is on MySQL 8, has been since 2021. I'd just keep it there tbh,
> no reason to move

I have not chased up which of those is right.

## Other

- The existing tables are in current_tables.sql. I know they are not great.
- Not in scope for this piece of work: invoicing and payments, stock, clinical records.
