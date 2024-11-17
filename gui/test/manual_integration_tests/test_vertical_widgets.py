import timetablinggui

app = timetablinggui.TimetablingGUI()  # create GUI window like you do with the Tk window (you can also use normal tkinter.Tk window)
app.geometry("400x650")
app.title("test_vertical_widgets")

app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure((0, 1, 2, 3), weight=1)

progressbar_1 = timetablinggui.GUIProgressBar(app, orientation="horizontal")
progressbar_1.grid(row=0, column=0, pady=20, padx=20)

progressbar_2 = timetablinggui.GUIProgressBar(app, orientation="vertical")
progressbar_2.grid(row=1, column=0, pady=20, padx=20)

slider_1 = timetablinggui.GUISlider(app, orientation="horizontal", command=progressbar_1.set,
                                    button_corner_radius=3, button_length=20)
slider_1.grid(row=2, column=0, pady=20, padx=20)

slider_2 = timetablinggui.GUISlider(app, orientation="vertical", command=progressbar_2.set,
                                    button_corner_radius=3, button_length=20)
slider_2.grid(row=3, column=0, pady=20, padx=20)


app.mainloop()
