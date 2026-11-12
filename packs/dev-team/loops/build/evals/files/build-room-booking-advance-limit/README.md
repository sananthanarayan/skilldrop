# Quillby Lane room diary

The little booking service behind the office's room screens and the `/rooms` chat command.

## Rooms

| Room  | Seats |
|-------|-------|
| Larch | 12    |
| Birch | 10    |
| Hazel | 6     |
| Pod-1 | 2     |
| Pod-2 | 2     |

## Using it

```python
from rooms.booking import Diary
diary = Diary()
diary.book("Hazel", "pat@quillby.example", start, end)
diary.book_weekly("Larch", "pat@quillby.example", start, end, weeks=6)
```

`book_weekly` books the same slot every week, all or nothing: if any week clashes, nothing is booked.

`Diary` takes a `clock` argument (defaults to `datetime.now`) so tests can pin the time.

## Tests

```
python3 -m unittest
```
