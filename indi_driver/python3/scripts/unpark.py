#!/usr/bin/env python3
"""
INDI Dome Script
"""

import os
import sys


def main():
    sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")
    )
    from dome import Dome

    try:
        dome = Dome()
        try:
            # Unpark: mark dome not parked/at-home so movement allowed
            dome.is_home = False
            sys.exit(0)
        except Exception:
            sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
