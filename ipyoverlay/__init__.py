"""
IPyOverlay
==========

import ipyoverlay as ui
import ipywidgets as ipw

container = ui.container.OverlayContainer()
container.widget = ipw.Label("This is a background widget")

overlay = ui.widgets.DecoratedWidgetWrapper()
overlay.widget = ipw.Label("Foreground widget")

container.add_child(overlay, left=40, top=100)
container.connect_child_to_pixel(overlay, (20, 20))
container
"""

# flake8: noqa
from .container import OverlayContainer
from .widgets import ContextMenu, ContextMenuArea, DecoratedWidgetWrapper, WidgetWrapper
from . import mpl

__version__ = "0.1.0"
