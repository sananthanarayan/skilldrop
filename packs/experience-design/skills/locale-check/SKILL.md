---
name: locale-check
description: Check a product's translations against the source strings before they ship — every key present, every placeholder (named, %s, %1$d, ICU plural and select) carried over intact, the plural forms each language needs, markup tags balanced, and strings over their character budget — with a script that reads JSON, ARB, gettext .po, Android strings.xml and iOS .strings, and lists each problem with its key and locale. Use when someone asks to "check the translations", "QA these locale files", "will the German fit", "why does the French build crash on this string", or hands over locale files before a release.
---

# locale-check

Decides whether a set of translated string files is safe to ship, and says exactly what to fix
in each one. The defects that matter are mechanical and easy to miss by reading: a `{count}`
dropped from one German string, Polish shipped with two plural forms where it needs four, an
Arabic file missing `zero`, two printf arguments swapped in French, an apostrophe that stops an
Android build. A read-through of 500 strings misses them; a check of every string doesn't. This
skill does not write the source strings (that's `ux-writing`) or the page content around them
(that's `content-design`), and it does not translate.

## How to respond

1. **Run the check on the source and every target before reading anything.** The source is
   the language the product is written in, often `en`; the targets are the translations.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/locale_check.py" en.json de.json fr.json pl.json --json
   # Other IDEs (from the skill folder)
   python3 scripts/locale_check.py values/strings.xml values-ar/strings.xml values-fr/strings.xml
   python3 scripts/locale_check.py messages.pot fr.po --budget budget.json
   ```

   It reads JSON (i18next `key_one` / `key_other` plurals included), ARB, `.po` against a
   `.pot` or source `.po`, Android `strings.xml`, iOS `.strings` and `.stringsdict`. The locale
   comes from the path (`de.json`, `values-fr/`, `fr.lproj`); when a path doesn't say, pass
   `--locale` once per target, in order. A file in another format (XLIFF, YAML, a
   spreadsheet) is read by hand: list its keys, placeholders and plural forms, and apply the
   rules below to every row. Exit 0 means no failures, 1 failures, 2 a file it couldn't read.

2. **Read the source string beside every finding, and beside every reordered placeholder.**
   The check matches tokens, not meaning, so a clean result is not the answer.
   - **A reorder is valid syntax and can still be wrong.** For every target whose numbered
     placeholders (`%2$s … %1$s`, `{1} … {0}`) appear in a different order from the source,
     read both sentences and confirm each argument still fills the same role. ✅ *"de %2$s a
     %1$s" for "from %1$s to %2$s" sends the parcel the wrong way: a failure, with the fix
     "de %1$s a %2$s".* A reorder that only follows the target's word order is fine.
   - **Read in full the strings on any screen the person names** (checkout, payment, sign-in),
     whatever the check says.
   A placeholder that moved is fine only once its role is confirmed; one that vanished is not. A select keyword is code, so
   `male` translated as `masculin` breaks the branch. A plural form that exists but says the
   wrong number is still wrong. Confirm each finding against the source before reporting it.

3. **Rank by what breaks first.**
   1. **The build or the app crashes:** a file that doesn't parse, an ICU message that
      doesn't parse, an Android apostrophe without a backslash, printf arguments whose types
      changed or swapped, a missing key the code reads.
   2. **The screen shows the wrong thing:** a dropped placeholder, plural forms the language
      needs but doesn't have, markup that doesn't balance.
   3. **The screen overflows:** strings over their budget.
   4. **Style:** warnings such as possibly untranslated, punctuation dropped, a stale key.
   A warning is reported as a warning. It never sits in the failures table.

4. **Give the corrected string when the fix is mechanical, and only then.**
   - **Restore a dropped placeholder** where the sentence's grammar puts it, and say so:
     ✅ *`"Hallo, {name}!"` — restored `{name}` after the greeting, as in the source.*
   - **Number swapped printf arguments** so the order can stay as the translator wrote it:
     ✅ *`"Vous avez %2$d messages, %1$s"`.*
   - **Add a missing plural form** by repeating the language's pattern only when the
     form is regular and you are sure of it (Polish `few` for 2–4: *"2 pliki"*). Otherwise
     mark it for a translator with the numbers it covers: *"pl `few` (2–4, 22–24, …):
     needs a translator"*.
   - **Escape** an Android apostrophe as `\'`.
   - **Never write new translated text silently.** An untranslated string, a wrong meaning or a
     missing key goes to a translator with the source string, the locale and the slot. When you
     do suggest wording for a missing key, label it *suggested, for a translator to confirm*.

5. **Change no file unless asked.** Offer a patched copy of each target with the mechanical
   fixes applied, written beside the original (`de.fixed.json`), and list what it changed.

6. **Measure every length the person gives you.** A limit stated in the request ("buttons
   max 24 characters", "the German must fit a 120 px tab") is a budget: pass it with
   `--budget`, or count the characters of every string it covers, and report each one over
   with its length and the limit. Never say a string fits without counting it. Only when no
   limit is given anywhere, say in one line that lengths weren't checked, and name the slots
   most at risk (buttons, tabs, toasts).
   A format read by hand, and a locale whose plural rules aren't known, are named too.

7. **Reply in this order.** First line: whether the release is safe to ship, as a plain yes
   or no, with the count of failures by locale, counted from the table below it so the two
   agree. Then the failures, in one table per locale
   or one table with a locale column: key, what breaks, source, target, and the corrected
   string or *needs a translator*. Then the warnings, shorter. Then what wasn't checked. Write
   for the person shipping the release: no tool names, no script output pasted, no paths
   inside this skill's folder. Asked which string caused a crash, name every string that would
   cause it, and pick one only when the evidence (a log, a stack trace, a screen) says which.

**Non-interactive runs:** a limit in the request is a budget (step 6); with none anywhere,
there is no length check, and the reply says so. A missing
locale code is inferred from the strings' script and language, tagged `[assumption]`, and
listed first. Emit `BLOCKED: need the source strings and at least one translation` only when
there is no source file or no target at all; with one of several targets unreadable, check the
rest and report that one as a failure.

## Useful references in this skill

- [`scripts/locale_check.py`](scripts/locale_check.py) — every check in this skill, with CLDR plural categories for about 60 languages and gettext `nplurals` (stdlib only)
- [`examples/settings-release.md`](examples/settings-release.md) — worked example: a settings screen in German, Russian and Arabic, with translated select keywords, missing Russian plurals and a toggle over budget

## Quality bar

- **Every target is checked, every finding read against its source string.** A count with no check behind it is a guess.
- **Crashes first, then wrong screens, then overflow, then style.** The reader fixes in that order.
- **A mechanical fix comes with the corrected string;** a wording fix goes to a translator.
- **Plural forms are judged by the target language's rules,** not the source's: Polish needs four, Arabic six, Japanese one.
- **Nothing is translated or edited unasked,** and nothing is cut: a dubious string is flagged, not removed.
- **Every reordered placeholder is read for meaning,** not passed because the syntax is valid.
- **Every length limit the person states is measured.** "It fits" always has a count behind it.
- **What wasn't checked is said in one line.**

## When to use this skill

- ✅ "Check these translations before the release" with locale files
- ✅ "Why does the French build crash on this string?"
- ✅ "Will the German fit on the buttons?" with a budget or the widths
- ✅ "QA the strings the agency sent back"
- ✅ A pull request that adds or updates locale files

## When NOT to use this skill

- ❌ Writing the source strings, button labels or error messages: that's `ux-writing`
- ❌ Writing or restructuring the page content itself: that's `content-design`
- ❌ "Translate this into French": that's translation, and this skill only checks it

## Anti-patterns to avoid

- ❌ **Reading the files instead of checking them.** A dropped `{count}` in string 312 of 500 is invisible to a skim.
- ❌ **Judging plurals by the source.** English has two forms; shipping Russian with two is the bug.
- ❌ **"Fixing" a translation by rewriting it.** Restore the placeholder; leave the wording to the translator.
- ❌ **Calling a missing key a warning.** The code reads it; the user sees the raw key or the source text.
- ❌ **Calling `masculin` a good translation of `male`.** Select keywords are code, never text.
- ❌ **"Lengths look fine" with no budget.** Say they weren't checked.
- ❌ **Trusting a clean check on a reordered sentence.** `%2$s … %1$s` passes the syntax and can still swap the sender and the receiver.
- ❌ **Naming one string as the crash on a guess.** Name every candidate until the evidence picks one.
- ❌ **Pasting the raw report.** Lead with the ship decision and the fixes, by locale.
