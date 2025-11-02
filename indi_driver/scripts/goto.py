#!/usr/bin/env python3
"""
INDI Dome Script
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")
)

from dome import Dome  # noqa: E402


def main():
    try:
        # Get azimuth from command line
        if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
            sys.exit(1)

        azimuth = float(sys.argv[1])

        # Validate azimuth range
        if not (0 <= azimuth <= 360):
            sys.exit(1)

        dome = Dome(verbose=False)
        dome.set_pos(azimuth)
        sys.exit(0)
    except (ValueError, IndexError):
        sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
