"""Utilities for managing events from matplotlib figures."""

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from matplotlib.axes import Axes


@dataclass
class MPLArtistEventHandler:
    axes: Axes
    """The axes this event will be registered to. This filters out events from other
    axes within the same figure, use a separate event handler to listen to each desired
    axes."""
    callback: Callable
    """The function to call when a point click is detected. This function will be passed
    the index within the points_x/points_y that was nearest and the mpl event object."""

    tolerance: float = 0.5
    """How far away from a point a click will still register as having clicked on that point."""

    button: int = 1
    """Which mouse button to listen for (by default left click.) Expects the
    matplotlib.backend_bases.MouseButton enum (for ease: 1 = left, 2 = middle, 3 = right)"""

    callback_id: int = field(default=None, repr=False, init=False)
    """Once attached, this is the cid of the callback once mpl_connect is called, used to
    disconnect this handler from the figure. (Call ``disconnect()``)."""

    def _handle_mpl_pick(self, event):
        # event.artist
        pass

    def connect(self):
        """Register the event handler and start listening for events."""

        def _inner_handler(event):
            self._handle_mpl_pick(event)

        self.callback_id = self.axes.get_figure().canvas.mpl_connect(
            "button_press_event", _inner_handler
        )

    def disconnect(self):
        """Unregister this callback from the figure canvas and stop getting events."""
        self.axes.get_figure().canvas.mpl_disconnect(self.callback_id)


@dataclass
class MPLEventHandler:
    """Class that attaches a custom event handler to a matplotlib axes, to call
    a custom callback function only when one of the requested points is clicked on.

    This is intended to simplify creating overlay widgets based on clicking within
    an mpl plot, and abstracts functionality I keep having to reimplement.

    TODO: example
    """

    axes: Axes
    """The axes this event will be registered to. This filters out events from other
    axes within the same figure, use a separate event handler to listen to each desired
    axes."""
    callback: Callable
    """The function to call when a point click is detected. This function will be passed
    the index within the points_x/points_y that was nearest and the mpl event object."""
    points_x: np.ndarray
    """The x-data of points to listen for a click at, should likely correspond to the
    data plotted in the figure."""
    points_y: np.ndarray
    """The y-data of points to listen for a click at, should likely correspond to the
    data plotted in the figure."""

    tolerance: float = 0.5
    """How far away from a point a click will still register as having clicked on that point."""

    button: int = 1
    """Which mouse button to listen for (by default left click.) Expects the
    matplotlib.backend_bases.MouseButton enum (for ease: 1 = left, 2 = middle, 3 = right)"""

    callback_id: int = field(default=None, repr=False, init=False)
    """Once attached, this is the cid of the callback once mpl_connect is called, used to
    disconnect this handler from the figure. (Call ``disconnect()``)."""

    def __post_init__(self):
        self.connect()

    def _find_nearest(self, xdata, ydata):
        """Uses manhattan distance to find the nearest point from points_x/points_y."""
        xdists = abs(xdata - self.points_x)
        ydists = abs(ydata - self.points_y)

        dists = xdists + ydists
        min_index = np.argmin(dists)
        if dists[min_index] < self.tolerance:
            # ensure click was within tolerance distance of the closest point.
            return min_index
        return None

    def _handle_mpl_button_press_event(self, event):
        """The raw event handler to handle mpl events. This filters through events that
        don't correspond to clicking on one of the requested points, and only forwards
        through the events that do."""
        if str(self.axes.get_figure().canvas.toolbar.mode) != "":
            # ignore if one of ipympl's tools is active.
            return
        if event.inaxes != self.axes:
            # ignore if the event wasn't in an axes we care about.
            return
        if event.button != self.button:
            # ignore if it wasn't the button we've been told to listen for.
            return
        nearest_row_index = self._find_nearest(event.xdata, event.ydata)
        if nearest_row_index is not None:
            # run the passed function if we actually were near a point.
            self.callback(nearest_row_index, event)

    def connect(self):
        """Register the event handler and start listening for events."""

        def _inner_handler(event):
            self._handle_mpl_button_press_event(event)

        self.callback_id = self.axes.get_figure().canvas.mpl_connect(
            "button_press_event", _inner_handler
        )

    def disconnect(self):
        """Unregister this callback from the figure canvas and stop getting events."""
        self.axes.get_figure().canvas.mpl_disconnect(self.callback_id)


def on_mpl_point_click(
    ax: Axes,
    callback: Callable,
    points_x: np.ndarray,
    points_y: np.ndarray,
    tolerance: float = 0.5,
    button: int = 1,
) -> MPLEventHandler:
    """More 'normal' semantic syntax for creating event handler."""
    handler = MPLEventHandler(ax, callback, points_x, points_y, tolerance, button)
    return handler
