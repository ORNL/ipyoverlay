<template>
  <div
    :id="wrapper_id"
    class="ipyoverlay-decorated-widget"
    :style="{
      borderColor: borderColor,
      backgroundColor: background_color,
      zIndex: z_index ,
      width: width === 'auto' ? 'auto' : width + 'px',
      height: height === 'auto' ? 'auto' : (height + decoration_height) + 'px'
    }"
    @mouseover="borderColor = hover_border_color"
    @mouseleave="borderColor = default_border_color"
    @mousedown="mouseDownHandler"
  >
    <div
      class="ipyoverlay-decorated-widget-header"
      :style="{ height: decoration_height + 'px', backgroundColor: headerBackgroundColor }"
    >
      <v-row class="header-row">
        <span style="margin-top: -2px">&nbsp;{{ title }}</span>
        <v-spacer />
        <v-btn
          v-if="closable"
          x-small
          elevation="0"
          tile
          class="close-btn"
          @mousedown="closeButtonHandler"
        >
          x
        </v-btn>
      </v-row>
    </div>
    <jupyter-widget :widget="widget" />
  </div>
</template>

<script>
module.exports = {
  data () {
    return {
      borderColor: "transparent", /* gets set to python default in the mounted check below */
      headerBackgroundColor: "#333333",
    };
  },
  mounted: function () {
    this.borderColor = this.default_border_color;
    this.headerBackgroundColor = this.default_header_color;
  },
  watch: {
    active() {
      if (this.active) {
        this.headerBackgroundColor = this.active_header_color;
      }
      else {
        this.headerBackgroundColor = this.default_header_color;
      }
    },
  },
  methods: {
    /**
     * Update the current_x and current_y in the python model,
     * this should get called after a mouse up event in the container
     */
    jupyter_updateCurrentPos() {
      const el = document.getElementById(this.wrapper_id);
      let boundingRect = el.getBoundingClientRect();

      this.current_x = boundingRect.x;
      this.current_y = boundingRect.y;
      this.current_height = boundingRect.height;
      this.current_width = boundingRect.width;
    },

    mouseDownHandler(e) {
      this.jupyter_updateCurrentPos();
      this.clicked = true;
    },

    closeButtonHandler(e) {
      this.handle_header_close_clicked();
      e.stopPropagation();
    },
  },
};
</script>

<style id="ipyoverlay-decorated-widget-style">
.ipyoverlay-decorated-widget {
  border-width: 1px;
  border-style: solid;
  display: block;
  z-index: 100;
  position: relative; /* necessary? */
}

.ipyoverlay-decorated-widget-header {
  background-color: #333333;
  width: 100%;
  display: block;
  z-index: 100;
  cursor: move;
}

.close-btn {
  /* Most of these heights will need to be set dynamically based on header_height */
  height: 15px !important;
  width: 15px !important;
  min-width: 15px !important;
  display: block !important;
  line-height: 15px !important;
}

.header-row {
  margin-left: 0px !important;
  margin-right: 0px !important;
}
</style>
