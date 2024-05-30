<template>
  <div
    :id="menu_id"
    ref="menu"
    class="ipyoverlay-context-menu"
    :style="{ width: width + 'px', display: visible ? 'block' : 'none' }"
    tabindex="0"
    @blur="lostFocus"
    @focus="gainedFocus"
  >
    <div class="ipyoverlay-context-menu-fixed">
      <ul :style="{ backgroundColor: background_color }">
        <li
          v-for="(option, index) in optionValues"
          class="ipyoverlay-context-menu-option"
          :style="{ backgroundColor: optionColor[index] }"
          @mouseover="setOptionBackgroundColor(index, hover_color)"
          @mouseleave="setOptionBackgroundColor(index, background_color)"
          @mousedown="fireOptionClickedEventHandler(index)"
          v-html="option"
        />
      </ul>
    </div>
  </div>
</template>

<script>
module.exports = {
  data() {
    return {
      //backgroundColor: "#333333",
      optionColor: [],

      optionKeys: [],
      optionValues: [],
    };
  },
  mounted: function () {
    this.refreshOptions();
  },
  watch: {
    options() {
      this.refreshOptions();
    },
    visible() {
      if (this.visible == true) {
        //const menuEl = document.getElementById(this.menu_id);
        const menuEl = this.$refs.menu;
        // https://stackoverflow.com/questions/4310639/cant-set-focus-on-a-text-field
        setTimeout(function() { menuEl.focus(); }, 1);
      }
    }
  },
  methods: {
    /**
     * fill optionKeys with the dictionary keys of options, and optionValues
     * with the html to display for each option.
     */
    refreshOptions() {
      console.log(this.options);
      this.optionColor = [];
      this.optionKeys = [];
      this.optionValues = [];
      for (let key in this.options) {
        this.optionColor.push(this.background_color);
        this.optionKeys.push(key);
        this.optionValues.push(this.options[key]);
      }
    },
    /**
     * Reminder that since optionColor is an array, and we're monitoring
     * specific indices in the div style in this template, we have to
     * reconstruct the whole color array for the reactivity to trigger.
     * @param index
     * @param color
     */
    setOptionBackgroundColor(index, color) {
      let newOptionColors = [];
      for (let i = 0; i < this.optionColor.length; i++) {
        if (i === index) { newOptionColors.push(color); }
        else { newOptionColors.push(this.optionColor[i]); }
      }
      this.optionColor = newOptionColors;
    },
    /**
     * Translate the index of the clicked option to the correct key, and fire
     * the event python-side.
     * @param index
     */
    fireOptionClickedEventHandler(index) {
      let key = this.optionKeys[index];

      // get the position attributes set from context-menu-area when right
      // click happened
      const menuEl = this.$refs.menu;
      let event_data = {
        "local_event_x": parseInt(menuEl.getAttribute("local_event_x")),
        "local_event_y": parseInt(menuEl.getAttribute("local_event_y")),
        "layer_event_x": parseInt(menuEl.getAttribute("layer_event_x")),
        "layer_event_y": parseInt(menuEl.getAttribute("layer_event_y")),
      };

      this.handle_option_clicked({"key": key, "event_data": event_data});
      this.visible = false;
    },
    gainedFocus(e) {
      console.log("Yep we have focus!");
    },
    lostFocus(e) {
      console.log("Losing focus");
      this.visible = false;
    },
  },
};
</script>

<style id="ipyoverlay-context-menu-style">
.ipyoverlay-context-menu {
  z-index: 2000;
  /*display: block;*/
  /*width: auto;*/
}
.ipyoverlay-context-menu-fixed {
  /*position: fixed;*/
  /*display: contents;*/
}
.ipyoverlay-context-menu ul {
  padding: 0px !important;
  padding-top: 2px !important;
  padding-bottom: 2px !important;
  list-style-type: none;
  z-index: 2000;
}
.ipyoverlay-context-menu ul li {
  padding-left: 10px;
  padding-right: 5px;
  padding-top: 1px;
  padding-bottom: 1px;
  z-index: 2001;
}
.ipyoverlay-context-menu ul li:not(:last-child) {
  border-bottom: 1px solid #4A4A4A;
}
</style>
