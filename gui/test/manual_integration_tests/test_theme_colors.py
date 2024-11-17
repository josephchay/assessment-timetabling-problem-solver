import tkinter
import timetablinggui

timetablinggui.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
timetablinggui.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

app = timetablinggui.TimetablingGUI()
app.geometry("1100x900")
app.title("timetablinggui simple_example.py")


def create_all_widgets(master, state="normal"):
    label_1 = timetablinggui.GUILabel(master=master, justify=tkinter.LEFT)
    label_1.pack(pady=10, padx=10)

    progressbar_1 = timetablinggui.GUIProgressBar(master=master)
    progressbar_1.pack(pady=10, padx=10)

    button_1 = timetablinggui.GUIButton(master=master, state=state, border_width=0)
    button_1.pack(pady=10, padx=10)

    slider_1 = timetablinggui.GUISlider(master=master, from_=0, to=1, state=state)
    slider_1.pack(pady=10, padx=10)
    slider_1.set(0.5)

    entry_1 = timetablinggui.GUIEntry(master=master, placeholder_text="GUIEntry", state=state)
    entry_1.pack(pady=10, padx=10)

    optionmenu_1 = timetablinggui.GUIOptionMenu(master, values=["Option 1", "Option 2", "Option 42 long long long..."], state=state)
    optionmenu_1.pack(pady=10, padx=10)
    optionmenu_1.set("GUIOptionMenu")

    combobox_1 = timetablinggui.GUIComboBox(master, values=["Option 1", "Option 2", "Option 42 long long long..."], state=state)
    combobox_1.pack(pady=10, padx=10)
    optionmenu_1.set("GUIComboBox")

    checkbox_1 = timetablinggui.GUICheckBox(master=master, state=state)
    checkbox_1.pack(pady=10, padx=10)

    radiobutton_var = tkinter.IntVar(value=1)

    radiobutton_1 = timetablinggui.GUIRadioButton(master=master, variable=radiobutton_var, value=1, state=state)
    radiobutton_1.pack(pady=10, padx=10)

    radiobutton_2 = timetablinggui.GUIRadioButton(master=master, variable=radiobutton_var, value=2, state=state)
    radiobutton_2.pack(pady=10, padx=10)

    switch_1 = timetablinggui.GUISwitch(master=master, state=state)
    switch_1.pack(pady=10, padx=10)

    text_1 = timetablinggui.GUITextbox(master=master, width=200, height=70, state=state)
    text_1.pack(pady=10, padx=10)
    text_1.insert("0.0", "GUITextbox\n\n\n\n")

    segmented_button_1 = timetablinggui.GUISegmentedButton(master=master, values=["GUISegmentedButton", "Value 2"], state=state)
    segmented_button_1.pack(pady=10, padx=10)

    tabview_1 = timetablinggui.GUITabview(master=master, width=200, height=100, state=state, border_width=2)
    tabview_1.pack(pady=10, padx=10)
    tabview_1.add("GUITabview")
    tabview_1.add("Tab 2")


frame_0 = timetablinggui.GUIFrame(master=app, fg_color="transparent")
frame_0.grid(row=0, column=0, padx=10, pady=10)
create_all_widgets(frame_0, state="disabled")

frame_1 = timetablinggui.GUIFrame(master=app, fg_color="transparent")
frame_1.grid(row=0, column=1, padx=10, pady=10)
create_all_widgets(frame_1)

frame_2 = timetablinggui.GUIFrame(master=app)
frame_2.grid(row=0, column=2, padx=10, pady=10)
create_all_widgets(frame_2)

frame_3 = timetablinggui.GUIFrame(master=app)
frame_3.grid(row=0, column=3, padx=10, pady=10)
frame_4 = timetablinggui.GUIFrame(master=frame_3)
frame_4.grid(row=0, column=0, padx=25, pady=25)
create_all_widgets(frame_4)

appearance_mode_button = timetablinggui.GUISegmentedButton(app, values=["light", "dark"], command=lambda v: timetablinggui.set_appearance_mode(v))
appearance_mode_button.grid(row=1, column=0, columnspan=3, padx=25, pady=25)

app.mainloop()
