# Worked example: a settings screen in German, Russian and Arabic

Input → output oracle for `locale-check`. Shows the order findings go in (what crashes, what
shows wrong, what overflows, what is only style), a mechanical fix written out, a plural set
judged by the target language, and a wording problem handed to a translator instead of
rewritten.

## Input

> Release candidate for the new Settings screen. Source is `en.json`; the translations are
> `de.json`, `ru.json` and `ar.json`. The toggle labels have 24 characters on a phone
> (`budget.json`). Good to go?

`en.json`

```json
{
  "settings": {
    "title": "Settings",
    "sync_toggle": "Sync over mobile data",
    "storage": "{used} of {total} used",
    "devices_one": "{{count}} device signed in",
    "devices_other": "{{count}} devices signed in",
    "sign_out_all": "Sign out of <b>all</b> devices?",
    "last_backup": "{when, select, today {Backed up today} yesterday {Backed up yesterday} other {Backed up on {date}}}"
  }
}
```

`de.json`

```json
{
  "settings": {
    "title": "Einstellungen",
    "sync_toggle": "Über mobile Daten synchronisieren",
    "storage": "{used} von {total} belegt",
    "devices_one": "{{count}} Gerät angemeldet",
    "devices_other": "{{count}} Geräte angemeldet",
    "sign_out_all": "Von <b>allen</b> Geräten abmelden?",
    "last_backup": "{when, select, heute {Heute gesichert} gestern {Gestern gesichert} other {Gesichert am {date}}}"
  }
}
```

`ru.json`

```json
{
  "settings": {
    "title": "Настройки",
    "sync_toggle": "Синхр. по мобильной сети",
    "storage": "Использовано {used}",
    "devices_one": "{{count}} устройство",
    "devices_other": "{{count}} устройств",
    "sign_out_all": "Выйти на <b>всех</b> устройствах?",
    "last_backup": "{when, select, today {Сохранено сегодня} yesterday {Сохранено вчера} other {Сохранено {date}}}"
  }
}
```

`ar.json`: every key present; `devices` has all six forms; `sync_toggle` is
"المزامنة عبر بيانات الجوال" (25 characters).

`budget.json`: `{"keys": {"settings.sync_toggle": 24}}`

## Output

**Not safe to ship yet: 2 failures in German, 2 in Russian and 1 in Arabic.** German's
backup line will show the fallback text for "today" and "yesterday", and Russian's storage
line drops the total.

**Failures**

| Locale | Key | What breaks | Source | Target | Fix |
|---|---|---|---|---|---|
| de | `settings.last_backup` | The select keywords were translated, so "today" and "yesterday" never match and every backup reads "Gesichert am …" | `{when, select, today {…} yesterday {…} other {…}}` | `{when, select, heute {…} gestern {…} other {…}}` | `{when, select, today {Heute gesichert} yesterday {Gestern gesichert} other {Gesichert am {date}}}` |
| ru | `settings.storage` | `{total}` dropped: the line says how much is used, not of what | `{used} of {total} used` | `Использовано {used}` | `Использовано {used} из {total}` |
| ru | `settings.devices` | Russian needs `few` and `many` as well: "3 устройств" is wrong, it's "3 устройства" | one, other | one, other | add `devices_few`: `{{count}} устройства` (2–4, 22–24, …) and `devices_many`: `{{count}} устройств` (5–20, 25–30, …); the existing `other` covers fractions |
| de | `settings.sync_toggle` | 33 characters on a 24-character toggle: it will wrap or truncate | Sync over mobile data | Über mobile Daten synchronisieren | needs a translator: a shorter wording such as "Sync über Mobilfunk" (19) for them to confirm |
| ar | `settings.sync_toggle` | 25 characters, one over the toggle's 24 | Sync over mobile data | المزامنة عبر بيانات الجوال | needs a translator |

**Warnings**

| Locale | Key | Note |
|---|---|---|
| ru | `settings.sync_toggle` | "Синхр." is an abbreviation the source doesn't use: fits the budget, but worth a translator's look |

**Not checked:** only the toggle has a budget, so the other strings' lengths weren't checked.

I haven't changed the files. I can write `de.fixed.json` and `ru.fixed.json` with the two
mechanical fixes (the select keywords and `{total}`) and the Russian plural forms; the
toggle wording stays with the translators.

## Why this is the oracle

- **Crashes and wrong screens before overflow, overflow before style.** The translated select
  keywords come first because they silently show the wrong sentence to every German user.
- **Plurals are judged by Russian's rules, not English's.** Two forms pass a read-through and
  fail every count from 2 to 4.
- **A mechanical fix is written out; a wording fix is not.** `{total}` is restored where Russian
  grammar puts it, while the over-budget toggle goes to a translator with a suggestion marked
  as one.

A cheaper pass answers "looks good, a couple of strings are long". It misses the select
keywords, because "heute" reads as a correct translation of "today", and it ships "3
устройств".
