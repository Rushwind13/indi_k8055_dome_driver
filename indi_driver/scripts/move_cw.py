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
        dome = Dome(verbose=False)
        dome.cw()
        sys.exit(0)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
