import time
import timetablinggui


class TestGUIButton:
    def __init__(self):
        self.root_gui = timetablinggui.TimetablingGUI()
        self.gui_button = timetablinggui.GUIButton(self.root_gui)
        self.gui_button.pack(padx=20, pady=20)
        self.root_gui.title(self.__class__.__name__)

    def clean(self):
        self.root_gui.quit()
        self.root_gui.withdraw()

    def main(self):
        self.execute_tests()
        self.root_gui.mainloop()

    def execute_tests(self):
        print(f"\n{self.__class__.__name__} started:")

        start_time = 0

        self.root_gui.after(start_time, self.test_iconify)
        start_time += 1500

        self.root_gui.after(start_time, self.clean)

    def test_iconify(self):
        print(" -> test_iconify: ", end="")
        self.root_gui.iconify()
        self.root_gui.after(100, self.root_gui.deiconify)
        print("successful")


if __name__ == "__main__":
    TestGUIButton().main()
