import timetablinggui

timetablinggui.set_default_color_theme("blue")
timetablinggui.set_appearance_mode("dark")

app = timetablinggui.TimetablingGUI()
app.geometry("600x1000")

app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)
app.grid_columnconfigure(2, weight=1)
app.grid_columnconfigure(3, weight=1)

f1 = timetablinggui.GUIFrame(app, fg_color="gray10", corner_radius=0)
f1.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew")
f1.grid_columnconfigure(0, weight=1)

f2 = timetablinggui.GUIFrame(app, fg_color="gray10", corner_radius=0)
f2.grid(row=0, column=1, rowspan=1, columnspan=1, sticky="nsew")
f2.grid_columnconfigure(0, weight=1)

f3 = timetablinggui.GUIFrame(app, fg_color="gray85", corner_radius=0)
f3.grid(row=0, column=2, rowspan=1, columnspan=1, sticky="nsew")
f3.grid_columnconfigure(0, weight=1)

f4 = timetablinggui.GUIFrame(app, fg_color="gray90", corner_radius=0)
f4.grid(row=0, column=3, rowspan=1, columnspan=1, sticky="nsew")
f4.grid_columnconfigure(0, weight=1)

for i in range(0, 16, 1):
    b = timetablinggui.GUIButton(f1, corner_radius=i, height=30, border_width=1, text=f"{i} {i - 1}",
                                 border_color="white", fg_color=None, text_color="white")
    # b = tkinter.Button(f1,  text=f"{i} {i-2}", width=20)
    b.grid(row=i, column=0, pady=5, padx=15, sticky="nsew")

    b = timetablinggui.GUIButton(f2, corner_radius=i, height=30, border_width=0, text=f"{i}",
                                 fg_color="#228da8")
    b.grid(row=i, column=0, pady=5, padx=15, sticky="nsew")

    b = timetablinggui.GUIButton(f3, corner_radius=i, height=30, border_width=1, text=f"{i} {i - 1}",
                                 fg_color=None, border_color="gray20", text_color="black")
    b.grid(row=i, column=0, pady=5, padx=15, sticky="nsew")

    b = timetablinggui.GUIButton(f4, corner_radius=i, height=30, border_width=0, text=f"{i}",
                                 border_color="gray10", fg_color="#228da8")
    b.grid(row=i, column=0, pady=5, padx=15, sticky="nsew")

app.mainloop()
