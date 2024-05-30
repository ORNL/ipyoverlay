<template>
  <div class="ipyui-popup" style="display: none;">
    <h1>YOOOO</h1>
    <jupyter-widget :widget="widget" />
  </div>
</template>

<script>
module.exports = {
  data() {
    return {
      windowRef: null,
      headObserver: null,
    };
  },
  methods: {
    jupyter_openPortal() {
      console.log("Opening...");
      this.windowRef = window.open("", "", "popup,width=" + this.width + ",height=" + this.height + ",left=" + this.left + ",top=" + this.top);
      this.windowRef.addEventListener("beforeunload", this.jupyter_closePortal);

      let el = document.createElement("body");
      this.$el.style.display = "block";
      el.appendChild(this.$root.$el);  // actually not sure if this will potentially grab more things...this is prob wrong.

      //this.transferCSS();
      this.transferHead();

      this.windowRef.document.body = el;
      this.is_open = true;
    },

    jupyter_closePortal() {
      console.log("Trying to close...");
      if(this.windowRef) {
        console.log("Yep we're closing");
        this.$el.style.display = "none";
        this.windowRef.close();
        this.windowRef = null;
        this.is_open = false;
      }
    },

    initObserver() {
      const config = { childList: true };
      const observer = new MutationObserver(this.onHeadChildListChange);
      observer.observe(document.head, config);
      this.observer = observer;
    },

    onHeadChildListChange(mutationList, observer) {
      if (!this.windowRef) { return; }

      for (const mutation of mutationList) {
        if (mutation.type === "childList" && mutation.addedNodes.length > 0) {

          for (let i = 0; i < mutation.addedNodes.length; i++) {
            let node = mutation.addedNodes[i];
            let tag = node.tagName.toLowerCase();
            if (tag === "style" || tag === "script") {
              // TODO: or linking a css stylesheet
              console.log("Yup copying a new stylesheet or script over!");
              this.windowRef.document.head.appendChild(node.cloneNode(true));
            }
          }
        }
      }
    },

    transferHead() {
      if (!this.windowRef) { return; }

      for (let i = 0; i < document.head.childNodes.length; i++) {
        let node = document.head.childNodes[i];
        if (node.tagName === undefined) { continue; }
        let tag = node.tagName.toLowerCase();
        if (tag === "style" || tag === "link" || tag === "script") {
          this.windowRef.document.head.appendChild(node.cloneNode(true));
        }
      }
    },

    /*transferCSS() {
        if (this.windowRef) {
          let sheets = document.styleSheets;
          for (let i in sheets) {
            console.log(sheets[i]);
            if (sheets[i].ownerNode) {
              if (!this.windowRef.document.head.contains(sheets[i].ownerNode)) {
                console.log("Copying! " + i);
                this.windowRef.document.head.appendChild(sheets[i].ownerNode.cloneNode(true));
              }
            }
          }
        }
      },*/
  },
  mounted() {
    this.initObserver();
  },
  beforeDestroy() {
    if (this.windowRef) {
      this.jupyter_closePortal();
    }
  }
};
</script>

<style id="ipyui-popup-component-style">
.ipyui-popup {
  /*color: white;*/
}
</style>
