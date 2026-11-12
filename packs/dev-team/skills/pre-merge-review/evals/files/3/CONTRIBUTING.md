# Contributing

- Standard library only. No third-party packages in the dispensing code.
- Checks before merging to main: `python3 -m unittest discover -s tests -t .` must pass with no new skips.
- The dispensing screen runs on the shared front-desk PC. Do not write client details to disk.
