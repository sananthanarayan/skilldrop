#!/usr/bin/env python3
"""Print the diff file and commit log file named on the command line."""
import sys

for path in sys.argv[1:]:
    print(open(path, encoding="utf-8").read())
