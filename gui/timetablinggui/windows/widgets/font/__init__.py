import os
import sys

from .gui_font import GUIFont
from .font_manager import FontManager

# import DrawEngine to set preferred_drawing_method if loading shapes font fails
from ..core_rendering import DrawEngine

FontManager.init_font_manager()

# load Roboto fonts (used on Windows/Linux)
timetablinggui_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FontManager.load_font(os.path.join(timetablinggui_directory, "assets", "fonts", "Roboto", "Roboto-Regular.ttf"))
FontManager.load_font(os.path.join(timetablinggui_directory, "assets", "fonts", "Roboto", "Roboto-Medium.ttf"))

# load font necessary for rendering the widgets (used on Windows/Linux)
if FontManager.load_font(os.path.join(timetablinggui_directory, "assets", "fonts", "timetablinggui_shapes_font.otf")) is False:
    # change draw method if font loading failed
    if DrawEngine.preferred_drawing_method == "font_shapes":
        sys.stderr.write("timetablinggui.windows.widgets.font warning: " +
                         "Preferred drawing method 'font_shapes' can not be used because the font file could not be loaded.\n" +
                         "Using 'circle_shapes' instead. The rendering quality will be bad!\n")
        DrawEngine.preferred_drawing_method = "circle_shapes"
