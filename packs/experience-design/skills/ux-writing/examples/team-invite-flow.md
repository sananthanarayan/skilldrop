# Worked example — the copy for a team invite flow

## Input given to the skill

> We're adding "invite teammates" to Northwind Boards (project management SaaS). Flow: Team page →
> Invite button → modal with an email field (multiple, comma separated) and a role picker
> (Admin / Member) → send. There's also a Pending invites tab where you can revoke an invite. Right
> now the modal says "Add users" and the button says "Submit", and the Team page calls them
> "members" while the billing page says "seats". Voice: friendly but not cute. Web only, English only
> for now.

## Output

# Interface copy: team invite flow

**Voice:** friendly but not cute (given) → plain, "you", sentence case, no exclamation marks
**Platform:** web · **Localised:** no, so budgets have no growth allowance
**Assumptions to confirm first:**
- There is a per-send invite limit (`{limit}` below, value not given).
- Admins can manage billing and members, and Members can't. The role hint depends on this, so confirm it before shipping.
- Invites go out by email with a join link, and revoking one kills the link without emailing the invitee.

Character counts include spaces and count each `{placeholder}` as written. Leave room for the real value: an email address can run 30+ characters.

### String table

| ID | Screen | Slot | Context | Budget | Recommended (count) | Variant (count, why) |
|---|---|---|---|---|---|---|
| `invite.title` | Invite | page title | Opens from Team › Invite | 40 | "Invite people to your workspace" (31) | "Invite teammates" (16, shorter) |
| `invite.email.label` | Invite | label | Email field | 30 | "Email addresses" (15) | "Emails" (6, shorter) |
| `invite.email.hint` | Invite | hint | Under the email field | 80 | "Separate addresses with commas. You can invite up to {limit} at once." (69) | "Add one or more emails, separated by commas." (44, shorter; drops the limit) |
| `invite.role.label` | Invite | label | Role picker | 30 | "Role" (4) | "Their role" (10, warmer) |
| `invite.role.hint` | Invite | hint | Under the role picker | 80 | "Admins can manage billing and members. Members can use the workspace." (69) | "Choose what they can do in this workspace." (42, shorter; less explicit) |
| `invite.submit` | Invite | button | Primary action | 20 | "Send invites" (12) | "Invite" (6, shorter) |
| `invite.error.email_format` | Invite | error | An address isn't a valid email | 100 | "“{value}” isn't an email address. Check it for typos, like a missing @." (71) | "Check “{value}”. It needs an @ and a domain, like sam@northwind.example." (72, more explicit) |
| `invite.error.already_member` | Invite | error | Address belongs to an existing member | 100 | "{email} is already in this workspace. Remove it to send the other invites." (74) | "{email} is already a member, so we won't invite them again." (59, warmer; no action) |
| `invite.error.limit` | Invite | error | More addresses than the limit | 100 | "You can invite up to {limit} people at once. Remove {excess} to continue." (73) | "That's more than {limit}. Send these in two batches." (52, shorter) |
| `invite.error.network` | Invite | error | Request failed or timed out | 100 | "We couldn't send the invites. Check your connection and try again." (66) | "Invites not sent. Try again in a moment." (40, shorter) |
| `invite.loading` | Invite | loading | After pressing Send invites | 40 | "Sending invites…" (16) | "Sending {n} invites…" (20, more explicit) |
| `invite.success` | Invite | toast | All invites sent | 60 | "Invites sent to {n} people" (26) | "{n} invites sent. They'll get an email." (39, more explicit) |
| `pending.empty.title` | Pending invites | empty | No pending invites | 40 | "No pending invites" (18) | "Nobody's waiting to join" (24, warmer) |
| `pending.empty.body` | Pending invites | empty | Under the empty title | 100 | "People you invite show here until they accept." (46) | "Invites you send will appear here." (34, shorter) |
| `pending.empty.action` | Pending invites | button | Empty state action | 20 | "Invite people" (13) | "Send an invite" (14, warmer) |
| `pending.revoke.title` | Pending invites | dialog title | Revoke an invite | 40 | "Revoke invite for {email}?" (26) | "Revoke this invite?" (19, shorter; drops the name) |
| `pending.revoke.body` | Pending invites | dialog body | Revoke dialog | 160 | "The link in their email will stop working. You can invite them again later." (75) | "They won't be able to join with this invite. You can send a new one any time." (77, warmer) |
| `pending.revoke.confirm` | Pending invites | button | Destructive confirm | 20 | "Revoke invite" (13) | "Revoke" (6, shorter) |
| `pending.revoke.cancel` | Pending invites | button | Dismiss | 20 | "Keep invite" (11) | "Cancel" (6, shorter; less clear) |

**Recommendations, briefly:** use the recommended column throughout. "Send invites" says what the button does where "Submit" doesn't. The already-member error keeps the action ("Remove it…") because the variant leaves the user unsure whether the other invites went. "Keep invite" beats "Cancel" in the revoke dialog, because "Cancel" next to "Revoke invite" reads as "cancel the invite".

### Terminology

| Concept | Use | Avoid | Notes |
|---|---|---|---|
| A person with access | member | user, seat, teammate (in UI labels) | The billing page says "seats". Change it to "members", or explain "you pay per member". "Teammates" only in the page title variant. |
| The shared space | workspace | team, account, organisation | The Team page title already says "Team". Rename it to "Members", or flag it for `information-architecture`. |
| Asking someone to join | invite (verb and noun) | add, add users | Replaces "Add users" in the current modal |
| Withdrawing an invite | revoke | cancel, delete | Keeps "Cancel" free to mean "close this dialog" |
| Permission level | role | permission, access level | Role names: Admin, Member |

### Open questions

- What is `{limit}`, the most invites per send? The hint and the limit error need it.
- Does an invite expire? If so, add an `invite.expired` error for the invitee's landing page and say the expiry in the success toast.
- Can a Member invite, or only an Admin? If only Admins can, Members need a disabled-state hint on the Invite button.
- Should the billing page change from "seats" to "members"? That's a product decision, not a copy one.
