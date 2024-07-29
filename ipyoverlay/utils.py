"""Utility functions, primarily for helping convert pixel/data locations
for the various viz libraries."""

import importlib.resources

import ipywidgets as ipw
from IPython.display import display
from matplotlib.axes import Axes


def display_output(obj):
    """Render the passed object via ``display()`` in a new ipywidgets
    ``Output`` widget and return it.

    This is useful for "widget-ifying" things with a single call, e.g. a matplotlib figure.

    .. code-block:: python

        import matplotlib.pyplot as plt
        from ipyoverlay import display_output, OverlayContainer

        fig, ax = plt.subplots()
        ax.scatter(data)

        OverlayContainer(display_output(fig))
    """
    out = ipw.Output()
    with out:
        display(obj)
    return out


def vue_template_path(filename: str) -> str:
    """Get the path to the package "data resource" that is the requested vue template file.

    Args:
        filename (str): The name of the template file in the vue folder, e.g ``rawwidget.vue``

    Returns:
        The full package resource file path for the specified vue file.
    """
    path = None
    with importlib.resources.as_file(
        importlib.resources.files("ipyoverlay") / "vue" / filename
    ) as template_file_path:
        path = str(template_file_path)
    return path


# def register_mpl_point_hover(
#     fig: Figure,
#     handler: Callable,
#     points_x: np.ndarray,
#     points_y: np.ndarray,
#     tolerance: float = 0.5,
# ):
#     """Add a custom event handler for when one of a specified set of points is hovered over.
#
#     This is intended to simplify creating overlay widgets based on clicking within an mpl plot.
#
#     Args:
#         fig (Figure): The matplotlib figure whose canvas this event will be registered to.
#         handler (Callable): The function to call when a point is hovered. This
#             function will be passed the index within the points_x/points_y that was nearest, if
#             within tolerance.
#         points_x (np.ndarray): The x-data of points to listen for mouse events, should likely
#             correspond to the data plotted in the figure.
#         points_y (np.ndarray): The y-data of points to listen for mouse events, should likely
#             correspond to the data plotted in the figure.
#         tolerance (float): How far away from a point a mouse will still register as having
#             hovered over that point.
#
#     Returns:
#         The id of the matplotlib mpl_connect call. (Can be used to later disconnect this handler.)
#     """


# def register_mpl_point_click(
#     fig: Figure,
#     handler: Callable,
#     points_x: np.ndarray,
#     points_y: np.ndarray,
#     tolerance: float = 0.5,
#     button: int = 1,
# ):
#     """Add a custom event handler for when one of a specified set of points is clicked on.
#
#     This is intended to simplify creating overlay widgets based on clicking within an mpl plot.
#
#     Args:
#         fig (Figure): The matplotlib figure whose canvas this event will be registered to.
#         handler (Callable): The function to call when an appropriate click is detected. This
#             function will be passed the index within the points_x/points_y that was nearest, if
#             within tolerance.
#         points_x (np.ndarray): The x-data of points to listen for a click at, should likely
#             correspond to the data plotted in the figure.
#         points_y (np.ndarray): The y-data of points to listen for a click at, should likely
#             correspond to the data plotted in the figure.
#         tolerance (float): How far away from a point a click will still register as having
#             clicked on that point.
#         button (int): Which mouse button to listen for (by default left click.) Expects the
#             matplotlib.backend_bases.MouseButton enum (for ease: 1 = left, 2 = middle, 3 = right)
#
#     Returns:
#         The id of the matplotlib mpl_connect call. (Can be used to later disconnect this handler.)
#     """
#
#     # TODO: for this to be able to handle when x/ydata change, might need to
#     # make a class that is the handler (containing function, this _find_nearest,
#     # etc.)
#     def _find_nearest(xdata, ydata):
#         """Uses manhattan distance."""
#         xdists = abs(xdata - points_x)
#         ydists = abs(ydata - points_y)
#
#         dists = xdists + ydists
#         min_index = np.argmin(dists)
#         if dists[min_index] < tolerance:
#             # ensure click was within tolerance distance of the closest point.
#             return min_index
#         return None
#
#     def _inner_mpl_mouse_listener(event):
#         if str(fig.canvas.toolbar.mode) != "":
#             # Ignore if one of ipympl's tools is active.
#             return
#         if event.button != button:
#             # Ignore if it wasn't the button we've been told to listen for.
#             return
#         nearest_row_index = _find_nearest(event.xdata, event.ydata)
#         if nearest_row_index is not None:
#             # run the passed function if we actually were near a point.
#             handler(nearest_row_index)
#
#     return fig.canvas.mpl_connect("button_press_event", _inner_mpl_mouse_listener)
#
#


# TODO: move to mpl
def convert_pixel_to_mpl_data(
    axis: Axes, pixel_point_x: float, pixel_point_y: float
) -> tuple[float, float]:
    """Given a location in pixels, return the corresponding data location for the provided
    matplotlib axis.

    Args:
        axis (Axes): The matplotlib axis to get the data location relative to.
        pixel_point_x (float): Number of pixels from the left. TODO: relative to container?
        pixel_point_y (float): Number of pixels from the top. TODO: relative to container?
    """
    data_bounds = axis.viewLim
    axis_pixel_bounds = axis.get_window_extent()

    # see NOTE: on static display in convert_mpl_data_to_pixel
    static_display_dpi = 100
    figure_dpi = axis.figure.get_dpi()

    pixel_point_x = pixel_point_x / static_display_dpi * figure_dpi
    pixel_point_y = pixel_point_y / static_display_dpi * figure_dpi

    # ---- Y ----

    # invert y-axis because matplotlib counts from the bottom of the figure
    axis_point_y = axis.figure.get_figheight() * figure_dpi - pixel_point_y

    i_min_y = axis_pixel_bounds.y0
    i_max_y = axis_pixel_bounds.y1
    axis_range_y = i_max_y - i_min_y

    scalar_y = (axis_point_y - i_min_y) / axis_range_y

    d_min_y = data_bounds.y0
    d_max_y = data_bounds.y1
    data_range_y = d_max_y - d_min_y
    data_point_y = scalar_y * data_range_y
    data_y = data_point_y + d_min_y

    # ---- X ----

    axis_point_x = pixel_point_x

    i_min_x = axis_pixel_bounds.x0
    i_max_x = axis_pixel_bounds.x1
    axis_range_x = i_max_x - i_min_x

    scalar_x = (axis_point_x - i_min_x) / axis_range_x

    d_min_x = data_bounds.x0
    d_max_x = data_bounds.x1
    data_range_x = d_max_x - d_min_x
    data_point_x = scalar_x * data_range_x
    data_x = data_point_x + d_min_x

    return data_x, data_y


# TODO: move to mpl
def convert_mpl_data_to_pixel(
    axis: Axes, data_x: float, data_y: float, truncate: bool = True
) -> tuple[float, float]:
    """Given a data location in a matplotlib axis, return the corresponding
    location in pixels from left/top.

    NOTE: these pixel outputs are relative to the matplotlib canvas element.
    This means if there are elements above/to the left of the graph, the
    outputs will need to be adjusted

    Args:
        axis (Axes): The matplotlib axis to get the pixel location relative to.
        data_x (float): X-axis value.
        data_y (float): Y-axis value.
        truncate (bool): Whether to return -1, -1 if outside the axis limits
            or not.
    """
    data_bounds = axis.viewLim
    axis_pixel_bounds = axis.get_window_extent()

    # ---- X ----

    d_min_x = data_bounds.x0
    d_max_x = data_bounds.x1

    # if it's out of bounds, return -1
    if (data_x < d_min_x or data_x > d_max_x) and truncate:
        return -1, -1

    # get a point (x scalar) from 0-1 that represents the linear location for x
    data_point_x = data_x - d_min_x
    data_range_x = d_max_x - d_min_x
    scalar_x = data_point_x / data_range_x

    # transform x scalar to be in terms of the axis pixels
    i_min_x = axis_pixel_bounds.x0
    i_max_x = axis_pixel_bounds.x1

    axis_range_x = i_max_x - i_min_x
    axis_point_x = axis_range_x * scalar_x + i_min_x
    pixel_point_x = axis_point_x

    # ---- Y ----

    d_min_y = data_bounds.y0
    d_max_y = data_bounds.y1

    # if it's out of bounds, return -1
    if (data_y < d_min_y or data_y > d_max_y) and truncate:
        return -1, -1

    # get a point (y scalar) from 0-1 that represents the linear location for x
    data_point_y = data_y - d_min_y
    data_range_y = d_max_y - d_min_y
    scalar_y = data_point_y / data_range_y

    # transform y scalar to be in terms of the axis pixels
    i_min_y = axis_pixel_bounds.y0
    i_max_y = axis_pixel_bounds.y1

    axis_range_y = i_max_y - i_min_y
    axis_point_y = axis_range_y * scalar_y + i_min_y

    # invert y-axis because matplotlib counts from the bottom of the figure
    figure_dpi = axis.figure.get_dpi()
    pixel_point_y = axis.figure.get_figheight() * figure_dpi - axis_point_y

    # ---- DPI adjustment ----

    # matplotlib's internal DPI adjusts with the zoom level of the page, but the
    # browser's pixel counts don't actually change, so we need to always
    # reconvert output values to be a DPI of 100 for it to line up correctly.
    static_display_dpi = 100
    pixel_point_x = (pixel_point_x / figure_dpi) * static_display_dpi
    pixel_point_y = (pixel_point_y / figure_dpi) * static_display_dpi

    return pixel_point_x, pixel_point_y
