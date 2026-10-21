# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Suresh Soundararajan

"""Entry point for MarkView."""

import sys
import signal

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')


def main():
    """Launch the MarkView application."""
    # Allow Ctrl+C to terminate the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    from markview.application import MarkViewApplication

    app = MarkViewApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
