import timetablinggui


app = timetablinggui.TimetablingGUI()
app.geometry("600x950")

switch_1 = timetablinggui.GUISwitch(app, text="darkmode", command=lambda: timetablinggui.set_appearance_mode("dark" if switch_1.get() == 1 else "light"))
switch_1.pack(padx=20, pady=20)

seg_1 = timetablinggui.GUISegmentedButton(app, values=[])
seg_1.configure(values=["value 1", "Value 2", "Value 42", "Value 123", "longlonglong"])
seg_1.pack(padx=20, pady=20)

frame_1 = timetablinggui.GUIFrame(app, height=100)
frame_1.pack(padx=20, pady=20, fill="x")

seg_2_var = timetablinggui.StringVar(value="value 1")

seg_2 = timetablinggui.GUISegmentedButton(frame_1, values=["value 1", "Value 2", "Value 42"], variable=seg_2_var)
seg_2.configure(values=[])
seg_2.configure(values=["value 1", "Value 2", "Value 42"])
seg_2.pack(padx=20, pady=10)
seg_2.insert(0, "insert at 0")
seg_2.insert(1, "insert at 1")

label_seg_2 = timetablinggui.GUILabel(frame_1, textvariable=seg_2_var)
label_seg_2.pack(padx=20, pady=10)

frame_1_1 = timetablinggui.GUIFrame(frame_1, height=100)
frame_1_1.pack(padx=20, pady=10, fill="x")

switch_2 = timetablinggui.GUISwitch(frame_1_1, text="change fg", command=lambda: frame_1_1.configure(fg_color="red" if switch_2.get() == 1 else "green"))
switch_2.pack(padx=20, pady=20)

seg_3 = timetablinggui.GUISegmentedButton(frame_1_1, values=["value 1", "Value 2", "Value 42"])
seg_3.pack(padx=20, pady=10)

seg_4 = timetablinggui.GUISegmentedButton(app)
seg_4.pack(padx=20, pady=20)

seg_5_var = timetablinggui.StringVar(value="kfasjkfdklaj")
seg_5 = timetablinggui.GUISegmentedButton(app, corner_radius=1000, border_width=0, unselected_color="green",
                                          variable=seg_5_var)
seg_5.pack(padx=20, pady=20)
seg_5.configure(values=["1", "2", "3", "4"])
seg_5.insert(0, "insert begin")
seg_5.insert(len(seg_5.cget("values")), "insert 1")
seg_5.insert(len(seg_5.cget("values")), "insert 2")
seg_5.insert(len(seg_5.cget("values")), "insert 3")
seg_5.configure(fg_color="green")

seg_5.set("insert 2")
seg_5.delete("insert 2")

label_seg_5 = timetablinggui.GUILabel(app, textvariable=seg_5_var)
label_seg_5.pack(padx=20, pady=20)

seg_6_var = timetablinggui.StringVar(value="kfasjkfdklaj")
seg_6 = timetablinggui.GUISegmentedButton(app, width=300)
seg_6.pack(padx=20, pady=20)
entry_6 = timetablinggui.GUIEntry(app)
entry_6.pack(padx=20, pady=(0, 20))
button_6 = timetablinggui.GUIButton(app, text="set", command=lambda: seg_6.set(entry_6.get()))
button_6.pack(padx=20, pady=(0, 20))
button_6 = timetablinggui.GUIButton(app, text="insert value", command=lambda: seg_6.insert(0, entry_6.get()))
button_6.pack(padx=20, pady=(0, 20))
label_6 = timetablinggui.GUILabel(app, textvariable=seg_6_var)
label_6.pack(padx=20, pady=(0, 20))

seg_6.configure(height=50, variable=seg_6_var)
seg_6.delete("GUISegmentedButton")

seg_7 = timetablinggui.GUISegmentedButton(app, values=["disabled seg button", "2", "3"])
seg_7.pack(padx=20, pady=20)
seg_7.configure(state="disabled")
seg_7.set("2")

seg_7.configure(height=40, width=400,
                dynamic_resizing=False, font=("Times", -20))

app.mainloop()
