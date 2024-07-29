"""Widget that can support a background view widget and a foreground
set of positionable overlay widgets."""

import uuid
from typing import Callable

import ipyvuetify as v
import ipywidgets as ipw
import numpy as np
import traitlets
from matplotlib.axes import Axes

# TODO: conditional import
from plotly.graph_objects import FigureWidget

from .connection import Connection
from .utils import convert_mpl_data_to_pixel, vue_template_path
from .widgets import DecoratedWidgetWrapper


class OverlayContainer(v.VuetifyTemplate):
    """A wrapper for a background set of components that can render other ipywidgets
    over the background."""

    template_file = vue_template_path("container.vue")

    # TODO: not actually clear that width/height is directly necessary, presumably
    # it will just be based on background?
    width = traitlets.Any("auto").tag(sync=True)
    """Width of the container, set to 'auto' to autoscale."""
    height = traitlets.Any(500).tag(sync=True)
    """Height of the container, set to 'auto' to autoscale."""
    # NOTE: we use Any to allow user to specify "auto" (which should imply 100%
    # fill)

    current_width = traitlets.Integer().tag(sync=True)
    """Read-only traitlet used for JS to communicate actual current size to python side."""
    current_height = traitlets.Integer().tag(sync=True)
    """Read-only traitlet used for JS to communicate actual current size to python side."""

    # TODO: arbitrary num of layers?
    widget = traitlets.Any().tag(sync=True, **ipw.widget_serialization)
    """The background widget/layout this container should wrap and render things over."""
    children = traitlets.List().tag(sync=True, **ipw.widget_serialization)
    """The set of widgets rendered as overlays over the background widget."""

    detail_connections = traitlets.List().tag(sync=True, **ipw.widget_serialization)
    """A list of connection widgets for each child."""
    child_connections_info = traitlets.List().tag(sync=True)
    """A list of lists containing the connection ids associated with each child widget."""
    # for each child, there's a list, first element is connection id and then a
    # "point index", either 1 or 2

    container_id = traitlets.Unicode("unset-overlay-container-id").tag(sync=True)

    dragging = traitlets.Bool(False).tag(sync=True)
    dragging_index = traitlets.Integer(-1).tag(sync=True)

    expandable = traitlets.Bool(True).tag(sync=True)
    """Whether to allow (and show button for) expanding the container to take up full
    notebook window."""
    # TODO: more like "Fullscreenable", figure out better name
    expanded = traitlets.Bool(False).tag(sync=True)
    """Get/set whether currently expanded to full notebook window or not."""

    def __init__(self, widget=None, **kwargs):
        super().__init__(**kwargs)

        # we add 'c' to the beginning to ensure id starts with letter, required for html4
        self.container_id = "c" + str(uuid.uuid4())

        self._resized_callbacks: list[Callable[[int, int]], None] = []
        self._rendered_callbacks: list[Callable] = []
        self.widget = widget

    # ============================================================
    # EVENT DEFINITONS
    # ============================================================

    def on_resized(self, callback: Callable[[int, int], None]):
        """Register a callback to execute when the container's size is changed.

        The callback will be passed the new width and height as integers.
        """
        self._resized_callbacks.append(callback)

    def on_rendered(self, callback: Callable):
        """Register a callback to execute when the container is rendered and displayed.

        Nothing is passed to the callback.
        """
        self._rendered_callbacks.append(callback)

    def fire_on_resized(self, width: int, height: int):
        """Trigger all registered on_resized callbacks."""
        for callback in self._resized_callbacks:
            callback(width, height)

    def fire_on_rendered(self):
        """Trigger all registered on_rendered callbacks."""
        for callback in self._rendered_callbacks:
            callback()

    # ============================================================
    # EVENT HANDLERS
    # ============================================================

    def vue_handle_child_mouse_down(self, event):
        """Event handler for when the mouse is clicked on an overlay component."""
        # expected to decide whether to set dragging=true or not?
        child_index = event["childIndex"]
        if hasattr(self.children[child_index], "overlay_container_should_handle_click"):
            # we allow a child to determine if it wants to handle a click or if
            # this container should start dragging
            if self.children[child_index].overlay_container_should_handle_click(event):
                self.dragging = True
                if hasattr(self.children[child_index], "active"):
                    self.children[child_index].active = True
        else:
            self.dragging = True

        # raise the clicked object above the others
        if hasattr(self.children[child_index], "z_index"):
            self.children[child_index].z_index = 110
            for index, child in enumerate(self.children):
                if index == child_index:
                    continue
                if hasattr(self.children[index], "z_index"):
                    self.children[index].z_index = 100

    def vue_handle_mouse_down(self, e):
        """Event handler for when the mouse is clicked not on an overlay component."""
        # hide any open context menus?

    def vue_handle_mouse_up(self, e):
        """Event handler for when the mouse button is released.

        Connection endpoint updates get handled here.
        """
        if self.dragging:
            if hasattr(self.children[self.dragging_index], "recheck_position"):
                self.children[self.dragging_index].recheck_position()
            if hasattr(self.children[self.dragging_index], "active"):
                self.children[self.dragging_index].active = False

            # get any connections to update as well
            conn_ids_to_update = []
            if len(self.child_connections_info[self.dragging_index]) > 0:
                for conn_info in self.child_connections_info[self.dragging_index]:
                    conn_ids_to_update.append(conn_info[0])
            for detail_connection in self.detail_connections:
                if detail_connection["id"] in conn_ids_to_update:
                    detail_connection["widget"].recheck_position()

    def vue_handle_resize(self, e):
        """Event handler for when the container's size changes. This gets
        propagated through on_resized handlers."""
        width = e["width"]
        height = e["height"]
        self.current_width = width
        self.current_height = height

        # update any connection svg widths/heights
        for connection in self.detail_connections:
            connection["widget"].width = width
            connection["widget"].height = height

        self.fire_on_resized(width, height)

    def vue_handle_rendered(self, e):
        """Event handler for when the componet is rendered in JS.
        This gets propagated through on_resized handlers."""
        self.fire_on_rendered()

    # ============================================================
    # INTERNAL FUNCTIONS
    # ============================================================

    def _update_child_connection_endpoints(self, child_index: int):
        """Refresh the location of any connection endpoints attached
        to the child."""
        self.send({"method": "updateChildConnectionsEndpoint", "args": [child_index]})

    def _initial_connection_setup(self, child) -> Connection:
        """Boilerplate for defining a new connection and adding relevant information
        for its attached child."""
        c = Connection()
        c.height = self.current_height
        c.width = self.current_width
        c.container_id = self.container_id

        self.detail_connections = [
            *self.detail_connections,
            {"widget": c, "id": c.connection_id},
        ]
        child_index = self.children.index(child)

        # every child gets a connections_info array, so find the array for the
        # specified child and add the new connection info
        new_child_connections_info = []
        for index, info in enumerate(self.child_connections_info):
            if index == child_index:
                new_child_connections_info.append([*info, [c.connection_id, 1]])
            else:
                new_child_connections_info.append(info)

        self.child_connections_info = new_child_connections_info

        return c

    def _finish_new_connection_setup(self, connection: Connection, child):
        """Boilerplate for setting correct information on connection once its
        endpoints have been attached."""
        child_index = self.children.index(child)
        # let the JS side know we've changed the connections
        self._update_child_connection_endpoints(child_index)
        connection.recheck_position()

    # ============================================================
    # PUBLIC FUNCTIONS
    # ============================================================

    def add_child_at_mpl_point(
        self, obj: ipw.Widget, axis: Axes, data_x: float, data_y: float
    ):
        """Add the passed widget as an overlay and connect it to a matplotlib
        figure at the specified data location.

        Args:
            obj (Widget): The ipywidget to add, recommend wrapping in
                DecoratedWidgetWrapper to support additional features like
                click/drag etc.
            axis (Axes): The matplotlib axis object containing the data location to connect to.
            data_x (float): The x-value within the axis to show the connection endpoint.
            data_y (float): The y-value within the axis to show the connection endpoint.
        """
        px_x, px_y = convert_mpl_data_to_pixel(axis, data_x, data_y)
        self.add_child(obj, px_x + 10, px_y + 10)
        self.connect_child_to_mpl(obj, axis, data_x, data_y)

    def add_child(self, obj: ipw.Widget, left: int = 0, top: int = 0):
        """Add the passed widget as an overlay at the specified position.

        Args:
            obj (Widget): The ipywidget to add, recommend wrapping in
                DecoratedWidgetWrapper to support additional features like
                click/drag etc.
            left (int): Position from the left in pixels to render widget at.
            top (int): Position from the top in pixels to render widget at.
        """
        self.send({"method": "addNewChildPosition", "args": [left, top]})
        self.children = [*self.children, obj]
        self.child_connections_info = [*self.child_connections_info, []]
        if hasattr(obj, "recheck_position"):
            obj.recheck_position()
        obj.container = self

    def remove_child(self, obj):
        """Remove the passed child from the container."""
        child_index = self.children.index(obj)
        self.send({"method": "removeChild", "args": [child_index]})

        # remove the child's connection information
        conn_ids_to_remove = []
        new_child_connections_info = []
        for index, info in enumerate(self.child_connections_info):
            if index == child_index:
                if len(info) > 0:
                    # find associated connection objs and remove
                    for info_set in info:
                        conn_ids_to_remove.append(info_set[0])
                continue
            new_child_connections_info.append(info)
        self.child_connections_info = new_child_connections_info

        # remove the actual connection objects
        new_detail_connections = []
        for detail_connection in self.detail_connections:
            if detail_connection["id"] in conn_ids_to_remove:
                detail_connection["widget"].disconnect_mpl()
                continue
            new_detail_connections.append(detail_connection)
        self.detail_connections = new_detail_connections

        # remove the child object
        new_children = []
        for child in self.children:
            if child == obj:
                continue
            new_children.append(child)
        self.children = new_children

    def move_child(self, child, x: int, y: int):
        """Move the specified child to the specified (left, top).

        The pixel values for left/top should be local to the container.
        """
        child_index = self.children.index(child)
        self.send({"method": "moveChild", "args": [child_index, x, y]})

    def move_child_client_px(self, child, x: int, y: int):
        """Move the specified child to the specified (left, top).

        The pixel values for left/top are clientX/clientY values wrt
        to the page, (e.g. what you would get from mouse events), not
        the left/top within the container.
        """
        child_index = self.children.index(child)
        self.send({"method": "moveChild", "args": [child_index, x, y, True]})

    def connect_child_to_pixel(self, child, point: tuple[int, int]) -> Connection:
        """Make a connection that moves around with a draggable child and a static point."""
        c = self._initial_connection_setup(child)

        # set the static point for the other end of the connection
        c.x2 = point[0]
        c.y2 = point[1]

        self._finish_new_connection_setup(c, child)
        return c

    def connect_child_to_mpl(self, child, axis: Axes, data_x: float, data_y: float):
        """Make a connection that moves around with a draggable child and a point
        in a matplotlib axis.

        Args:
            child: The widget to draw a connection line from.
            axis (Axes): The matplotlib axis object containing the data location to connect to.
            data_x (float): The x-value within the axis to show the connection endpoint.
            data_y (float): The y-value within the axis to show the connection endpoint.
        """
        c = self._initial_connection_setup(child)

        c.connect_to_mpl(2, axis, data_x, data_y)

        self._finish_new_connection_setup(c, child)
        return c

    def connect_child_to_plotly(
        self, child, fig_widget: FigureWidget, data_x: float, data_y: float
    ):
        """Make a connection that moves around with a draggable child and a point
        in a plotly figure."""
        c = self._initial_connection_setup(child)

        c.connect_to_plotly(2, fig_widget, data_x, data_y)

        self._finish_new_connection_setup(c, child)
        return c

    def get_current_width_height(self) -> tuple[int, int]:
        """Ask JS to update our current_width and current_height variables
        to reflect current overlay container dimensions."""
        self.send({"method": "getCurrentSize", "args": []})
        return self.current_width, self.current_height

    def get_relative_layout_position(
        self,
        x,
        y,
        relative_points_x: np.ndarray,
        relative_points_y: np.ndarray,
        radius: float | int = -1,
        source: str = "mpl",
        force: bool = False,
    ) -> tuple[float, float]:
        """
        Args:
            radius (float | int): How far out to get a position. Leave -1 to compute based on
                relative points.
            source (str): How to consider data
            force (bool): Whether to move other widgets around to make fit better or not.
        """
        # find all boundaries of other current decorated widgets
        existing_boxes = []
        for child in self.children:
            if isinstance(child, DecoratedWidgetWrapper):
                child.recheck_position()
                existing_boxes.append(
                    [
                        child.current_x,
                        child.current_y,
                        child.current_width + child.current_x,
                        child.current_height + child.current_y,
                    ]
                )

        # get the center of the relative points
        center_x = relative_points_x.mean()
        center_y = relative_points_y.mean()

        # get the direction of the passed point from the relative center
        angle = np.arctan2(y - center_y, x - center_x)
        dist = np.sqrt((y - center_y) ** 2 + (x - center_x) ** 2)

        # for now just directly output the position for that angle with that
        # radius
        dist += radius

        # TODO: take size of box into account? (can't since it prob isn't created yet)
        # TODO: take other boxes into account
        # TODO: take container size into account
        # TODO: do pixel translations here based on source

        final_x = dist * np.cos(angle) + center_x
        final_y = dist * np.sin(angle) + center_y

        return final_x, final_y
