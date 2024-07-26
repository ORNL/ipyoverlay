<template>
  <svg
    :id="connection_id"
    :width="width"
    :height="height"
    class="ipyoverlay-connection-line"
    :style="{ visibility: visibility }"
  >
    <line
      :x1="currentX1"
      :y1="currentY1"
      :x2="currentX2"
      :y2="currentY2"
      stroke="white"
      stroke-width="2"
      custom="yes"
    />
    <line
      :x1="currentX1"
      :y1="currentY1"
      :x2="currentX2"
      :y2="currentY2"
      stroke="black"
      stroke-width="1"
      custom="yes"
    />
  </svg>
</template>

<script>
module.exports = {
  data() {
    return {
      currentX1: -1,
      currentY1: -1,
      currentX2: -1,
      currentY2: -1,
      visibility: "hidden",

      plotlyDivs: [],
      mplDivs: [],

      // these are the corner data values of the plotly plot if relevant
      plotlyX0: -1,
      plotlyX1: -1,
      plotlyY0: -1,
      plotlyY1: -1,
    };
  },
  mounted: function() {
    this.currentX1 = this.x1;
    this.currentY1 = this.y1;
    this.currentX2 = this.x2;
    this.currentY2 = this.y2;
    this.updateVisibility();

    if (this.plotly_div_class !== "") {
      this.storePlotlyDivReference(this.plotly_div_class);
    }
  },
  watch: {
    x1() { this.currentX1 = this.x1; this.updateVisibility(); },
    y1() { this.currentY1 = this.y1; this.updateVisibility(); },
    x2() { this.currentX2 = this.x2; this.updateVisibility(); },
    y2() { this.currentY2 = this.y2; this.updateVisibility(); },

    // the python side for plotly and mpl connections add a special class
    // to the container div (which plotly/mpl python APIs respectively handle)
    // and we store them here so the JS side has an easy way to reference the
    // appropriate DOM element.
    plotly_div_class() { this.storePlotlyDivReference(this.plotly_div_class); },
    mpl_div_class() { this.storeMPLDivReference(this.mpl_div_class); },
  },
  methods: {
    // ============================================================
    // PYTHON-CALLABLE FUNCTIONS
    // ============================================================

    /**
     * Get the current endpoints for the line and communicate them back to
     * python-visible variables.
     */
    jupyter_updateCurrentPos() {
      const el = document.getElementById(this.connection_id);
      this.x1 = parseFloat(el.children[0].getAttribute("x1"));
      this.y1 = parseFloat(el.children[0].getAttribute("y1"));
      this.x2 = parseFloat(el.children[0].getAttribute("x2"));
      this.y2 = parseFloat(el.children[0].getAttribute("y2"));
    },
    jupyter_convertMPLRelativePxToPx(x, y) {
      console.log("Converting relative px to actual px for " + this.connection_id.toString());
      //let div = this.mplDivs[0];
      // see point in storeMPLDivReference for why above doesn't work
      let query_str = "#" + this.container_id + " ." + this.mpl_div_class;
      let div = document.querySelector(query_str);
      // I can't just use this div because it also includes e.g. the ipympl
      // header if it exists, so I have to use the rect of the actual canvas
      // object.
      let rect = div.querySelector("canvas").getBoundingClientRect();
      let container = document.getElementById(this.container_id);
      let containerRect = container.getBoundingClientRect();

      console.log("Before: " + x.toString() + "," + y.toString());

      let pixelX = x + rect.left - containerRect.left;
      let pixelY = y + rect.top - containerRect.top;

      console.log("After: " + pixelX.toString() + "," + pixelY.toString());

      this.currentX2 = pixelX;
      this.currentY2 = pixelY;
      this.x2 = pixelX;
      this.y2 = pixelY;
      return [pixelX, pixelY];
    },

    // ============================================================
    // INTERNAL FUNCTIONS
    // ============================================================


    /**
     * Hide the line if any coordinates are out of range, to avoid panned plots
     * from showing connections to upper left corner if out of the current view.
     */
    updateVisibility() {
      if (this.currentX1 === -1 || this.currentX2 === -1 || this.currentY1 === -1 || this.currentY2 === -1) {
        this.visibility = "hidden";
      }
      else { this.visibility = "visible"; }
    },
    /**
     * Attaching a connection to a plotly plot has several challenges - namely
     * that any layout changes don't communicate things like new axis ranges
     * to the python side, so we can't do the same type of event handler setup
     * deal as for matplotlib. The second challenge is that even from the JS
     * side, since the div was created via ipywidgets we have no explicit
     * reference to the plotly graph div (which we need to _actually_ attach
     * an event handler to listen to those axis range change events.)
     *
     * Our delightful hack to deal with this is to add a super uber definitely
     * unique class from the python side (which so happens to add said class
     * to the actual div we care about), then search for that element from
     * here, and then re-remove the class from within python.
     * @param className The string class name assigned to the div containing the
     * plotly graph.
     */
    // TODO: one potential flaw is this won't auto-trigger when a cell is
    // re-rendered. There's probably a way we can listen for view count
    // changing on the python side though.
    //jupyter_storePlotlyDivReference(className) {
    storePlotlyDivReference(className) {
      this.plotlyDivs = document.getElementsByClassName(className);
      this.addPlotlyEventHandlers();
    },
    /**
     * To watch for plotly viewport changes, we have to manually attach event
     * handlers for relayout events so we can update connection endpoints when
     * pointed to data values.
     */
    addPlotlyEventHandlers() {
      console.log("Adding event handlers...");
      console.log(this.plotlyDivs);
      for (let i = 0; i < this.plotlyDivs.length; i++) {
        let div = this.plotlyDivs[i];
        console.log(div);
        var _this = this;
        div.on("plotly_relayout", function(eventdata) {
          console.log("RELAYOUT");
          console.log(eventdata);
          // handle map plots
          // https://stackoverflow.com/questions/3590685/accessing-this-from-within-an-objects-inline-function
          if (Object.hasOwn(eventdata, "mapbox._derived")) {
            let cornerLatLongs = eventdata["mapbox._derived"].coordinates;
            _this.plotlyX0 = cornerLatLongs[0][0];
            _this.plotlyX1 = cornerLatLongs[1][0];
            _this.plotlyY0 = cornerLatLongs[1][1];
            _this.plotlyY1 = cornerLatLongs[2][1];
            _this.convertPlotlyDataToPx();
          }
        });

        // if it's a map, get initial derived coordinates...
        console.log(div._fullLayout);
        if (Object.hasOwn(div._fullLayout, "mapbox")) {
          console.log("Yep it's a map!");
          let cornerLatLongs = div._fullLayout.mapbox._subplot.getView()._derived.coordinates;
          this.plotlyX0 = cornerLatLongs[0][0];
          this.plotlyX1 = cornerLatLongs[1][0];
          this.plotlyY0 = cornerLatLongs[1][1];
          this.plotlyY1 = cornerLatLongs[2][1];
          this.convertPlotlyDataToPx();
        }
      }
    },
    /**
     * Using the current plotly axis ranges, determine what the assigned plotly
     * data values would be in pixels and move the endpoints.
     */
    convertPlotlyDataToPx() {
      // roughly following the logic of utils.convert_mpl_data_to_pixel

      let div = this.plotlyDivs[0];
      let rect = div.getBoundingClientRect();
      let container = document.getElementById(this.container_id);
      let containerRect = container.getBoundingClientRect();
      console.log(rect);

      let pixelX = 0;
      let pixelY = 0;

      if (Object.hasOwn(div._fullLayout, "mapbox")) {
        let newPoint = div._fullLayout.mapbox._subplot.map.project([this.data_x, this.data_y]);
        console.log("Mapbox project returned:");
        console.log(newPoint);
        console.log("Container:");
        console.log(containerRect);

        pixelX = newPoint.x + rect.left - containerRect.left;
        pixelY = newPoint.y + rect.top - containerRect.top;
      }
      else {
        // ---- X ----

        let dataMinX = this.plotlyX0;
        let dataMaxX = this.plotlyX1;

        // get scalar from 0-1 that reps linear loc for x
        let windowDataX = this.data_x - dataMinX;
        let dataRangeX = dataMaxX - dataMinX;
        let scalarX = windowDataX / dataRangeX;

        // transform the scalar in terms of axis pixels
        let axisRangeX = rect.width;
        let pixelX = axisRangeX * scalarX + rect.left - containerRect.left;

        // ---- Y ----

        let dataMinY = this.plotlyY0;
        let dataMaxY = this.plotlyY1;

        // get scalar from 0-1 that reps linear loc for y
        let windowDataY = this.data_y - dataMinY;
        let dataRangeY = dataMaxY - dataMinY;
        let scalarY = windowDataY / dataRangeY;

        // transform the scalar in terms of axis pixels
        let axisRangeY = rect.height;
        let pixelY = axisRangeY * scalarY + rect.top - containerRect.top;
      }

      this.currentX2 = pixelX;
      this.currentY2 = pixelY;
    },
    storeMPLDivReference(className) {
      // partially because of issue #1, if the ipympl plot is rendered anytime
      // in a cell before the container is/ipympl plot rendered again, this
      // first div is pointing to the wrong one. Eventually may want to consider
      // getting rid of this alltogether, since we have the classname and
      // container id available anyway and can query live. (NOTE: this doesn't
      // solve if the container is rendered more than once)
      this.mplDivs = document.getElementsByClassName(className);
    },
  },
};
</script>
<style id='ipyoverlay-connection-style'>
.ipyoverlay-connection-line {
  z-index: 90;
  display: block;
  position: absolute;
  pointer-events: none;
  top: 0;
  left: 0;
}
</style>
