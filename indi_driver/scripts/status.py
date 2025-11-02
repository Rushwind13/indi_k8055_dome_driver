#!/usr/bin/env python3
"""
INDI Dome Script: Status
Reports dome status to stdout or file.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")
)

from dome import Dome  # noqa: E402


def main():
    try:
        dome = Dome(verbose=False)
        parked = 1 if dome.isHome() else 0
        shutter_open = 1 if dome.isOpen() else 0
        azimuth = dome.get_pos()
        status_line = f"{parked} {shutter_open} {azimuth:.1f}"

        # Check if we have a file argument (from INDI)
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
            # Write to file (INDI temp file)
            with open(sys.argv[1], "w") as f:
                f.write(status_line)
        else:
            # Write to stdout
            print(status_line)

        sys.exit(0)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
