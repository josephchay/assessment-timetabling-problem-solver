import tkinter.messagebox
import timetablinggui

timetablinggui.set_appearance_mode("dark")


class App(timetablinggui.TimetablingGUI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("test filedialog")

        self.button_1 = timetablinggui.GUIButton(master=self, text="askopenfile", command=lambda: print(timetablinggui.filedialog.askopenfile()))
        self.button_1.pack(pady=10)
        self.button_2 = timetablinggui.GUIButton(master=self, text="askopenfiles", command=lambda: print(timetablinggui.filedialog.askopenfiles()))
        self.button_2.pack(pady=10)
        self.button_3 = timetablinggui.GUIButton(master=self, text="askdirectory", command=lambda: print(timetablinggui.filedialog.askdirectory()))
        self.button_3.pack(pady=10)
        self.button_4 = timetablinggui.GUIButton(master=self, text="asksaveasfile", command=lambda: print(timetablinggui.filedialog.asksaveasfile()))
        self.button_4.pack(pady=10)
        self.button_5 = timetablinggui.GUIButton(master=self, text="askopenfilename", command=lambda: print(timetablinggui.filedialog.askopenfilename()))
        self.button_5.pack(pady=10)
        self.button_6 = timetablinggui.GUIButton(master=self, text="askopenfilenames", command=lambda: print(timetablinggui.filedialog.askopenfilenames()))
        self.button_6.pack(pady=10)
        self.button_7 = timetablinggui.GUIButton(master=self, text="asksaveasfilename", command=lambda: print(timetablinggui.filedialog.asksaveasfilename()))
        self.button_7.pack(pady=10)


if __name__ == "__main__":
    app = App()
    app.mainloop()
