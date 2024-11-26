from gui import timetablinggui


class RegistrationFrame(timetablinggui.GUIFrame):
    def __init__(self, parent, register_callback):
        super().__init__(parent)
        self.register_callback = register_callback
        self._create_widgets()

    def _create_widgets(self):
        # Title
        label_frame = timetablinggui.GUIFrame(self)
        label_frame.pack(pady=20)

        self.title = timetablinggui.GUILabel(
            label_frame,
            text="Create Student Account",
            font=("Arial", 24, "bold")  # Using standard font
        )
        self.title.pack()

        self.subtitle = timetablinggui.GUILabel(
            label_frame,
            text="Enter student details below",
            font=("Arial", 14)  # Using standard font
        )
        self.subtitle.pack()

        # Username
        self.username_label = timetablinggui.GUILabel(
            self,
            text="Student Username",
            font=("Arial", 12)  # Using standard font
        )
        self.username_label.pack(pady=(20, 0), padx=30, anchor="w")

        self.user_name_entry = timetablinggui.GUIEntry(
            self,
            placeholder_text="Enter student name",
            width=300
        )
        self.user_name_entry.pack(pady=(5, 10), padx=30)

        # Password
        self.password_label = timetablinggui.GUILabel(
            self,
            text="Password",
            font=("Arial", 12)  # Using standard font
        )
        self.password_label.pack(pady=(10, 0), padx=30, anchor="w")

        self.password_entry = timetablinggui.GUIEntry(
            self,
            placeholder_text="Enter password for student",
            show="•",
            width=300
        )
        self.password_entry.pack(pady=(5, 20), padx=30)

        # Register button
        self.register_button = timetablinggui.GUIButton(
            self,
            text="Register Student",
            command=self._handle_register,
            width=300
        )
        self.register_button.pack(pady=20, padx=30)

        # Error label
        self.error_label = timetablinggui.GUILabel(
            self,
            text="",
            text_color="red",
            wraplength=300
        )
        self.error_label.pack(pady=10)

    def _handle_register(self):
        name = self.user_name_entry.get().strip()
        password = self.password_entry.get().strip()
        self.register_callback(name, password)

    def show_error(self, message, is_success=False):
        self.error_label.configure(
            text=message,
            text_color="green" if is_success else "red"
        )

    def clear_fields(self):
        self.user_name_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.error_label.configure(text="")
