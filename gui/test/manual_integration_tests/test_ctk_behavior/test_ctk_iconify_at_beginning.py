import timetablinggui

app = timetablinggui.TimetablingGUI()
app.geometry("400x240")

app.iconify()
app.after(2000, app.deiconify)

app.mainloop()
