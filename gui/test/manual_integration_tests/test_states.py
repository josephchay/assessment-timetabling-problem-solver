import tkinter
import timetablinggui


app = timetablinggui.TimetablingGUI()
app.geometry("400x900")
app.title("timetablinggui Test")


def change_state(widget):
    if widget.cget("state") == tkinter.NORMAL:
        widget.configure(state=tkinter.DISABLED)
    elif widget.cget("state") == tkinter.DISABLED:
        widget.configure(state=tkinter.NORMAL)


def widget_click():
    print("widget clicked")


button_1 = timetablinggui.GUIButton(master=app, text="button_1", command=widget_click)
button_1.pack(padx=20, pady=(20, 10))
button_2 = timetablinggui.GUIButton(master=app, text="Disable/Enable button_1", command=lambda: change_state(button_1))
button_2.pack(padx=20, pady=(10, 20))

switch_1 = timetablinggui.GUISwitch(master=app, text="switch_1", command=widget_click)
switch_1.pack(padx=20, pady=(20, 10))
button_2 = timetablinggui.GUIButton(master=app, text="Disable/Enable switch_1", command=lambda: change_state(switch_1))
button_2.pack(padx=20, pady=(10, 20))

entry_1 = timetablinggui.GUIEntry(master=app, placeholder_text="entry_1")
entry_1.pack(padx=20, pady=(20, 10))
button_3 = timetablinggui.GUIButton(master=app, text="Disable/Enable entry_1", command=lambda: change_state(entry_1))
button_3.pack(padx=20, pady=(10, 20))

checkbox_1 = timetablinggui.GUICheckBox(master=app, text="checkbox_1")
checkbox_1.pack(padx=20, pady=(20, 10))
button_4 = timetablinggui.GUIButton(master=app, text="Disable/Enable checkbox_1", command=lambda: change_state(checkbox_1))
button_4.pack(padx=20, pady=(10, 20))

radiobutton_1 = timetablinggui.GUIRadioButton(master=app, text="radiobutton_1")
radiobutton_1.pack(padx=20, pady=(20, 10))
button_5 = timetablinggui.GUIButton(master=app, text="Disable/Enable radiobutton_1", command=lambda: change_state(radiobutton_1))
button_5.pack(padx=20, pady=(10, 20))

optionmenu_1 = timetablinggui.GUIOptionMenu(app, values=["test 1", "test 2"])
optionmenu_1.pack(pady=10, padx=10)
button_6 = timetablinggui.GUIButton(master=app, text="Disable/Enable optionmenu_1", command=lambda: change_state(optionmenu_1))
button_6.pack(padx=20, pady=(10, 20))

combobox_1 = timetablinggui.GUIComboBox(app, values=["test 1", "test 2"])
combobox_1.pack(pady=10, padx=10)
button_7 = timetablinggui.GUIButton(master=app, text="Disable/Enable combobox_1", command=lambda: change_state(combobox_1))
button_7.pack(padx=20, pady=(10, 20))

slider_1 = timetablinggui.GUISlider(app)
slider_1.pack(pady=10, padx=10)
button_8 = timetablinggui.GUIButton(master=app, text="Disable/Enable slider_1", command=lambda: change_state(slider_1))
button_8.pack(padx=20, pady=(10, 20))


app.mainloop()
