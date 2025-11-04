#!/usr/bin/env python
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
        # Attempt to stop rotation and shutter movement
        try:
            dome.rotation_stop()
        except Exception as e:
            # Log the exception but continue to ensure abort is safe
            sys.stderr.write("WARN: rotation_stop failed: {}\n".format(e))
        try:
            dome.shutter_stop()
        except Exception as e:
            sys.stderr.write("WARN: shutter_stop failed: {}\n".format(e))
        sys.exit(0)
    except Exception:
        sys.exit(0)  # Always succeed for safety


if __name__ == "__main__":
    main()
