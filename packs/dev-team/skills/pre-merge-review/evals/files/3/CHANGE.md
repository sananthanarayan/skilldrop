# Tidy dose calculation into helpers

Author: Sam Okafor
Target: main

Refactor only, no behaviour change. Pulled the max-dose cap out into a `_cap()` helper so it is
easier to read, and folded the pound conversion into the main branch of `dose_mg`.

Also adds a small debug log Dana at the front desk asked for, so we can trace odd doses back to
the client who queried them.

All tests pass locally (`python3 -m unittest`). I skipped `test_lb_cap` because it was flaky on CI.
