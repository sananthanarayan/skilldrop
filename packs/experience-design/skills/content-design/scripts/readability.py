#!/usr/bin/env python3
"""Plain-language check for a block of text. Stdlib only, Python 3.9+.

Reports word and sentence counts, average sentence length, the share of long words
(3+ syllables), an estimated Flesch-Kincaid grade, and every sentence over the length limit.
Syllables are counted with a vowel-group heuristic, so treat the grade as an estimate for
comparing a before and after, not as a precise score.

Usage:
    python3 readability.py page.md                 # text from a file
    cat page.md | python3 readability.py -         # text from stdin
    python3 readability.py page.md --max-sentence 20 --json
"""
import argparse
import json
import re
import sys

WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def strip_markdown(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)        # fenced code
    text = re.sub(r"`[^`]*`", " ", text)                       # inline code
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)          # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)       # links keep their text
    text = re.sub(r"^\s{0,3}#{1,6}\s*(.*)$", r"\1.", text, flags=re.M)  # headings end a sentence
    text = re.sub(r"^\s*[-*+]\s+(.*)$", r"\1.", text, flags=re.M)       # list items end a sentence
    text = re.sub(r"^\s*\d+[.)]\s+(.*)$", r"\1.", text, flags=re.M)
    text = re.sub(r"[*_>|]", " ", text)
    return text


def syllables(word):
    w = word.lower().strip("'-")
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    groups = re.findall(r"[aeiouy]{1,2}", w)
    return max(1, len(groups))


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n", text)
    out = []
    for p in parts:
        p = " ".join(p.split())
        if WORD.search(p):
            out.append(p)
    return out


def analyse(text, max_sentence):
    plain = strip_markdown(text)
    sents = sentences(plain)
    words = WORD.findall(plain)
    if not words or not sents:
        return None
    syl = [syllables(w) for w in words]
    long_words = sum(1 for s in syl if s >= 3)
    n_words, n_sents = len(words), len(sents)
    grade = 0.39 * (n_words / n_sents) + 11.8 * (sum(syl) / n_words) - 15.59
    too_long = []
    for s in sents:
        n = len(WORD.findall(s))
        if n > max_sentence:
            too_long.append({"words": n, "sentence": s})
    return {
        "words": n_words,
        "sentences": n_sents,
        "avg_sentence_words": round(n_words / n_sents, 1),
        "long_word_pct": round(100.0 * long_words / n_words, 1),
        "fk_grade_estimate": round(grade, 1),
        "max_sentence": max_sentence,
        "long_sentences": too_long,
    }


def main():
    ap = argparse.ArgumentParser(description="Plain-language check: sentence length, long words, estimated grade.")
    ap.add_argument("path", help="text or markdown file, or - for stdin")
    ap.add_argument("--max-sentence", type=int, default=25, help="flag sentences longer than this many words (default 25)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a text report")
    args = ap.parse_args()

    if args.max_sentence < 1:
        sys.exit("error: --max-sentence must be 1 or more")
    try:
        text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    except OSError as e:
        sys.exit("error: cannot read {}: {}".format(args.path, e.strerror))

    r = analyse(text, args.max_sentence)
    if r is None:
        sys.exit("error: no words found in the input")

    if args.json:
        print(json.dumps(r, indent=2))
        return
    print("Words: {}  Sentences: {}  Avg sentence: {} words".format(r["words"], r["sentences"], r["avg_sentence_words"]))
    print("Long words (3+ syllables): {}%".format(r["long_word_pct"]))
    print("Estimated Flesch-Kincaid grade: {} (heuristic syllables; compare before/after, don't quote as exact)".format(r["fk_grade_estimate"]))
    if r["long_sentences"]:
        print("Sentences over {} words: {}".format(r["max_sentence"], len(r["long_sentences"])))
        for s in r["long_sentences"]:
            print("  - ({} words) {}".format(s["words"], s["sentence"]))
    else:
        print("Sentences over {} words: none".format(r["max_sentence"]))


if __name__ == "__main__":
    main()
