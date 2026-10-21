"""Every fuzz target, run briefly in the normal test suite on every OS (RFC-0062).

The fuzz workflow runs the same targets for longer, coverage-guided with Atheris, on Linux. Here
each target runs its seeds and a fixed set of mutations, so the targets keep working, and a
crash the fuzzer once found can't come back unnoticed.
"""
import unittest

from tests.fuzz.fuzz import stdlib_fuzz
from tests.fuzz.targets import TARGETS

ITERATIONS = 150


class FuzzTargets(unittest.TestCase):
    pass


def _case(name):
    def test(self):
        found = stdlib_fuzz(name, ITERATIONS)
        if found:
            data, err = found
            self.fail("%s\ninput: %r" % (err, data[:300]))
    test.__doc__ = "fuzz target %s: seeds and %d mutations run without a crash" % (name, ITERATIONS)
    return test


for _t in TARGETS:
    setattr(FuzzTargets, "test_" + _t[0].replace("-", "_"), _case(_t[0]))


if __name__ == "__main__":
    unittest.main()
