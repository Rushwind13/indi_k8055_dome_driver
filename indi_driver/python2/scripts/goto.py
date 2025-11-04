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
        # Get azimuth from command line
        if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
            sys.exit(1)

        azimuth = float(sys.argv[1])

        dome = Dome()
        # Restore previous state
        restore_state(dome)
        
        try:
            # Use the rotation API to move toward the requested azimuth.
            dome.rotation(azimuth)
            # Save state after successful movement
            save_state(dome, "goto")
            sys.exit(0)
        except Exception:
            # If rotation() fails, try using cw() as fallback
            try:
                dome.cw(amount=azimuth)
                # Save state after successful movement
                save_state(dome, "goto")
                sys.exit(0)
            except Exception:
                sys.exit(1)
    except (ValueError, IndexError):
        sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
