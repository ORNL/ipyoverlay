<template>
  <!-- REMINDER: have to have this outer container div because a template can
  only have one element. -->
  <div
    :id="container_id"
    ref="ipyoverlay_container"
    class="ipyoverlay-container"
    :style="{
      width: width === 'auto' ? '100%' : width + 'px',
      height: height === 'auto' ? '100%' : height + 'px',
      position: expanded ? 'fixed' : 'static',
    }"
    @mousemove="mouseMoveHandler"
    @mouseup="mouseUpHandler"
    @mousedown="mouseDownHandler"
  >
    <div v-if="expandable" class="ipyoverlay-screen-btn">
      <v-btn fab small color="primary" @click="expanded = !expanded">
        <v-icon v-if="!expanded">mdi-fullscreen</v-icon>
        <v-icon v-if="expanded">mdi-fullscreen-exit</v-icon>
      </v-btn>
    </div>

    <!--<jupyter-widget :widget="widget" style="position: absolute" />-->
    <jupyter-widget :widget="widget" />

    <div v-for="detail_connection in detail_connections" :key="detail_connection.id">
      <jupyter-widget :widget="detail_connection.widget" />
    </div>

    <div
      v-for="(overlayObj, index) in children"
      :id="container_id + '-child-' + index"
      class="ipyoverlay-child-container"
      :style="{ left: overlayPosLeft[index] + 'px', top: overlayPosTop[index] + 'px' }"
      @mousedown="childMouseDownHandler($event, index)"
    >
      <jupyter-widget :widget="overlayObj" />
    </div>
  </div>
</template>

<script>
module.exports = {
  data() {
    return {
      // positions for overlay children are tracked through these arrays
      // _only_ on the JS side, to help reduce Python <-> JS traffic during
      // actions like dragging.
      overlayPosLeft: [],
      overlayPosTop: [],

      draggingOffsetX: -1,
      draggingOffsetY: -1,

      // these get set as "previous values" when container gets expanded.
      unexpandedHeight: "auto",
      unexpandedWidth: "auto",

      // listens for resize events
      observer: null,
    };
  },
  watch: {
    expanded() {
      if (this.expanded) {
        this.unexpandedHeight = this.height;
        this.height = "auto";
        this.unexpandedWidth = this.width;
        this.width = "auto";
      }
      else {
        this.height = this.unexpandedHeight;
        this.width = this.unexpandedWidth;
      }
    },
  },
  mounted() {
    this.initObserver();
    this.handle_rendered();
  },
  methods: {
    // ============================================================
    // PYTHON-CALLABLE FUNCTIONS
    // ============================================================

    /**
     * When parent python code adds a new child, add its left and top
     * position attributes to the position arrays.
     * @param {number} posLeft Pixels from left of container to top left of child.
     * @param {number} posTop Pixels from top of container to top left of child.
     */
    jupyter_addNewChildPosition(posLeft, posTop) {
      this.overlayPosLeft = [...this.overlayPosLeft, posLeft];
      this.overlayPosTop = [...this.overlayPosTop, posTop];
    },

    /**
     * Refresh the position of the connections for the given child to the
     * center of that child's bounding box.
     * @param {number} childIndex The index of the child widget from the python side.
     */
    jupyter_updateChildConnectionsEndpoint(childIndex) {
      // short circuit if there's no connections attached to this child
      if (this.child_connections_info[childIndex].length < 1) { return; }

      // get the overlay container
      const containerEl = this.$refs.ipyoverlay_container;
      let containerRect = containerEl.getBoundingClientRect();

      // get the child
      const childEl = document.getElementById(this.container_id + "-child-" + childIndex);
      let childRect = childEl.getBoundingClientRect();

      // compute the centerpoint of the child
      const centerX = childRect.x - containerRect.x + childRect.width / 2;
      const centerY = childRect.y - containerRect.y + childRect.height / 2;

      this.setChildConnectionsEndpoint(childIndex, centerX, centerY);
    },

    /**
     * When parent python code deletes an overlay element, remove associated
     * left/top coordinates from position arrays.
     * @param {number} childIndex The index within overlayPosLeft/Top of the child being
     * removed.
     */
    jupyter_removeChild(childIndex) {
      let newPosLeft = [];
      let newPosTop = [];

      // iterate and "re-add" all except the index to remove
      for (let i = 0; i < this.overlayPosLeft.length; i++) {
        if (i === childIndex) {
          continue;
        }
        newPosLeft.push(this.overlayPosLeft[i]);
      }
      for (let i = 0; i < this.overlayPosTop.length; i++) {
        if (i === childIndex) {
          continue;
        }
        newPosTop.push(this.overlayPosTop[i]);
      }

      // now assign to cause reactive changes
      this.overlayPosLeft = newPosLeft;
      this.overlayPosTop = newPosTop;
    },

    /**
     * When parent python code requests to move a child to a specified
     * location, translate coordinates to be local to the container if they
     * aren't already. (globalCoords == True implies that the coordinates
     * being passed in are relative to the entire page, e.g. computed off of
     * clientX, clientY)
     * @param {number} childIndex The index within overlayPosLeft/Top of child
     * being moved.
     * @param {number} newLeft Pixels from left to use for assigning new location.
     * @param {number} newTop Pixels from top to use for assigning new location.
     * @param {boolean} globalCoords Whether newLeft/newTop are relative to
     * entire page or the container.
     */
    jupyter_moveChild(childIndex, newLeft, newTop, globalCoords=false) {
      // translate the coordinates to within the container if the pixel
      // values are clientX/clientY
      if (globalCoords) {
        const containerEl = this.$refs.ipyoverlay_container;
        let boundingRect = containerEl.getBoundingClientRect();

        newLeft = newLeft - boundingRect.x;
        newTop = newTop - boundingRect.y;
      }

      this.setChildPosition(childIndex, newLeft, newTop);
    },

    /**
     * When parent python code asks for the current width and height, update
     * the traitlet values.
     */
    jupyter_getCurrentSize() {
      let container = this.$refs.ipyoverlay_container;
      this.current_width = container.offsetWidth;
      this.current_height = container.offsetHeight;
    },

    // ============================================================
    // INTERNAL FUNCTIONS
    // ============================================================

    /**
     * Update the connections for the given child to the specified x y coords
     * @param {number} childIndex The index within overlayPosLeft/Top of child
     * that was moved.
     * @param {number} x Pixels from left of container.
     * @param {number} y Pixels from top of container.
     */
    setChildConnectionsEndpoint(childIndex, x, y) {
      console.log("Setting child " + childIndex.toString() + " connection endpoint");
      // iterate each listed connection for this child
      for (let i = 0; i < this.child_connections_info[childIndex].length; i++) {
        // get the connection information (UUID of the connection element and
        // the side (1 or 2) that this child is connected to
        let connectionID = this.child_connections_info[childIndex][i][0];
        let pointSide = this.child_connections_info[childIndex][i][1];
        console.log("Setting " + pointSide.toString() + " side to " + x.toString() + "," + y.toString());

        // get the connection element and set the appropriate side to the
        // center point
        let connectionEl = document.getElementById(connectionID).children[0];
        connectionEl.setAttribute("x" + pointSide, x);
        connectionEl.setAttribute("y" + pointSide, y);

        connectionEl = document.getElementById(connectionID).children[1];
        connectionEl.setAttribute("x" + pointSide, x);
        connectionEl.setAttribute("y" + pointSide, y);
      }
    },

    /**
     * Move the specified child, x and y should already be relative to the
     * container. Also update any connections tied to this child.
     * @param {number} childIndex The index within overlayPosLeft/Top of child
     * that was moved.
     * @param {number} x Pixels from left of container.
     * @param {number} y Pixels from top of container.
     */
    setChildPosition(childIndex, x, y) {
      // reconstruct the new position arrays (because we can't mutate
      // an array and expect reactive events to propagate)
      let newPosLeft = [];
      let newPosTop = [];

      // reconstruct left positions array
      for (let i = 0; i < this.overlayPosLeft.length; i++) {
        if (i === childIndex) { newPosLeft.push(x); }
        else { newPosLeft.push(this.overlayPosLeft[i]); }
      }

      // reconstruct top positions array
      for (let i = 0; i < this.overlayPosTop.length; i++) {
        if (i === childIndex) { newPosTop.push(y); }
        else { newPosTop.push(this.overlayPosTop[i]); }
      }

      // now assign to cause reactive changes
      this.overlayPosLeft = newPosLeft;
      this.overlayPosTop = newPosTop;

      // determine if any connection points need to be updated
      if (this.child_connections_info[childIndex].length > 0) {
        // get the size of the dragging item so we can find the "center"
        let childEl = document.getElementById(this.container_id + "-child-" + childIndex.toString());
        let childElRect = childEl.getBoundingClientRect();
        let centerX = x + childElRect.width / 2;
        let centerY = y + childElRect.height / 2;
        this.setChildConnectionsEndpoint(childIndex, centerX, centerY);
      }
    },

    /**
     * Create a ResizeObserver that watches for changes to the overlay
     * container's width (so we can add events to auto-adjust child sizes
     * etc.)
     * https://dev.to/sammm/using-mutationobserver-and-resizeobserver-to-measure-a-changing-dom-element-in-vue-3jpd
     */
    initObserver() {
      const observer = new ResizeObserver(this.onResize);
      observer.observe(this.$refs.ipyoverlay_container);
      this.observer = observer;
    },

    // ============================================================
    // EVENT HANDLERS
    // ============================================================

    mouseMoveHandler(e) {
      if (this.dragging) {
        const containerEl = document.getElementById(this.container_id);
        let boundingRect = containerEl.getBoundingClientRect();

        let newX = e.x - boundingRect.x - this.draggingOffsetX;
        let newY = e.y - boundingRect.y - this.draggingOffsetY;

        this.setChildPosition(this.dragging_index, newX, newY);
      }
    },

    mouseUpHandler(e) {
      this.handle_mouse_up(e);
      this.dragging = false;
    },

    mouseDownHandler(e) {
      // functionality to create new children?
      console.log("mouseDownHandler");
      console.log(e);
      this.handle_mouse_down(e);
      e.stopPropagation();
    },

    childMouseDownHandler(e, index) {
      console.log("childMouseDownHandler");
      // set everything for dragging except the actual dragging bool, allow
      // the python side to determine that. (prepare everything to begin
      // dragging, but don't actually start it, handle that on python side.)
      this.dragging_index = index;
      this.draggingOffsetX = e.layerX;
      this.draggingOffsetY = e.layerY;
      // Important to note that you can't pass more than one thing to python
      e.childIndex = index;
      console.log(index);
      this.handle_child_mouse_down(e);
      e.stopPropagation();
    },

    onResize() {
      console.log(this.$refs.ipyoverlay_container);
      let container = this.$refs.ipyoverlay_container;
      let width = container.offsetWidth;
      let height = container.offsetHeight;
      console.log(width + "," + height);
      this.handle_resize({"width": width, "height": height});
    },
  },
};
</script>

<style id="ipyoverlay-container-style">
.ipyoverlay-container {
  display: block;
  z-index: 20;
  top: 0;
  left: 0;
  background-color: #111111;
  overflow-y: scroll;
}

.ipyoverlay-child-container {
  display: block;
  position: absolute;
  /*z-index: 50;*/
}

/* TODO: these prob need to be an optional thing */
.jupyter-matplotlib-canvas-div {
  margin: 0 !important;
}
.jupyter-matplotlib-canvas-container {
  margin: 0 !important;
}
.jupyter-matplotlib-toolbar button {
  background-color: var(--jp-layout-color2, "#222222");
}

.ipyoverlay-screen-btn {
  position: absolute;
  /*visibility: hidden;*/
  right: 5px;
  top: 5px;
  z-index: 9000;
}
.ipyoverlay-screen-btn:hover {
  visibility: visible;
}
</style>
