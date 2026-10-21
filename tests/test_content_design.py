import json
import os
import unittest

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "content-design", "readability.py"


class ReadabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def test_syllable_heuristic_on_known_words(self):
        s = self.m.syllables
        self.assertEqual(s("cat"), 1)
        self.assertEqual(s("make"), 1)       # silent final e dropped
        self.assertEqual(s("jumped"), 1)     # -ed dropped
        self.assertEqual(s("table"), 2)      # -le kept
        self.assertEqual(s("computer"), 3)
        self.assertEqual(s("information"), 4)

    def test_short_sentences_give_exact_counts_and_grade(self):
        r = self.m.analyse("The cat sat. The dog ran.", 25)
        self.assertEqual(r["words"], 6)
        self.assertEqual(r["sentences"], 2)
        self.assertEqual(r["avg_sentence_words"], 3.0)
        self.assertEqual(r["long_word_pct"], 0.0)
        # 0.39 * 3 + 11.8 * 1 - 15.59
        self.assertEqual(r["fk_grade_estimate"], -2.6)
        self.assertEqual(r["long_sentences"], [])

    def test_long_word_share_counts_three_plus_syllables(self):
        r = self.m.analyse("The computer is fast.", 25)
        self.assertEqual(r["words"], 4)
        self.assertEqual(r["long_word_pct"], 25.0)

    def test_sentence_over_limit_is_flagged_and_at_limit_is_not(self):
        at_limit = " ".join(["word"] * 25) + "."
        over = " ".join(["word"] * 26) + "."
        self.assertEqual(self.m.analyse(at_limit, 25)["long_sentences"], [])
        flagged = self.m.analyse(over, 25)["long_sentences"]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["words"], 26)

    def test_contractions_and_hyphenated_words_count_once(self):
        r = self.m.analyse("Don't use well-known jargon.", 25)
        self.assertEqual(r["words"], 4)

    def test_headings_and_list_items_end_a_sentence(self):
        text = "# Apply for a permit\n\n- Check you are eligible\n- Pay the fee\n"
        r = self.m.analyse(text, 25)
        self.assertEqual(r["sentences"], 3)
        self.assertEqual(r["words"], 11)

    def test_code_is_ignored_and_links_keep_their_text(self):
        text = "Run `rm -rf build` now.\n\n```\nlots of code words here\n```\n\nRead [the guide](https://example.test/x)."
        r = self.m.analyse(text, 25)
        self.assertEqual(r["words"], 5)  # Run, now, Read, the, guide
        self.assertEqual(r["sentences"], 2)

    def test_blank_line_splits_sentences_without_punctuation(self):
        r = self.m.analyse("First line here\n\nSecond line here", 25)
        self.assertEqual(r["sentences"], 2)

    def test_no_words_returns_none(self):
        self.assertIsNone(self.m.analyse("123 456 !!!", 25))


class ReadabilityCliTest(unittest.TestCase):
    def test_json_output_from_file(self):
        with workdir() as d:
            p = write(os.path.join(d, "page.md"), "The cat sat. The dog ran.\n")
            code, out, err = run(SKILL, SCRIPT, p, "--json")
        self.assertEqual(code, 0, err)
        r = json.loads(out)
        self.assertEqual(r["words"], 6)
        self.assertEqual(r["max_sentence"], 25)

    def test_stdin_dash_reads_text(self):
        code, out, err = run(SKILL, SCRIPT, "-", "--json", stdin="One two three.\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["words"], 3)

    def test_max_sentence_flag_changes_what_is_flagged(self):
        text = "This sentence has exactly six words.\n"
        code, out, _ = run(SKILL, SCRIPT, "-", "--max-sentence", "5", stdin=text)
        self.assertEqual(code, 0)
        self.assertIn("Sentences over 5 words: 1", out)
        self.assertIn("(6 words)", out)
        code, out, _ = run(SKILL, SCRIPT, "-", "--max-sentence", "6", stdin=text)
        self.assertIn("Sentences over 6 words: none", out)

    def test_text_report_labels_grade_as_estimate(self):
        code, out, _ = run(SKILL, SCRIPT, "-", stdin="The cat sat.\n")
        self.assertEqual(code, 0)
        self.assertIn("Estimated Flesch-Kincaid grade", out)
        self.assertIn("don't quote as exact", out)

    def test_missing_file_fails_clearly(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, os.path.join(d, "nope.md"))
        self.assertNotEqual(code, 0)
        self.assertIn("cannot read", err)
        self.assertNotIn("Traceback", err)

    def test_empty_input_fails_clearly(self):
        code, _, err = run(SKILL, SCRIPT, "-", stdin="")
        self.assertNotEqual(code, 0)
        self.assertIn("no words found", err)

    def test_max_sentence_below_one_is_rejected(self):
        code, _, err = run(SKILL, SCRIPT, "-", "--max-sentence", "0", stdin="Hi there.")
        self.assertNotEqual(code, 0)
        self.assertIn("--max-sentence", err)


if __name__ == "__main__":
    unittest.main()
