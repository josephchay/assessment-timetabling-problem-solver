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
            font=("Arial", 24, "bold")
        )
        self.title.pack()

        self.subtitle = timetablinggui.GUILabel(
            label_frame,
            text="Enter student details below",
            font=("Arial", 14)
        )
        self.subtitle.pack()

        # Full Name
        self.name_label = timetablinggui.GUILabel(
            self,
            text="Student Full Name",
            font=("Arial", 12)
        )
        self.name_label.pack(pady=(20, 0), padx=30, anchor="w")

        self.name_entry = timetablinggui.GUIEntry(
            self,
            placeholder_text="Enter student's full name",
            width=300
        )
        self.name_entry.pack(pady=(5, 10), padx=30)

        # Generated Username Display
        self.username_label = timetablinggui.GUILabel(
            self,
            text="Generated Username",
            font=("Arial", 12)
        )
        self.username_label.pack(pady=(10, 0), padx=30, anchor="w")

        self.username_display = timetablinggui.GUILabel(
            self,
            text="Username will be generated",
            font=("Arial", 12),
            text_color="gray"
        )
        self.username_display.pack(pady=(5, 10), padx=30)

        # Password
        self.password_label = timetablinggui.GUILabel(
            self,
            text="Password",
            font=("Arial", 12)
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

        # Bind the name entry to update username preview
        self.name_entry.bind('<KeyRelease>', self._update_username_preview)

    def _generate_username(self, full_name: str) -> str:
        # Remove spaces and convert to lowercase
        username = "student_" + "".join(full_name.lower().split())
        return username

    def _update_username_preview(self, event=None):
        full_name = self.name_entry.get().strip()
        if full_name:
            username = self._generate_username(full_name)
            self.username_display.configure(
                text=username,
                text_color="black"
            )
        else:
            self.username_display.configure(
                text="Username will be generated",
                text_color="gray"
            )

    def _handle_register(self):
        full_name = self.name_entry.get().strip()
        password = self.password_entry.get().strip()

        if not full_name or not password:
            self.show_error("Please fill in all fields")
            return

        username = self._generate_username(full_name)
        # Pass name, username, and password to callback
        self.register_callback(username, password, full_name)

    def show_error(self, message, is_success=False):
        self.error_label.configure(
            text=message,
            text_color="green" if is_success else "red"
        )

    def clear_fields(self):
        self.name_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.username_display.configure(
            text="Username will be generated",
            text_color="gray"
        )
        self.error_label.configure(text="")
