# summarise-reading-list

You are given a module reading list pasted from the reading list system: one item
per line, with title, author, year, format and a `held` column (yes/no).

1. Count the items by format (book, e-book, article, other).
2. List every item where `held` is `no`, with title, author and year.
3. If a line has no `held` value, list it separately under "Holding not stated".
   Do not guess.

Never add items that are not in the pasted list. If the list is empty, say so and stop.
