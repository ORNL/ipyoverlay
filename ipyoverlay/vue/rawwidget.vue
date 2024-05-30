<template>
  <div
    class="ipyoverlay-rawwidget"
    :style="{ borderColor: borderColor, backgroundColor: background_color }"
    @mouseover="borderColor = hover_border_color"
    @mouseleave="borderColor = default_border_color"
    @mousedown="mouseDownHandler"
  >
    <jupyter-widget :widget="widget" />
  </div>
</template>

<script>
module.exports = {
  data () {
    return {
      borderColor: "transparent", /* gets set to python default in the mounted check below */
    };
  },
  mounted: function () {
    this.borderColor = this.default_border_color;
  },
  methods: {
    mouseDownHandler(e) {  // eslint-disable-line no-unused-vars
      console.log("Handling mouse down in the thing itself!");
      this.clicked = true;
    }
  },
};
</script>

<style id="ipyoverlay-rawwidget-style">
.ipyoverlay-rawwidget {
  border-width: 1px;
  border-style: solid;
  display: block;
  z-index: 100;
  position: relative; /* necessary? */
}
</style>
