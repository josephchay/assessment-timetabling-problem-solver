import timetablinggui

timetablinggui.set_appearance_mode("dark")
timetablinggui.set_default_color_theme("blue")
timetablinggui.set_window_scaling(0.8)
timetablinggui.set_widget_scaling(0.8)

app = timetablinggui.TimetablingGUI()
app.geometry("400x300")
app.title("GUIDialog Test")


def change_mode():
    if c1.get() == 0:
        timetablinggui.set_appearance_mode("light")
    else:
        timetablinggui.set_appearance_mode("dark")


def button_1_click_event():
    dialog = timetablinggui.GUIInputDialog(text="Type in a number:", title="Test")
    print("Number:", dialog.get_input())


def button_2_click_event():
    dialog = timetablinggui.GUIInputDialog(text="long text " * 100, title="Test")
    print("Number:", dialog.get_input())


button_1 = timetablinggui.GUIButton(app, text="Open Dialog", command=button_1_click_event)
button_1.pack(pady=20)
button_2 = timetablinggui.GUIButton(app, text="Open Dialog", command=button_2_click_event)
button_2.pack(pady=20)
c1 = timetablinggui.GUICheckBox(app, text="dark mode", command=change_mode)
c1.pack(pady=20)

app.mainloop()
