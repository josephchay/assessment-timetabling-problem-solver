import timetablinggui

timetablinggui.set_appearance_mode("dark")

app = timetablinggui.TimetablingGUI()
app.geometry("400x400+300+300")

toplevel = timetablinggui.GUIToplevel(app)
toplevel.geometry("350x240+800+300")


def change_appearance_mode():
    # test zoom with withdraw
    app.after(1000, lambda: toplevel.state("zoomed"))
    app.after(2000, toplevel.withdraw)
    app.after(3000, toplevel.deiconify)
    app.after(4000, lambda: toplevel.state("normal"))

    # test zoom with iconify
    app.after(5000, lambda: toplevel.state("zoomed"))
    app.after(6000, toplevel.iconify)
    app.after(7000, toplevel.deiconify)
    app.after(8000, lambda: toplevel.state("normal"))


button_1 = timetablinggui.GUIButton(app, text="start test", command=change_appearance_mode)
button_1.pack(pady=20, padx=20)

app.mainloop()
