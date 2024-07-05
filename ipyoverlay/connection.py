"""UI class representing a 'details on demand' connection line, or an SVG
that is a line connecting some floating overlay to some source component or
positon."""

import uuid

import ipyvuetify as v
import ipywidgets as ipw
import traitlets
from matplotlib.axes import Axes

# TODO: conditional import
from plotly.graph_objects import FigureWidget

from .utils import convert_mpl_data_to_pixel, vue_template_path

# from enum import IntEnum


# class ConnectionType(IntEnum):
#     Pixel = 0
#     Child = 1
#     MPL = 2
#     Plotly = 3


class Connection(v.VuetifyTemplate):
    """SVG connection line, can be used to help track what an overlaid widget
    is referring to in an underlying component."""

    template_file = vue_template_path("connection.vue")

    # NOTE: width and height need to be the same as the container, otherwise if
    # one point of a line gets moved out of the initial default size of the SVG
    # it'll be invisible.
    width = traitlets.Integer(500).tag(sync=True)
    """Width of the SVG container to draw this connection within. Should match
    OverlayContainer width."""
    height = traitlets.Integer(500).tag(sync=True)
    """Height of the SVG container to draw this connection within. Should match
    OverlayContainer height."""

    # NOTE: these are currently one direction - they set the actual values but
    # do not reflect the correct current ones.
    x1 = traitlets.Float(-1).tag(sync=True)
    """X coordinate of first endpoint. This attribute is only used to send a
    value to the JS side, it won't necessarily reflect the current value."""
    y1 = traitlets.Float(-1).tag(sync=True)
    """Y coordinate of first endpoint. This attribute is only used to send a
    value to the JS side, it won't necessarily reflect the current value."""
    x2 = traitlets.Float(-1).tag(sync=True)
    """X coordinate of second endpoint. This attribute is only used to send a
    value to the JS side, it won't necessarily reflect the current value."""
    y2 = traitlets.Float(-1).tag(sync=True)
    """Y coordinate of second endpoint. This attribute is only used to send a
    value to the JS side, it won't necessarily reflect the current value."""

    conn_type_1 = traitlets.Int(0).tag(
        sync=True
    )  # TODO: unused, please use to distinguish mpl/plotly/direct/window
    conn_type_2 = traitlets.Int(0).tag(sync=True)

    connection_id = traitlets.Unicode("unset-connection-id").tag(sync=True)

    # only really necessary for plotly stuff to get plot offset
    container_id = traitlets.Unicode("unset-connection-id").tag(sync=True)

    # used for mpl/plotly connections
    data_x = traitlets.Float(-1).tag(sync=True)
    data_y = traitlets.Float(-1).tag(sync=True)

    plotly_div_class = traitlets.Unicode("").tag(sync=True)
    mpl_div_class = traitlets.Unicode("").tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.connection_id = str(uuid.uuid4())

        # matplotlib related info
        self.axis: Axes = None
        self.prev_fig_width_height: tuple[int, int] = None
        self.prev_axis_limits: tuple[float, float, float, float] = None
        # self.data_x: float = None
        # self.data_y: float = None
        self.mpl_side: int = None
        self.mpl_canvas_ref = None
        self.mpl_handler_id = None

        self.debug: ipw.Widget = None

    def _debug(self, *msg):
        if self.debug is not None:
            with self.debug:
                print(*msg)

    def recheck_position(self):
        """Ask JS to update python values for the current x1,y1,x2,y2."""
        self.send({"method": "updateCurrentPos", "args": []})

    def connect_to_plotly(
        self, side: int, fig_widget: FigureWidget, data_x: float, data_y: float
    ):
        """Start any necessary tracking so plotly figure changes keep the connection line
        endpoint updated.

        Args:
            side (int): ??? TODO: unused currently
            fig_widget (FigureWidget): The plotly widget being connected to.
            data_x (float): The x-value within the widget to show the connection endpoint.
            data_y (float): The y-value within the widget to show the connection endpoint.
        """
        # Attaching a connection to a plotly plot has several challenges - namely
        # that any layout changes don't communicate things like new axis ranges
        # to the python side, so we can't do the same type of event handler setup
        # deal as for matplotlib. The second challenge is that even from the JS
        # side, since the div was created via ipywidgets we have no explicit
        # reference to the plotly graph div (which we need to _actually_ attach
        # an event handler to listen to those axis range change events.)
        #
        # Our delightful hack to deal with this is to add a super uber definitely
        # unique class from the python side (which so happens to add said class
        # to the actual div we care about), then search for that class from
        # JS, and then re-remove the class from within python.
        self.data_x = data_x
        self.data_y = data_y
        fig_widget.add_class(f"plotly-{id(fig_widget)}")
        self.plotly_div_class = f"plotly-{id(fig_widget)}"

    def connect_to_mpl(self, side: int, axis: Axes, data_x: float, data_y: float):
        """Start any necessary tracking so matplotlib figure changes keep the connection line
        endpoint updated.

        Args:
            side (int): Which end of the connection refers to the MPL axis (1 or 2.)
            fig_widget (Axes): The matplotlib axis object being connected to.
            data_x (float): The x-value within the axis to show the connection endpoint.
            data_y (float): The y-value within the axis to show the connection endpoint.
        """
        self.axis = axis
        fig = axis.get_figure()
        fig.canvas.add_class(f"mpl-{id(fig)}")
        self.mpl_div_class = f"mpl-{id(fig)}"
        self.mpl_canvas_ref = fig.canvas
        self.mpl_handler_id = fig.canvas.mpl_connect(
            "draw_event", self._handle_mpl_draw_event
        )
        self.prev_fig_width_height = fig.canvas.get_width_height()
        axlim = axis.viewLim
        self.prev_axis_limits = axlim.x0, axlim.x1, axlim.y0, axlim.y1
        self.mpl_side = side
        self.data_x = data_x
        self.data_y = data_y
        self.refresh_mpl_location()

    def disconnect_mpl(self):
        """Since each connection adds its own draw_event listener, we need to make sure
        to remove it once a connection is removed, otherwise it will continue to try updating
        a non-existant svg."""
        if self.mpl_canvas_ref is not None and self.mpl_handler_id is not None:
            self.mpl_canvas_ref.mpl_disconnect(self.mpl_handler_id)

    def refresh_mpl_location(self):
        """If using matplotlib, update endpoint with current pixel values for associated
        data."""
        new_x, new_y = convert_mpl_data_to_pixel(self.axis, self.data_x, self.data_y)
        self._debug("Refreshing", new_x, new_y, self.connection_id)
        # if self.mpl_side == 1:
        #     self.x1 = new_x
        #     self.y1 = new_y
        # elif self.mpl_side == 2:
        #     self.x2 = new_x
        #     self.y2 = new_y
        self.send({"method": "convertMPLRelativePxToPx", "args": [new_x, new_y]})

    # def _handle_plotly_relayout(self, eventdata):
    #     """Note that because of ...
    #     we listen for the _property_lock trait change instead (which appears to
    #     always include the _js2py_relayout data?
    #     """

    def _handle_mpl_draw_event(self, event):
        canvas = event.canvas
        # check if figure size has changed
        new_fig_width_height = canvas.get_width_height()
        fig_size_changes = [
            new_fig_width_height[i] != self.prev_fig_width_height[i]
            for i in range(len(new_fig_width_height))
        ]
        fig_size_changed = any(fig_size_changes)

        # check if axis view limits have changed
        axlim = self.axis.viewLim
        new_axis_limits = axlim.x0, axlim.x1, axlim.y0, axlim.y1
        axlim_changes = [
            new_axis_limits[i] != self.prev_axis_limits[i]
            for i in range(len(new_axis_limits))
        ]
        axis_limits_changed = any(axlim_changes)

        self.prev_fig_width_height = new_fig_width_height
        self.prev_axis_limits = new_axis_limits

        # only refresh connection location if we actually need to
        if not fig_size_changed and not axis_limits_changed:
            return

        self.refresh_mpl_location()
