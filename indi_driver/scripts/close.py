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
        ok = False
        try:
            ok = dome.shutter_close()
        except Exception:
            ok = False

        if ok:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
