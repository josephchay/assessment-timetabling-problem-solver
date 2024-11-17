import timetablinggui

app = timetablinggui.TimetablingGUI()
app.geometry("400x400+300+300")

toplevel = timetablinggui.GUIToplevel(app)
toplevel.geometry("350x240+800+300")

toplevel.iconify()
toplevel.after(2000, toplevel.deiconify)

app.mainloop()
