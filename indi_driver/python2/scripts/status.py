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
        # derive status from library methods/attributes
        try:
            parked = bool(getattr(dome, "is_home", False) or dome.isHome())
        except Exception:
            parked = bool(getattr(dome, "is_home", False))

        try:
            shutter_open = bool(getattr(dome, "is_open", False) or dome.isOpen())
        except Exception:
            shutter_open = bool(getattr(dome, "is_open", False))

        try:
            azimuth = float(dome.get_pos())
        except Exception:
            azimuth = 0.0

        status_line = "{} {} {:.1f}".format(parked, shutter_open, azimuth)

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
