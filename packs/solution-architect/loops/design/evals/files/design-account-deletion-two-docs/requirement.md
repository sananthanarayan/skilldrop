# REQ-41: Members can delete their account

**Status:** Ratified by product review, 2 November 2026
**Owner:** Lior Asante (Product, Stridewell)

Stridewell is a running-club app: members log runs, join club challenges and message
club-mates.

## The requirement

1. A member can delete their account from Settings.
2. After they confirm, there is a 7-day cooling-off period. Logging in during those
   7 days cancels the deletion.
3. When the cooling-off period ends, all of the member's personal data is removed from
   every Stridewell system within 30 days.
4. The member gets a confirmation email when deletion is complete.
5. Messages the member sent to club chats are removed, not anonymised.
6. Club challenge leaderboards keep their totals, but the member's name and photo are gone.

## Data we hold per member

- Profile (name, email, photo, date of birth) in the `members` table
- Run logs with GPS traces in the `runs` table
- Club chat messages in the `messages` table
- Photos in the media store, referenced from `members.photo_key`
- A nightly pseudonymised copy in the analytics warehouse (see ADR-0007)
- Nightly database backups (see ADR-0006)
