from gui import timetablinggui


class InvigilatorOptionsFrame(timetablinggui.GUIFrame):
    def __init__(self, parent, create_student_callback, continue_callback, logout_callback):
        super().__init__(parent)
        self.create_student_callback = create_student_callback
        self.continue_callback = continue_callback
        self.logout_callback = logout_callback
        self._create_widgets()

    def _create_widgets(self):
        # Title
        label_frame = timetablinggui.GUIFrame(self)
        label_frame.pack(pady=20)

        self.title = timetablinggui.GUILabel(
            label_frame,
            text="Welcome, Invigilator",
            font=("Arial", 24, "bold")  # Using standard font
        )
        self.title.pack()

        self.subtitle = timetablinggui.GUILabel(
            label_frame,
            text="Please select an option",
            font=("Arial", 14)  # Using standard font
        )
        self.subtitle.pack()

        # Create Student Account button
        self.create_student_button = timetablinggui.GUIButton(
            self,
            text="Create Student Account",
            command=self.create_student_callback,
            width=300
        )
        self.create_student_button.pack(pady=20, padx=30)

        # Continue to Main Application button
        self.continue_button = timetablinggui.GUIButton(
            self,
            text="Continue to Main Application",
            command=self.continue_callback,
            width=300
        )
        self.continue_button.pack(pady=10, padx=30)

        # Logout button
        self.logout_button = timetablinggui.GUIButton(
            self,
            text="Logout",
            command=self.logout_callback,
            width=300,
            fg_color="transparent",
            border_width=2
        )
        self.logout_button.pack(pady=20, padx=30)

    def update_welcome_message(self, name):
        self.title.configure(text=f"Welcome, {name}")

