# Ledgerly 4.2 release notes

Released to all workspaces. Upgrade window: Saturday 02:00 to 04:00 UTC.

## What changed

- **Faster month-end close.** Reconciliation runs in the background, so the close screen
  no longer locks while it works.
- **New export screen.** The CSV export moved from Settings to Reports.
- ~~Bulk invoice delete~~ is postponed to 4.3.

Before:

![Export under Settings in 4.1](img/before/screen.png)

After:

![Export under Reports in 4.2](img/after/screen.png)

## How reconciliation now flows

```mermaid
flowchart LR
  Import[Bank import] --> Match[Auto-match]
  Match --> Review[Review queue]
  Review --> Close[Month-end close]
```

## Upgrading a self-hosted install

1. Back up the database.

```bash
ledgerly-admin backup --out /backups/pre-4.2.dump
```

2. Run the migration.

```bash
ledgerly-admin migrate --to 4.2
```

3. Restart the web and worker services.

## Known issues

The export screen ignores the date filter for workspaces created before 2021.[^2]

[^2]: Fixed in 4.2.1, due two weeks after this release.
