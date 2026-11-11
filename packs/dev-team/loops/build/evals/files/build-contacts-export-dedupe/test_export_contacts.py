import unittest

from export_contacts import to_rows


class ToRowsTest(unittest.TestCase):
    def test_joins_names(self):
        rows = to_rows([{"first_name": "Ada", "last_name": "Quill", "email": "ada@example.com"}])
        self.assertEqual(rows, [("Ada Quill", "ada@example.com")])


if __name__ == "__main__":
    unittest.main()
