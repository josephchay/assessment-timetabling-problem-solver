import timetablinggui


app = timetablinggui.TimetablingGUI()
app.geometry("1200x1000")
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure((0, 1), weight=1)

frame_1 = timetablinggui.GUIFrame(app)
frame_1.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
frame_2 = timetablinggui.GUIFrame(app)
frame_2.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

def set_scaling(scaling):
    timetablinggui.set_widget_scaling(scaling)

scaling_button = timetablinggui.GUISegmentedButton(frame_1, values=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 2.0], command=set_scaling)
scaling_button.pack(pady=(2, 10))

b = timetablinggui.GUIButton(frame_1, text="single name", font=("Times",))
b.pack(pady=2)
b = timetablinggui.GUIButton(frame_1, text="name with size", font=("Times", 18))
b.pack(pady=2)
b = timetablinggui.GUIButton(frame_1, text="name with negative size", font=("Times", -18))
b.pack(pady=2)
b = timetablinggui.GUIButton(frame_1, text="extra keywords", font=("Times", -18, "bold italic underline overstrike"))
b.pack(pady=2)

b = timetablinggui.GUIButton(frame_1, text="object default")
b.pack(pady=(10, 2))
b = timetablinggui.GUIButton(frame_1, text="object single name", font=timetablinggui.GUIFont("Times"))
b.pack(pady=2)
b = timetablinggui.GUIButton(frame_1, text="object with name and size", font=timetablinggui.GUIFont("Times", 18))
b.pack(pady=2)
b = timetablinggui.GUIButton(frame_1, text="object with name and negative size", font=timetablinggui.GUIFont("Times", -18))
b.pack(pady=2)
b = timetablinggui.GUIButton(frame_1, text="object with extra keywords",
                             font=timetablinggui.GUIFont("Times", -18, weight="bold", slant="italic", underline=True, overstrike=True))
b.pack(pady=2)

b1 = timetablinggui.GUIButton(frame_1, text="object default modified")
b1.pack(pady=(10, 2))
b1.cget("font").configure(size=9)
print("test_font.py:", b1.cget("font").cget("size"), b1.cget("font").cget("family"))

b2 = timetablinggui.GUIButton(frame_1, text="object default overridden")
b2.pack(pady=10)
b2.configure(font=timetablinggui.GUIFont(family="Times"))

label_font = timetablinggui.GUIFont(size=5)
for i in range(30):
    l = timetablinggui.GUILabel(frame_2, font=label_font, height=0)
    l.grid(row=i, column=0, pady=1)
    b = timetablinggui.GUIButton(frame_2, font=label_font, height=5)
    b.grid(row=i, column=1, pady=1)
    c = timetablinggui.GUICheckBox(frame_2, font=label_font)
    c.grid(row=i, column=2, pady=1)
    c = timetablinggui.GUIComboBox(frame_2, font=label_font, dropdown_font=label_font, height=15)
    c.grid(row=i, column=3, pady=1)
    e = timetablinggui.GUIEntry(frame_2, font=label_font, height=15, placeholder_text="testtest")
    e.grid(row=i, column=4, pady=1)
    o = timetablinggui.GUIOptionMenu(frame_2, font=label_font, height=15, width=50)
    o.grid(row=i, column=5, pady=1)
    r = timetablinggui.GUIRadioButton(frame_2, font=label_font, height=15, width=50)
    r.grid(row=i, column=6, pady=1)
    s = timetablinggui.GUISwitch(frame_2, font=label_font, height=15, width=50)
    s.grid(row=i, column=7, pady=1)
frame_2.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

def change_font():
    import time
    t1 = time.perf_counter()
    label_font.configure(size=10, overstrike=True)
    t2 = time.perf_counter()
    print("change_font:", (t2-t1)*1000, "ms")

app.after(3000, change_font)
app.after(6000, lambda: label_font.configure(size=8, overstrike=False))
app.mainloop()
