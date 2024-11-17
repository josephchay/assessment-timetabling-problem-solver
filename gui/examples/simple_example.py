import timetablinggui
import tkinterDnD

timetablinggui.set_gui_parent_class(tkinterDnD.Tk)

timetablinggui.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
timetablinggui.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

app = timetablinggui.TimetablingGUI()
app.geometry("400x780")
app.title("timetablinggui simple_example.py")

print(type(app), isinstance(app, tkinterDnD.Tk))

def button_callback():
    print("Button click", combobox_1.get())


def slider_callback(value):
    progressbar_1.set(value)


frame_1 = timetablinggui.GUIFrame(master=app)
frame_1.pack(pady=20, padx=60, fill="both", expand=True)

label_1 = timetablinggui.GUILabel(master=frame_1, justify=timetablinggui.LEFT)
label_1.pack(pady=10, padx=10)

progressbar_1 = timetablinggui.GUIProgressBar(master=frame_1)
progressbar_1.pack(pady=10, padx=10)

button_1 = timetablinggui.GUIButton(master=frame_1, command=button_callback)
button_1.pack(pady=10, padx=10)

slider_1 = timetablinggui.GUISlider(master=frame_1, command=slider_callback, from_=0, to=1)
slider_1.pack(pady=10, padx=10)
slider_1.set(0.5)

entry_1 = timetablinggui.GUIEntry(master=frame_1, placeholder_text="GUIEntry")
entry_1.pack(pady=10, padx=10)

optionmenu_1 = timetablinggui.GUIOptionMenu(frame_1, values=["Option 1", "Option 2", "Option 42 long long long..."])
optionmenu_1.pack(pady=10, padx=10)
optionmenu_1.set("GUIOptionMenu")

combobox_1 = timetablinggui.GUIComboBox(frame_1, values=["Option 1", "Option 2", "Option 42 long long long..."])
combobox_1.pack(pady=10, padx=10)
combobox_1.set("GUIComboBox")

checkbox_1 = timetablinggui.GUICheckBox(master=frame_1)
checkbox_1.pack(pady=10, padx=10)

radiobutton_var = timetablinggui.IntVar(value=1)

radiobutton_1 = timetablinggui.GUIRadioButton(master=frame_1, variable=radiobutton_var, value=1)
radiobutton_1.pack(pady=10, padx=10)

radiobutton_2 = timetablinggui.GUIRadioButton(master=frame_1, variable=radiobutton_var, value=2)
radiobutton_2.pack(pady=10, padx=10)

switch_1 = timetablinggui.GUISwitch(master=frame_1)
switch_1.pack(pady=10, padx=10)

text_1 = timetablinggui.GUITextbox(master=frame_1, width=200, height=70)
text_1.pack(pady=10, padx=10)
text_1.insert("0.0", "GUITextbox\n\n\n\n")

segmented_button_1 = timetablinggui.GUISegmentedButton(master=frame_1, values=["GUISegmentedButton", "Value 2"])
segmented_button_1.pack(pady=10, padx=10)

tabview_1 = timetablinggui.GUITabview(master=frame_1, width=300)
tabview_1.pack(pady=10, padx=10)
tabview_1.add("GUITabview")
tabview_1.add("Tab 2")

app.mainloop()
