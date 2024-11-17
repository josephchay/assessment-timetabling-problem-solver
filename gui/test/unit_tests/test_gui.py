import time
import timetablinggui


class TestGUI:
    def __init__(self):
        self.root_gui = timetablinggui.TimetablingGUI()
        self.root_gui.title("TestGUI")

    def clean(self):
        self.root_gui.quit()
        self.root_gui.withdraw()

    def main(self):
        self.execute_tests()
        self.root_gui.mainloop()

    def execute_tests(self):
        print("\nTestGUI started:")
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
        self.root_gui.geometry("100x200+200+300")
        assert self.root_gui.current_width == 100 and self.root_gui.current_height == 200

        self.root_gui.minsize(300, 400)
        assert self.root_gui.current_width == 300 and self.root_gui.current_height == 400
        assert self.root_gui.min_width == 300 and self.root_gui.min_height == 400

        self.root_gui.maxsize(400, 500)
        self.root_gui.geometry("600x600")
        assert self.root_gui.current_width == 400 and self.root_gui.current_height == 500
        assert self.root_gui.max_width == 400 and self.root_gui.max_height == 500

        self.root_gui.maxsize(1000, 1000)
        self.root_gui.geometry("300x400")
        self.root_gui.resizable(False, False)
        self.root_gui.geometry("500x600")
        assert self.root_gui.current_width == 500 and self.root_gui.current_height == 600
        print("successful")

    def test_scaling(self):
        print(" -> test_scaling: ", end="")

        timetablinggui.ScalingTracker.set_window_scaling(1.5)
        self.root_gui.geometry("300x400")
        assert self.root_gui._current_width == 300 and self.root_gui._current_height == 400
        assert self.root_gui.window_scaling == 1.5 * timetablinggui.ScalingTracker.get_window_dpi_scaling(self.root_gui)

        self.root_gui.maxsize(400, 500)
        self.root_gui.geometry("500x500")
        assert self.root_gui._current_width == 400 and self.root_gui._current_height == 500

        timetablinggui.ScalingTracker.set_window_scaling(1)
        assert self.root_gui._current_width == 400 and self.root_gui._current_height == 500
        print("successful")

    def test_configure(self):
        print(" -> test_configure: ", end="")
        self.root_gui.configure(bg="white")
        assert self.root_gui.cget("fg_color") == "white"

        self.root_gui.configure(background="red")
        assert self.root_gui.cget("fg_color") == "red"
        assert self.root_gui.cget("bg") == "red"

        self.root_gui.config(fg_color=("green", "#FFFFFF"))
        assert self.root_gui.cget("fg_color") == ("green", "#FFFFFF")
        print("successful")

    def test_appearance_mode(self):
        print(" -> test_appearance_mode: ", end="")
        timetablinggui.set_appearance_mode("light")
        self.root_gui.config(fg_color=("green", "#FFFFFF"))
        assert self.root_gui.cget("bg") == "green"

        timetablinggui.set_appearance_mode("dark")
        assert self.root_gui.cget("bg") == "#FFFFFF"
        print("successful")

    def test_iconify(self):
        print(" -> test_iconify: ", end="")
        self.root_gui.iconify()
        self.root_gui.after(100, self.root_gui.deiconify)
        print("successful")


if __name__ == "__main__":
    TestGUI().main()
