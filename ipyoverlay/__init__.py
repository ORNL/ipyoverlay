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

from ipyoverlay import mpl

# flake8: noqa
from ipyoverlay.container import OverlayContainer
from ipyoverlay.utils import display_output
from ipyoverlay.widgets import (
    ContextMenu,
    ContextMenuArea,
    DecoratedWidgetWrapper,
    WidgetWrapper,
)

__version__ = "0.2.1"
