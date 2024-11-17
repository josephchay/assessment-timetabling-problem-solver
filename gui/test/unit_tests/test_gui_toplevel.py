import timetablinggui


class TestGUIToplevel:
    def __init__(self):
        self.root_gui = timetablinggui.TimetablingGUI()
        self.root_gui.title("TestGUIToplevel")
        self.gui_toplevel = timetablinggui.GUIToplevel()
        self.gui_toplevel.title("TestGUIToplevel")

    def clean(self):
        self.root_gui.quit()
        self.gui_toplevel.withdraw()
        self.root_gui.withdraw()

    def main(self):
        self.execute_tests()
        self.root_gui.mainloop()

    def execute_tests(self):
        print("\nTestGUIToplevel started:")
        start_time = 0

        self.root_gui.after(start_time, self.test_geometry)
        start_time += 100

        self.root_gui.after(start_time, self.test_scaling)
        start_time += 100

        self.root_gui.after(start_time, self.test_configure)
        start_time += 100

        self.root_gui.after(start_time, self.test_appearance_mode)
        start_time += 100

        self.root_gui.after(start_time, self.test_iconify)
        start_time += 1500

        self.root_gui.after(start_time, self.clean)

    def test_geometry(self):
        print(" -> test_geometry: ", end="")
        self.gui_toplevel.geometry("200x300+200+300")
        assert self.gui_toplevel.current_width == 200 and self.gui_toplevel.current_height == 300

        self.gui_toplevel.minsize(300, 400)
        assert self.gui_toplevel.current_width == 300 and self.gui_toplevel.current_height == 400
        assert self.gui_toplevel.min_width == 300 and self.gui_toplevel.min_height == 400

        self.gui_toplevel.maxsize(400, 500)
        self.gui_toplevel.geometry("600x600")
        assert self.gui_toplevel.current_width == 400 and self.gui_toplevel.current_height == 500
        assert self.gui_toplevel.max_width == 400 and self.gui_toplevel.max_height == 500

        self.gui_toplevel.maxsize(1000, 1000)
        self.gui_toplevel.geometry("300x400")
        self.gui_toplevel.resizable(False, False)
        self.gui_toplevel.geometry("500x600")
        assert self.gui_toplevel.current_width == 500 and self.gui_toplevel.current_height == 600
        print("successful")

    def test_scaling(self):
        print(" -> test_scaling: ", end="")

        timetablinggui.ScalingTracker.set_window_scaling(1.5)
        self.gui_toplevel.geometry("300x400")
        assert self.gui_toplevel.current_width == 300 and self.gui_toplevel.current_height == 400
        assert self.root_gui.window_scaling == 1.5 * timetablinggui.ScalingTracker.get_window_dpi_scaling(self.root_gui)

        self.gui_toplevel.maxsize(400, 500)
        self.gui_toplevel.geometry("500x500")
        assert self.gui_toplevel.current_width == 400 and self.gui_toplevel.current_height == 500

        timetablinggui.ScalingTracker.set_window_scaling(1)
        assert self.gui_toplevel.current_width == 400 and self.gui_toplevel.current_height == 500
        print("successful")

    def test_configure(self):
        print(" -> test_configure: ", end="")
        self.gui_toplevel.configure(bg="white")
        assert self.gui_toplevel.fg_color == "white"

        self.gui_toplevel.configure(background="red")
        assert self.gui_toplevel.fg_color == "red"
        assert self.gui_toplevel.cget("bg") == "red"

        self.gui_toplevel.config(fg_color=("green", "#FFFFFF"))
        assert self.gui_toplevel.fg_color == ("green", "#FFFFFF")
        print("successful")

    def test_appearance_mode(self):
        print(" -> test_appearance_mode: ", end="")
        timetablinggui.set_appearance_mode("light")
        self.gui_toplevel.config(fg_color=("green", "#FFFFFF"))
        assert self.gui_toplevel.cget("bg") == "green"

        timetablinggui.set_appearance_mode("dark")
        assert self.gui_toplevel.cget("bg") == "#FFFFFF"
        print("successful")

    def test_iconify(self):
        print(" -> test_iconify: ", end="")
        self.gui_toplevel.iconify()
        self.gui_toplevel.after(100, self.gui_toplevel.deiconify)
        print("successful")


if __name__ == "__main__":
    TestGUIToplevel()
