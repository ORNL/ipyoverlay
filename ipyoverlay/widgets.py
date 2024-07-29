"""The widget and widget wrappers provided by ipyoverlay."""

import uuid
from typing import Callable

import ipyvuetify as v
import ipywidgets as ipw
import traitlets

from .utils import vue_template_path


class WidgetWrapper(v.VuetifyTemplate):
    """A basic draggable wrapper for any ipywidget.

    Widgets contained in this wrapper should likely not be interactive as
    this could have weird interactions with the drag events. Interactive
    widgets should instead be wrapped with the DecoratedWidgetWrapper, which
    provides a draggable bar above the widget instead.

    Args:
        widget: The ipywidget to display inside this overlay.
    """

    # TODO: TODO: haven't tested this in a while and I think some of the ID
    # functionality may be missing. Compare with DecoratedWidgetWrapper

    # load the vue code
    template_file = vue_template_path("rawwidget.vue")

    widget = traitlets.Any().tag(sync=True, **ipw.widget_serialization)

    clicked = traitlets.Bool(False).tag(sync=True)

    background_color = traitlets.Unicode("#444444").tag(sync=True)
    hover_border_color = traitlets.Unicode("#3389EA").tag(sync=True)
    default_border_color = traitlets.Unicode("transparent").tag(sync=True)

    def __init__(self, widget=None, **kwargs):
        super().__init__(**kwargs)

        if widget is not None:
            self.widget = widget

    def overlay_container_should_handle_click(self, event) -> bool:
        """When the container detects a click on a widget, it calls this to determine
        if it should handle it (``True``, container will then handle dragging logic)
        or if this widget will handle it (``False``)."""
        val_to_return = self.clicked
        self.clicked = False
        return val_to_return


# TODO: rename?
class PopupComponent(v.VuetifyTemplate):
    """Separate browser window containing the wrapped widget.

    There are several important qualifiers/limitations to be aware of with this.
    While vue correctly and automagically communicates variable state changes
    as expected, base styles from the jupyter notebook don't transfer (so some
    ipywidgets might look slightly different), and certain interactive display
    widgets don't seem to handle events correctly.

    This may be a good option to have a separate window on a separate screen
    with a simple control panel with standard inputs or basic html output, but
    interactive plots from plotly and matplotlib may not function as intended.

    Args:
        widget: The ipywidget to display inside the window.
        width (int): The width of the browser window (some browsers may ignore.)
        height (int): The height of the browser window (some browsers may ignore.)
        left (int): The distance from the left of the screen to show the browser
            window (some browsers may ignore.)
        right (int): The distance from the right of the screen to show the browser
            window (some browsers may ignore.)
    """

    # https://stackoverflow.com/questions/49657462/open-a-vuejs-component-on-a-new-window

    # load the vue code
    template_file = vue_template_path("popup-component.vue")

    # NOTE: there are some important limitations regarding....I think mouse
    # events? It's unclear, but interactive matplotlib figures and interactive
    # plotly figures both don't work. Communication in general does though, so
    # buttons, input fields, non-interactive displays etc. are all fine.

    widget = traitlets.Any().tag(sync=True, **ipw.widget_serialization)

    is_open = traitlets.Bool(False).tag(sync=True)

    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    left = traitlets.Int(200).tag(sync=True)
    top = traitlets.Int(200).tag(sync=True)

    # TODO: on close event?

    def __init__(
        self,
        widget=None,
        width: int = 600,
        height: int = 400,
        left: int = 200,
        top: int = 200,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.widget = widget

        self.width = width
        self.height = height
        self.left = left
        self.top = top

    def show(self, width=None, height=None, left=None, top=None):
        """Display the popup browser window."""
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if left is not None:
            self.left = left
        if top is not None:
            self.top = top
        self.send({"method": "openPortal", "args": []})

    def hide(self):
        """Close the popup browser window."""
        self.send({"method": "closePortal", "args": []})


class ContextMenu(v.VuetifyTemplate):
    """A menu of clickable options that can trigger provided event handlers. This should
    be used in tandem with a ContextMenuArea.

    Args:
        options (dict[str, str | tuple[str, Callable]]): The options to display in
            the menu. The keys represent a backend string to track, which the event
            handlers can check for, and the values are either strings (the html to
            display for the option, or a tuple of the html and an event handler to
            call specifically for that option.
    """

    # load the vue code
    template_file = vue_template_path("context-menu.vue")

    menu_id = traitlets.Unicode("unset-id").tag(sync=True)

    background_color = traitlets.Unicode("#444444").tag(sync=True)
    hover_color = traitlets.Unicode("#3389EA").tag(sync=True)
    width = traitlets.Integer(200).tag(sync=True)
    visible = traitlets.Bool(False).tag(sync=True)

    # TODO: at some point allow dividing options up into labeled sections
    options = traitlets.Dict().tag(sync=True)
    # the key is the backend string to refer to that option, the value is the
    # html to display, or the html + the event handler directly.

    def __init__(self, options: dict[str, str | tuple[str, Callable]] = None, **kwargs):
        super().__init__(**kwargs)
        self.menu_id = str(uuid.uuid4())

        self._option_clicked_callbacks = {"_any_": []}

        if options is not None:
            self.set_options(options)

    # ============================================================
    # EVENT DEFINITONS
    # ============================================================

    def on_option_clicked(self, callback, option: str = None):
        """If option is None, call this callback when any option is clicked.

        The callback will be passed the option key from the options dictionary,
        and an event_data dictionary containing mouse coordinates of the original
        right click.
        """
        if option is None:
            option = "_any_"
        if option not in self._option_clicked_callbacks:
            self._option_clicked_callbacks[option] = []
        self._option_clicked_callbacks[option].append(callback)

    def fire_on_option_clicked(self, option_key, event_data):
        """Trigger all registered on_option_clicked callbacks."""
        if option_key in self._option_clicked_callbacks:
            for callback in self._option_clicked_callbacks[option_key]:
                callback(option_key, event_data)
        for callback in self._option_clicked_callbacks["_any_"]:
            callback(option_key, event_data)

    # ============================================================
    # EVENT HANDLERS
    # ============================================================

    def vue_handle_option_clicked(self, data):
        """Event handler for when an option in the vue-component is clicked."""
        # TODO: pass in layer/local x/y coords attached to element
        option_key = data["key"]
        event_data = data["event_data"]
        self.fire_on_option_clicked(option_key, event_data)

    # ============================================================
    # INTERNAL FUNCTIONS
    # ============================================================

    # ============================================================
    # PUBLIC FUNCTIONS
    # ============================================================

    def set_options(self, options: dict[str, str | tuple[str, Callable]]):
        """NOTE: does not currently remove previous event handlers."""
        new_options = {}
        for option in options:
            if isinstance(options[option], tuple):
                option_text = options[option][0]
                option_event_handler = options[option][1]
                new_options[option] = option_text
                self.on_option_clicked(option_event_handler, option)
            else:
                new_options[option] = options[option]

        self.options = new_options

    def overlay_container_should_handle_click(self, e) -> bool:
        """When the container detects a click on a widget, it calls this to determine
        if it should handle it (``True``, container will then handle dragging logic)
        or if this widget will handle it (``False``)."""
        # context menus can't be dragged
        return False


class ContextMenuArea(v.VuetifyTemplate):
    """Widget wrapper that displays a specified context menu when the widget is
    right clicked."""

    # load the vue code
    template_file = vue_template_path("context-menu-area.vue")

    area_id = traitlets.Unicode("unset-area-id").tag(sync=True)

    widget = traitlets.Any().tag(sync=True, **ipw.widget_serialization)
    """The widget/layout that this context menu area applies to."""
    menu = traitlets.Any().tag(sync=True, **ipw.widget_serialization)
    """The context menu widget to use on right click."""

    force_right_click = traitlets.Bool(False).tag(sync=True)
    """Whether to enforce all right-clicks opening a context menu. This is
    necessary when wrapping ipympl matplotlib canvas plots, since they disable
    right click triggering the browser's contextmenu event."""

    enabled = traitlets.Bool(True).tag(sync=True)
    """Get/set whether the context menu area is actually active (if False, right
    click will follow normal browser behavior)."""

    # TODO: on menu change reassign this? have to do a set_menu?
    menu_id = traitlets.Unicode().tag(sync=True)

    def __init__(
        self,
        widget=None,
        menu: ContextMenu = None,
        force_right_click: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.area_id = str(uuid.uuid4())

        if widget is not None:
            self.widget = widget
        if menu is not None:
            self.menu = menu
            self.menu_id = menu.menu_id
        self.force_right_click = force_right_click

    def vue_set_menu_visible(self, visible: bool):
        """Vue-accessible function for displaying or hiding the menu."""
        self.menu.visible = visible


class DecoratedWidgetWrapper(v.VuetifyTemplate):
    """A 'windowed' draggable and closeable wrapper for any ipywidget.

    This renders a widget and places a bar above it with an exit button, and
    click and drag functionality only occurs when this bar is clicked. This
    allows un-conflicted interaction with the inner widget itself.

    Args:
        widget: The ipywidget to display inside this overlay.
    """

    # load the vue code
    template_file = vue_template_path("decorated-widget.vue")

    current_x = traitlets.Float().tag(sync=True)
    current_y = traitlets.Float().tag(sync=True)

    closable = traitlets.Bool(True).tag(sync=True)

    wrapper_id = traitlets.Unicode("unset-id").tag(sync=True)

    widget = traitlets.Any().tag(sync=True, **ipw.widget_serialization)

    clicked = traitlets.Bool(False).tag(sync=True)

    background_color = traitlets.Unicode("#444444").tag(sync=True)
    hover_border_color = traitlets.Unicode("#3389EA").tag(sync=True)
    default_border_color = traitlets.Unicode("transparent").tag(sync=True)

    default_header_color = traitlets.Unicode("#333333").tag(sync=True)
    active_header_color = traitlets.Unicode("#3389EA").tag(sync=True)
    active = traitlets.Bool(False).tag(sync=True)

    decoration_height = traitlets.Integer(15).tag(sync=True)

    title = traitlets.Unicode("").tag(sync=True)

    z_index = traitlets.Integer(100).tag(sync=True)

    width = traitlets.Any("auto").tag(sync=True)
    height = traitlets.Any("auto").tag(sync=True)

    current_width = traitlets.Float().tag(sync=True)
    current_height = traitlets.Float().tag(sync=True)

    def __init__(self, widget=None, **kwargs):
        super().__init__(**kwargs)

        if widget is not None:
            self.widget = widget

        self.wrapper_id = str(uuid.uuid4())
        self.container = None

        self._closed_callbacks: list[Callable[[DecoratedWidgetWrapper], None]] = []

    # def add_connection(self, connection, point_index: int):
    #     """NOTE: point_index should either be 1 or 2"""
    #     self.connections.append(connection)
    #     self.connection_ids = [*self.connection_ids, connection.connection_id]

    # ============================================================
    # EVENT DEFINITONS
    # ============================================================

    def on_closed(self, callback: Callable[["DecoratedWidgetWrapper"], None]):
        """Register a callback to execute when the widget is closed

        The callback will be passed this widget's instance.
        """
        self._closed_callbacks.append(callback)

    def fire_on_closed(self):
        """Trigger all registered on_closed callbacks."""
        for callback in self._closed_callbacks:
            callback(self)

    # ============================================================
    # EVENT HANDLERS
    # ============================================================

    def vue_handle_header_close_clicked(self, e):
        """Event handler for when the vue component's x-button is clicked."""
        self.fire_on_closed()
        if self.container is not None:
            self.container.remove_child(self)

    # ============================================================
    # INTERNAL FUNCTIONS
    # ============================================================

    # ============================================================
    # PUBLIC FUNCTIONS
    # ============================================================

    def recheck_position(self):
        """Request the vue side to update/sync current_x and current_y values.
        This reads from JS, doesn't write."""
        self.send({"method": "updateCurrentPos", "args": []})

    def overlay_container_should_handle_click(self, e) -> bool:
        """When the container detects a click on a widget, it calls this to determine
        if it should handle it (``True``, container will then handle dragging logic)
        or if this widget will handle it (``False``)."""
        if e["y"] - self.current_y >= self.decoration_height:
            self.clicked = False
        val_to_return = self.clicked
        self.clicked = False
        return val_to_return
