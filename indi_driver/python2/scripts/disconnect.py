#!/usr/bin/env python
"""
INDI Dome Script: Disconnect
Safely disconnects and stops all dome operations.
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

        # Attempt graceful disconnect of underlying device if available
        try:
            dev = getattr(dome, "dome", None)
            if dev is not None and hasattr(dev, "close"):
                dev.close()
            # Mark device as disconnected
            if hasattr(dome.dome, "k8055_device"):
                dome.dome.k8055_device.is_open = False
        except Exception as e:
            sys.stderr.write("WARN: device close failed: {}\n".format(e))

        # Save disconnected state
        save_state(dome, "disconnect")
        sys.exit(0)
    except Exception:
        sys.exit(0)  # Don't fail on disconnect


if __name__ == "__main__":
    main()
