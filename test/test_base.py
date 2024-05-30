"""Simple import and init tests."""

# pylint: disable=import-outside-toplevel,unused-import

from ipyoverlay.connection import Connection
from ipyoverlay.container import OverlayContainer
from ipyoverlay.widgets import ContextMenu, ContextMenuArea, DecoratedWidgetWrapper


def test_import():
    """Importing the library should not throw errors!"""
    import ipyoverlay  # noqa: F401


def test_inits():
    """All classes should initialize without errors."""
    conn = Connection()  # noqa: F841
    container = OverlayContainer()  # noqa: F841
    area = ContextMenuArea()  # noqa: F841
    menu = ContextMenu()  # noqa: F841
    widget = DecoratedWidgetWrapper()  # noqa: F841
