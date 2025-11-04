#!/usr/bin/env python
"""
INDI Dome Script: Connect
Tests dome hardware connection.
"""

import os
import sys


def main():
    sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")
    )
    from dome import Dome

    try:
        # Constructing Dome will attempt to initialize the hardware
        Dome()
        sys.exit(0)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
