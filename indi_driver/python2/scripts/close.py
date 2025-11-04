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
    from persistence import restore_state, save_state

    try:
        dome = Dome()
        # Restore previous state
        restore_state(dome)
        
        ok = False
        try:
            ok = dome.shutter_close()
        except Exception:
            ok = False

        if ok:
            # Save state after successful shutter operation
            save_state(dome, "close")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
