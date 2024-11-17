import tkinter
import tkinter.ttk as ttk
import timetablinggui

app = timetablinggui.TimetablingGUI()
app.title('Test OptionMenu ComboBox.py')
app.geometry('400x500')


def select_callback(choice):
    choice = variable.get()
    print("display_selected", choice)


countries = ['Bahamas', 'Canada', 'Cuba', 'United States', "long sdhfhjgdshjafghdgshfhjdsfj"]

variable = tkinter.StringVar()
variable.set("test")

optionmenu_tk = tkinter.OptionMenu(app, variable, *countries, command=select_callback)
optionmenu_tk.pack(pady=10, padx=10)

optionmenu_1 = timetablinggui.GUIOptionMenu(app, variable=variable, values=countries, command=select_callback)
optionmenu_1.pack(pady=20, padx=10)

optionmenu_2 = timetablinggui.GUIOptionMenu(app, variable=variable, values=countries, command=select_callback,
                                            dynamic_resizing=False)
optionmenu_2.pack(pady=20, padx=10)

combobox_tk = ttk.Combobox(app, values=countries, textvariable=variable)
combobox_tk.pack(pady=10, padx=10)

combobox_1 = timetablinggui.GUIComboBox(app, variable=variable, values=countries, command=select_callback, width=300)
combobox_1.pack(pady=20, padx=10)

def set_new_scaling(scaling):
    timetablinggui.set_window_scaling(scaling)
    timetablinggui.set_widget_scaling(scaling)

scaling_slider = timetablinggui.GUISlider(app, command=set_new_scaling, from_=0, to=2)
scaling_slider.pack(pady=20, padx=10)

app.mainloop()
