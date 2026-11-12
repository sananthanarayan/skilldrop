# Worked example: a paper before journal submission

## Input

> *"I'm submitting this to the journal next week ([inputs/paper.md](inputs/paper.md)). Can you
> check my citations and cross-references? It's APA 7th, and the abstract limit is 50 words."*

## What the manuscript shows

```text
# Manuscript check

Citation style: author-year; 10 references, 9 cited; 2 figures; 1 tables; abstract 46 words.

FAIL line 9: cites “Yeager (2016)”, but the reference list spells it Yeagar (2016)
FAIL line 34: cites “Kuh et al., 2009”, but the reference list has Kuh 2008
FAIL references on lines 42 and 56 are the same work (DOI 10.1093/biomet/70.1.41)
FAIL line 11: refers to Section 6, but there is no section 6
FAIL line 28: refers to Table 2, but there is no Table 2
FAIL line 28: refers to Figure 3, but there is no Figure 3
WARN reference on line 54 (Pascarella 2005) is never cited
WARN Figure 2 (line 30) is never referred to in the text
```

## Reply

**Six things a reviewer would catch:**

1. **Line 34: "Kuh et al., 2009"** — your list has Kuh et al. (2008), and the introduction cites
   2008. Change the citation to 2008.
2. **Line 9: "Yeager (2016)"** — the reference list spells it **Yeagar**. The author is Yeager;
   correct the list entry.
3. **Rosenbaum and Rubin (1983) is listed twice** (lines 42 and 56, the same DOI). Delete the
   second entry.
4. **Line 11 refers to Section 6**, but the paper ends at Section 4. Did you mean Section 4?
5. **Line 28 refers to Table 2 and Figure 3**, but the paper has one table and two figures. Table
   2 looks cut in revision; Figure 3 is probably Figure 2 (retention by cohort).
6. **Figure 2 is never referred to.** Fixing item 5 to "Figure 2" solves both.

**Never cited:** Pascarella and Terenzini (2005). Cite it where the introduction discusses
retention research, or remove it.

**Reference style (APA 7th)**
- Kuh et al. (2008), Stephens et al. (2012) and Walton and Cohen (2011) have no DOI; APA 7 includes one whenever the work has one, so look each up.
- Yeager (2016) has one author in your list; the paper has many. APA 7 lists up to 20 authors.
- "PNAS" should be the full journal name, *Proceedings of the National Academy of Sciences*.

**Abstract:** 46 words, under the 50-word limit.
