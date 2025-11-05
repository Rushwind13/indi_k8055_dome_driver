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
        # Attempt to stop rotation and shutter movement
        try:
            dome.rotation_stop()
        except Exception as e:
            # Log the exception but continue to ensure abort is safe
            print(f"WARN: rotation_stop failed: {e}", file=sys.stderr)
        try:
            dome.shutter_stop()
        except Exception as e:
            print(f"WARN: shutter_stop failed: {e}", file=sys.stderr)
        sys.exit(0)
    except Exception:
        sys.exit(0)  # Always succeed for safety


if __name__ == "__main__":
    main()
