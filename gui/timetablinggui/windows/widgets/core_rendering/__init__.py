import sys

from .gui_canvas import GUICanvas
from .draw_engine import DrawEngine

GUICanvas.init_font_character_mapping()

# determine draw method based on current platform
if sys.platform == "darwin":
    DrawEngine.preferred_drawing_method = "polygon_shapes"
else:
    DrawEngine.preferred_drawing_method = "font_shapes"
