# IPyOverlay

The code for this project has not yet finished going through our open source release process.

![Demo GIF of interacting with a plot with ipyoverlay](img/demo.gif)
A GIF demoing interaction with an ipympl Matplotlib figure. In the demo,
Clicking a cluster opens a pop-up window with a new figure.

![Figures rendered on top of other figures](img/overlay_figures.png)
The background Matplotlib figure shown is rendered as an interactive ipympl
widget and wrapped in IPyOverlay’s `OverlayContainer`, and shows a UMAP of
clustered embeddings. Clicking a cluster or right-clicking and selecting an
exhibit creates a click-and-draggable pop-up window containing a new
visualization that plots more details for the selected cluster. Optionally, each
pop-up window can show a line connecting the window to the center of the cluster
it is associated with in the underlying figure. 

![Right click context menu](img/context_menu.png) 
Custom actions can be added as A right-click menu to any widget. This menu is
specific to this Matplotlib UMAP and allows users to choose whether to open a
violin or distribution plot for the hovered cluster. 

![Overlay widgets can span larger areas in the notebook](img/overlay_figures_over_multiple.png)
If multiple separate “background” widgets (Matplotlib UMAP on the left and
Plotly map on the right) are wrapped in an `OverlayContainer`, overlay widgets
can be displayed and dragged over all of them. 
