import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run_bench  # noqa: E402


@unittest.skipIf(os.name == "nt", "process groups are POSIX")
class RunGroupTimeoutTest(unittest.TestCase):
    def test_a_child_holding_the_pipe_does_not_hang_the_run(self):
        start = time.time()
        with self.assertRaises(subprocess.TimeoutExpired):
            run_bench.run_group(["sh", "-c", "sleep 60 & sleep 60"], "", ".", 1)
        self.assertLess(time.time() - start, 15)

    def test_output_is_returned(self):
        self.assertEqual(run_bench.run_group(["sh", "-c", "cat"], "hello", ".", 10), "hello")


if __name__ == "__main__":
    unittest.main()
