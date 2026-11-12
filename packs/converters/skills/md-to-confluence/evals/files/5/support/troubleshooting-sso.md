# Troubleshooting: SSO login failures

For Tier 1 agents at Lumen Desk. Work top to bottom; stop at the first fix that works.

> [!NOTE]
> Most SSO tickets are clock drift or a stale browser session. Check those first.

## Quick checks

- [ ] Ask the customer for the exact error text (screenshot if possible)
- [ ] Confirm their workspace URL ends in `.lumendesk.example`
- [ ] Ask them to try a private/incognito window

## Common errors

<details>
<summary>"SAML response not valid yet" or "expired assertion"</summary>

This is almost always clock drift on the customer's identity provider[^1].
Ask their admin to check the IdP server time. More than 3 minutes of drift will fail.

</details>

<details>
<summary>Redirect loop after login</summary>

Clear cookies for the workspace domain, then retry. If it still loops, collect a HAR file:

1. Open DevTools (<kbd>F12</kbd>)
2. Network tab, tick **Preserve log**
3. Reproduce, then right-click and **Save all as HAR**

</details>

<details>
<summary>"User not provisioned"</summary>

The user exists in the IdP but not in Lumen Desk. Check SCIM sync status[^2]:

```bash
lumenctl scim status --workspace acme-demo | grep -E "last_sync|errors" && echo "<check above>"
```

If `errors > 0`, escalate. See the [escalation matrix](./escalation-matrix.md).

</details>

## When to escalate

> [!WARNING]
> Never ask the customer to send their IdP signing certificate or private key in a ticket.

Escalate to Tier 2 if the issue is not resolved after the quick checks and the matching
section above, or if more than one user in the same workspace is affected[^3].

[^1]: Lumen Desk allows up to 180 seconds of skew.
[^2]: SCIM sync runs every 40 minutes.
