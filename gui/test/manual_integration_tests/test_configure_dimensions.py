import timetablinggui
import random


app = timetablinggui.TimetablingGUI()
app.geometry("400x400")


def button_callback():
    button_1.configure(width=random.randint(30, 200), height=random.randint(30, 60))
    frame_1.configure(width=random.randint(30, 200), height=random.randint(30, 200))
    label_1.configure(width=random.randint(30, 200), height=random.randint(30, 40))
    entry_1.configure(width=random.randint(30, 200), height=random.randint(30, 40))
    progressbar_1.configure(width=random.randint(30, 200), height=random.randint(10, 16))
    slider_1.configure(width=random.randint(30, 200), height=random.randint(14, 20))


button_1 = timetablinggui.GUIButton(app, text="button_1", command=button_callback)
button_1.pack(pady=10)

frame_1 = timetablinggui.GUIFrame(app)
frame_1.pack(pady=10)

label_1 = timetablinggui.GUILabel(app, fg_color="green")
label_1.pack(pady=10)

entry_1 = timetablinggui.GUIEntry(app, placeholder_text="placeholder")
entry_1.pack(pady=10)

progressbar_1 = timetablinggui.GUIProgressBar(app)
progressbar_1.pack(pady=10)

slider_1 = timetablinggui.GUISlider(app)
slider_1.pack(pady=10)

app.mainloop()
