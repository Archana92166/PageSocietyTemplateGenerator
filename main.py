"""Application entry point for Page Society Template Generator."""

from __future__ import annotations

import sys

from app.core.application import Application


def main() -> int:
    """Create and run the desktop application."""
    return Application().run()


if __name__ == "__main__":
    sys.exit(main())
