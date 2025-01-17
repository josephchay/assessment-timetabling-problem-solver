import tkinter
import timetablinggui

timetablinggui.set_appearance_mode("System")  # Other: "Dark", "Light"


class TestApp(timetablinggui.TimetablingGUI):
    def __init__(self):
        super().__init__()
        self.geometry(f"{1400}x{700}")
        self.title("timetablinggui complete test")

        self.create_widgets_on_tk()
        self.create_widgets_on_gui_frame()
        self.create_widgets_on_gui_frame_customized()
        self.create_widgets_on_tk_frame_customized()

    def change_appearance_mode(self, value):
        """ gets called by self.slider_1 """

        if value == 0:
            self.label_1.configure(text="mode: Light")
            timetablinggui.set_appearance_mode("Light")
        elif value == 1:
            self.label_1.configure(text="mode: Dark")
            timetablinggui.set_appearance_mode("Dark")
        else:
            self.label_1.configure(text="mode: System")
            timetablinggui.set_appearance_mode("System")

    def create_widgets_on_tk(self):
        x, y = 150, 80

        self.label_1 = timetablinggui.GUILabel(master=self, text="widgets_on_tk", fg_color="gray50")
        self.label_1.place(x=x, y=y, anchor=tkinter.CENTER)

        self.frame_1 = timetablinggui.GUIFrame(master=self, width=200, height=60)
        self.frame_1.place(x=x, y=y+80, anchor=tkinter.CENTER)

        self.button_1 = timetablinggui.GUIButton(master=self)
        self.button_1.place(x=x, y=y + 160, anchor=tkinter.CENTER)

        self.entry_1 = timetablinggui.GUIEntry(master=self)
        self.entry_1.place(x=x, y=y + 240, anchor=tkinter.CENTER)

        self.progress_bar_1 = timetablinggui.GUIProgressBar(master=self)
        self.progress_bar_1.place(x=x, y=y + 320, anchor=tkinter.CENTER)

        self.slider_1 = timetablinggui.GUISlider(master=self, command=self.change_appearance_mode, from_=0, to=2, number_of_steps=2)
        self.slider_1.place(x=x, y=y + 400, anchor=tkinter.CENTER)

        self.check_box_1 = timetablinggui.GUICheckBox(master=self)
        self.check_box_1.place(x=x, y=y + 480, anchor=tkinter.CENTER)

    def create_widgets_on_gui_frame(self):
        x, y = 450, 40

        self.gui_frame = timetablinggui.GUIFrame(master=self, width=300, height=600)
        self.gui_frame.place(x=x, y=y, anchor=tkinter.N)

        self.label_2 = timetablinggui.GUILabel(master=self.gui_frame, text="create_widgets_on_gui_frame", fg_color="gray50", width=200)
        self.label_2.place(relx=0.5, y=y, anchor=tkinter.CENTER)

        self.frame_2 = timetablinggui.GUIFrame(master=self.gui_frame, width=200, height=60)
        self.frame_2.place(relx=0.5, y=y + 80, anchor=tkinter.CENTER)

        self.button_2 = timetablinggui.GUIButton(master=self.gui_frame, border_width=3)
        self.button_2.place(relx=0.5, y=y + 160, anchor=tkinter.CENTER)

        self.entry_2 = timetablinggui.GUIEntry(master=self.gui_frame)
        self.entry_2.place(relx=0.5, y=y + 240, anchor=tkinter.CENTER)

        self.progress_bar_2 = timetablinggui.GUIProgressBar(master=self.gui_frame)
        self.progress_bar_2.place(relx=0.5, y=y + 320, anchor=tkinter.CENTER)

        self.slider_2 = timetablinggui.GUISlider(master=self.gui_frame, command=lambda v: self.label_2.configure(text=str(round(v, 5))))
        self.slider_2.place(relx=0.5, y=y + 400, anchor=tkinter.CENTER)

        self.check_box_2 = timetablinggui.GUICheckBox(master=self.gui_frame)
        self.check_box_2.place(relx=0.5, y=y + 480, anchor=tkinter.CENTER)

    def change_frame_color(self, value):
        """ gets called by self.slider_3 """

        def rgb2hex(rgb_color: tuple) -> str:
            return "#{:02x}{:02x}{:02x}".format(round(rgb_color[0]), round(rgb_color[1]), round(rgb_color[2]))

        col_1 = rgb2hex((100, 50, value * 250))
        col_2 = rgb2hex((20, value * 250, 50))

        self.gui_frame_customized.configure(fg_color=col_1)
        self.tk_frame_customized.configure(bg=col_1)
        self.configure(bg=col_2)
        self.progress_bar_3.set(value)

    def create_widgets_on_gui_frame_customized(self):
        x, y = 800, 40

        self.gui_frame_customized = timetablinggui.GUIFrame(master=self, width=300, height=600)
        self.gui_frame_customized.place(x=x, y=y, anchor=tkinter.N)
        self.gui_frame_customized.configure(fg_color=("#F4F4FA", "#1E2742"))

        self.label_3 = timetablinggui.GUILabel(master=self.gui_frame_customized, text="customized", corner_radius=60,
                                               font=("times", 16))
        self.label_3.place(relx=0.5, y=y, anchor=tkinter.CENTER)
        self.label_3.configure(fg_color=("#F4F4FA", "#333D5E"), text_color=("#373E57", "#7992C1"))

        self.frame_3 = timetablinggui.GUIFrame(master=self.gui_frame_customized, width=200, height=60)
        self.frame_3.place(relx=0.5, y=y + 80, anchor=tkinter.CENTER)
        self.frame_3.configure(fg_color=("#EBECF3", "#4B577E"))

        self.button_3 = timetablinggui.GUIButton(master=self.gui_frame_customized, command=lambda: None, border_width=3,
                                                 corner_radius=20, font=("times", 16))
        self.button_3.place(relx=0.5, y=y + 160, anchor=tkinter.CENTER)
        self.button_3.configure(border_color=("#4F90F8", "#6FADF9"), hover_color=("#3A65E8", "#4376EE"))
        self.button_3.configure(fg_color="transparent")

        self.entry_3 = timetablinggui.GUIEntry(master=self.gui_frame_customized, font=("times", 16))
        self.entry_3.place(relx=0.5, y=y + 240, anchor=tkinter.CENTER)
        self.entry_3.configure(fg_color=("gray60", "gray5"), corner_radius=20)
        self.entry_3.insert(0, "1234567890")
        self.entry_3.focus_set()

        self.progress_bar_3 = timetablinggui.GUIProgressBar(master=self.gui_frame_customized, height=16, fg_color=("#EBECF3", "#4B577E"))
        self.progress_bar_3.place(relx=0.5, y=y + 320, anchor=tkinter.CENTER)
        self.progress_bar_3.configure(progress_color="#8AE0C3", border_width=3, border_color=("gray60", "#4B577E"))

        self.slider_3 = timetablinggui.GUISlider(master=self.gui_frame_customized, command=self.change_frame_color, from_=0, to=10)
        self.slider_3.place(relx=0.5, y=y + 400, anchor=tkinter.CENTER)
        self.slider_3.configure(button_color="#8AE0C3", fg_color=("#EBECF3", "#4B577E"), progress_color=("gray30", "gray10"))
        self.slider_3.configure(from_=0, to=1)

        self.check_box_3 = timetablinggui.GUICheckBox(master=self.gui_frame_customized, corner_radius=50, font=("times", 16))
        self.check_box_3.place(relx=0.5, y=y + 480, anchor=tkinter.CENTER)
        self.check_box_3.configure(border_color="#8AE0C3")

    def create_widgets_on_tk_frame_customized(self):
        x, y = 1150, 40

        self.tk_frame_customized = tkinter.Frame(master=self, width=300, height=600, bg="darkred")
        self.tk_frame_customized.place(x=x, y=y, anchor=tkinter.N)

        self.label_4 = timetablinggui.GUILabel(master=self.tk_frame_customized, text="customized", corner_radius=6)
        self.label_4.place(relx=0.5, y=y, anchor=tkinter.CENTER)
        self.label_4.configure(fg_color=("#F4F4FA", "#333D5E"), text_color=("#373E57", "#7992C1"))

        self.frame_4 = timetablinggui.GUIFrame(master=self.tk_frame_customized, width=200, height=60)
        self.frame_4.place(relx=0.5, y=y + 80, anchor=tkinter.CENTER)
        self.frame_4.configure(fg_color=("#EBECF3", "#4B577E"))

        self.button_4 = timetablinggui.GUIButton(master=self.tk_frame_customized, command=lambda: x, border_width=3)
        self.button_4.place(relx=0.5, y=y + 160, anchor=tkinter.CENTER)
        self.button_4.configure(border_color=("#4F90F8", "#6FADF9"), hover_color=("#3A65E8", "#4376EE"))
        self.button_4.configure(fg_color="transparent")

        self.entry_4 = timetablinggui.GUIEntry(master=self.tk_frame_customized)
        self.entry_4.place(relx=0.5, y=y + 240, anchor=tkinter.CENTER)
        self.entry_4.configure(fg_color=("gray60", "gray5"))
        self.entry_4.insert(0, "1234567890")
        self.entry_4.focus_set()

        self.progress_bar_4 = timetablinggui.GUIProgressBar(master=self.tk_frame_customized, height=16, fg_color=("#EBECF3", "#4B577E"))
        self.progress_bar_4.place(relx=0.5, y=y + 320, anchor=tkinter.CENTER)
        self.progress_bar_4.configure(progress_color="#8AE0C3", border_width=3, border_color=("gray60", "#4B577E"))

        self.slider_4 = timetablinggui.GUISlider(master=self.tk_frame_customized, command=self.change_frame_color, from_=0, to=10)
        self.slider_4.place(relx=0.5, y=y + 400, anchor=tkinter.CENTER)
        self.slider_4.configure(button_color="#8AE0C3", fg_color=("#EBECF3", "#4B577E"), progress_color=("gray30", "gray10"))
        self.slider_4.configure(from_=0, to=1)

        self.check_box_4 = timetablinggui.GUICheckBox(master=self.tk_frame_customized)
        self.check_box_4.place(relx=0.5, y=y + 480, anchor=tkinter.CENTER)
        self.check_box_4.configure(border_color="#8AE0C3")


if __name__ == "__main__":
    test_app = TestApp()
    test_app.mainloop()
