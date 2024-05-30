<template>
  <div
    :id="area_id"
    ref="area"
    class="ipyoverlay-context-menu-area"
    @mousedown="mouseDownHandler"
    @contextmenu="contextMenuHandler"
  >
    <jupyter-widget
      :widget="widget"
    />
    <jupyter-widget
      ref="menu"
      class="ipyoverlay-context-menu-area-menu"
      :widget="menu"
    />
  </div>
</template>

<script>
module.exports = {
  data () { return { }; },
  methods: {
    mouseDownHandler(e) {
      if (e.button === 2 && this.force_right_click) {
        this.contextMenuHandler(e);
      }
    },
    contextMenuHandler(e) {
      if (!this.enabled) { return; }

      this.set_menu_visible(true);

      const menuEl = this.$refs.menu.$el;
      console.log(menuEl);
      menuEl.style.display = "block";
      // if you don't set display to block before trying to get the rect, the
      // rect will just be zeros, because the element isn't actually visible
      // yet. (not sure why set_menu_visible doesn't trigger first, guessing
      // there's async stuff for Python <-> JS
      let offsetRect = menuEl.offsetParent.getBoundingClientRect();

      menuEl.style.left = e.x - offsetRect.x + "px";
      menuEl.style.top = e.y - offsetRect.y + "px";

      // record where event took place so we can pass to event handlers
      menuEl.setAttribute("local_event_x", e.x - offsetRect.x);
      menuEl.setAttribute("local_event_y", e.y - offsetRect.y);

      menuEl.setAttribute("layer_event_x", e.layerX);
      menuEl.setAttribute("layer_event_y", e.layerY);

      e.preventDefault();
      e.stopPropagation();
    },
  },
};
</script>

<style id="ipyoverlay-context-menu-area-style">
.ipyoverlay-context-menu-area {
  display: contents;
}
.ipyoverlay-context-menu-area-menu {
  position: fixed;
}
</style>
