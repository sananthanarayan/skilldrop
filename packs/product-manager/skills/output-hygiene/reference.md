# Tell taxonomy

Two halves. The first is decided by `scripts/scrub.py` and needs no judgment. The second is
what the script cannot see, and is the reason this is a skill rather than a lint rule.

---

## Part 1 — mechanical classes (the script decides)

### auto: safe to remove without reading the sentence

| Class | Codepoints | Why it is a defect |
|---|---|---|
| invisible | U+200B ZWSP · U+200C ZWNJ · U+200D ZWJ · U+2060 WJ · U+FEFF BOM · U+00AD SHY · U+2028/2029 separators · U+202A–202E and U+2066–2069 bidi controls | Renders as nothing, survives copy-paste, and silently breaks `grep`, `diff`, string equality, and JSON round-trips. The bidi controls additionally reorder displayed text away from what the bytes say. |
| spacing | U+00A0 NBSP · U+202F NNBSP · U+2007 figure · U+2009 thin · U+200A hair · U+2002 en · U+2003 em · U+3000 ideographic | Looks exactly like a space and is not one. Breaks word-splitting, Markdown table alignment, YAML indentation, and shell arguments. |
| provenance | `Co-authored-by: Claude …` · a `Generated with … Claude Code` link footer · a trailing `— Claude` signature | Added by the harness, not chosen by the author. Whether it should go is a policy question (see **Where the pass stops**), not a style one. |
| closer | A final paragraph opening `Let me know if…`, `Hope this helps`, `Would you like me to…`, `Happy to…` | Addresses a chat partner. The reader of a shipped document is not in a conversation. |

### review: reported, never auto-applied

| Class | What it catches | Why judgment is required |
|---|---|---|
| homoglyph | A non-ASCII letter inside an otherwise-ASCII word — Cyrillic `а` U+0430 for `a`, `е` U+0435 for `e`, `о` U+043E for `o`, Greek `ο` U+03BF, `ι` U+03B9 | The ASCII letter that "looks right" is a guess, and the word may be genuinely foreign. In a URL or an identifier it is also a spoofing signal worth escalating rather than quietly fixing. |
| typography | U+2018/2019 curly singles · U+201C/201D curly doubles · U+2013 en dash · U+2014 em dash · U+2026 ellipsis · U+2032/2033 primes | Correct in Markdown prose and in anything typeset, so `--medium markdown` (the default) does not report them at all — one row per apostrophe would bury every finding that mattered. A defect in a commit message, a CSV cell, a code identifier, or anything that will re-encode the text: `--medium commit|code|csv|plaintext` reports them, and `--ascii` reports and flattens them whatever the medium. |

### Where the pass stops

The provenance class is held — reported, not removed — in four contexts:

- An academic or journal submission under an AI-disclosure rule.
- A workplace whose AI-use policy requires declaring assisted work.
- A repository whose contribution guide requires the co-author trailer.
- A regulated filing or a legal document.

In all four the report names the rule and cleans every other class. For a repository that does
*not* want the trailer, the durable fix is prospective and lives in the harness, not in a
cleaning pass: Claude Code writes it per its own settings, so turning it off there stops it at
the source and leaves history alone.

---

## Part 2 — prose tells (the model decides)

A tell is a **density**, not a word. One instance is a style choice; five in three paragraphs is
a fingerprint. Never flag an instance — flag the pattern, and quote three instances as evidence.

### The symmetric triple

❌ *"The migration is faster, cheaper, and safer."*
✅ *"The migration halves cutover time. It also costs less, though the saving is small enough that it should not drive the decision."*

Why: three balanced adjectives is a rhythm, not an argument. The second version ranks them and admits one is weak.

### The not-just-X-but-Y frame

❌ *"This is not just a schema change, it's a change in how the team reasons about ownership."*
✅ *"The schema change forces every service to declare an owner, which is the part that will cause arguments."*

Why: the frame promises a reveal and delivers a restatement. Say the second clause and drop the first.

### Bolded lead-ins on every bullet

❌ Ten bullets, each opening with two bold words and a colon.
✅ Bold the three bullets a skimmer must not miss; leave the other seven plain.

Why: when everything is emphasized, nothing is. Uniform bolding is a template, and it reads as one.

### The hedge stack

❌ *"It is important to note that this approach may potentially introduce some additional complexity."*
✅ *"This adds a second write path. That is the cost."*

Why: four hedges in one sentence assert nothing. Strip hedges that qualify the hedge — keep the
one that carries a real, named uncertainty (*"we have two weeks of data"* stays).

### Section symmetry

❌ Six sections, each 3–4 sentences, each with a heading of the same grammatical shape.
✅ The section that matters runs nine sentences; two others run one line each.

Why: real documents are lumpy because real subjects are. Perfect evenness is generated shape.

### The restating conclusion

❌ A closing paragraph that summarizes the four sections above and adds nothing.
✅ End on the decision, the owner, and the date — or end where the argument ends.

Why: the summary-of-the-summary is filler the reader has already read.

### Vocabulary flags

`delve` · `leverage` (as a verb) · `robust` · `seamless` · `underscores the importance of` ·
`in today's fast-paced` · `it is worth noting that` · `navigate the complexities of` ·
`a testament to` · `tapestry`.

These are flags, not bans. One `robust` in a document about error handling is fine. Three
different words from this list in one paragraph is the finding.

### What is not a tell

- **Em dashes.** Punctuation. Only a finding at four-plus per paragraph.
- **Bullet lists.** Structure. Humans write them.
- **Correct grammar.** Consistent spelling is not evidence of anything.
- **Headings.** A document with headings is a document with headings.

Flagging any of these is how a hygiene pass loses the author's trust for the findings that were real.
