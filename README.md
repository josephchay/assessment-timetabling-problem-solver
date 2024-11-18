# Assessment Timetabling Problem Solver

##### Official Implementation for Symbolic Artificial Intelligence Coursework 1

---

## About

This repository contains the official implementation of the paper _Assessment Timetabling Problem Solver_ by Joseph Chay.

### Development

#### Installation

To install the dependencies, run the following commands:

```bash
pip install -r requirements.txt
```

Install the dependencies for our personally developed custom GUI specifically designed
for this Assessment Timetabling Problem Solver assignment:

```bash
cd gui
```

```bash
pip install -e .
```

After installing the dependencies, you can utilize the simple example code below as a test of our
self-developed customizable GUI interface:

```python
from gui import timetablinggui

timetablinggui.set_appearance_mode("System")  # Modes: can be system (default), light, dark
timetablinggui.set_default_color_theme("blue")  # Themes: can be blue (default), dark-blue, green, yellow, orange.

app = timetablinggui.GUI()  # create the GUI window
app.geometry("800x600")

def button_function():
    """
    Function to be executed when the button is clicked
    """

    print("button clicked!")

# Create a Usable Customizable Functioning Button
button = timetablinggui.GUIButton(master=app, text="GUIButton", command=button_function)
button.place(relx=0.5, rely=0.5, anchor=timetablinggui.CENTER)

app.mainloop()
```

Exit the directory to the root of the repository

```bash
cd ..
```

Execute the following command to run the entire well-structured and developed Timetabling Problem System
completely tailored to the end user of all levels of expertise,
including developers, debuggers, and normal daily end-users:

```bash
python main.py
```
