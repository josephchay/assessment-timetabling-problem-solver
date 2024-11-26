from typing import Optional, Tuple

from gui import timetablinggui
from .database import Database
from .invigilator_access import InvigilatorOptionsFrame
from .registration import RegistrationFrame


class LoginFrame(timetablinggui.GUIFrame):
    def __init__(self, parent, login_callback):
        super().__init__(parent)
        self.login_callback = login_callback
        self._create_widgets()

    def _create_widgets(self):
        # Title
        label_frame = timetablinggui.GUIFrame(self)
        label_frame.pack(pady=20)

        self.login_title = timetablinggui.GUILabel(
            label_frame,
            text="Assessment Scheduler",
            font=("Arial", 24, "bold")  # Using standard font
        )
        self.login_title.pack()

        self.login_subtitle = timetablinggui.GUILabel(
            label_frame,
            text="Login to continue",
            font=("Arial", 14)  # Using standard font
        )
        self.login_subtitle.pack()

        # Username
        self.username_label = timetablinggui.GUILabel(
            self,
            text="Username",
            font=("Arial", 12)  # Using standard font
        )
        self.username_label.pack(pady=(20, 0), padx=30, anchor="w")

        self.username_entry = timetablinggui.GUIEntry(
            self,
            placeholder_text="Enter your username",
            width=300
        )
        self.username_entry.pack(pady=(5, 10), padx=30)

        # Password
        self.password_label = timetablinggui.GUILabel(
            self,
            text="Password",
            font=("Arial", 12)  # Using standard font
        )
        self.password_label.pack(pady=(10, 0), padx=30, anchor="w")

        self.password_entry = timetablinggui.GUIEntry(
            self,
            placeholder_text="Enter your password",
            show="•",
            width=300
        )
        self.password_entry.pack(pady=(5, 20), padx=30)

        # Login button
        self.login_button = timetablinggui.GUIButton(
            self,
            text="Login",
            command=self._handle_login,
            width=300
        )
        self.login_button.pack(pady=10, padx=30)

        # Error label
        self.error_label = timetablinggui.GUILabel(
            self,
            text="",
            text_color="red",
            wraplength=300
        )
        self.error_label.pack(pady=10)

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        self.login_callback(username, password)

    def clear_fields(self):
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.error_label.configure(text="")

    def show_error(self, message):
        self.error_label.configure(text=message)


class LoginWindow(timetablinggui.GUIToplevel):
    def __init__(self):
        try:
            super().__init__()
        except Exception as e:
            print(f"Warning: Could not initialize window with custom settings: {e}")

        self.db = Database()
        self.success = False
        self.user_type = None
        self.user = None
        self.user_name = None

        # Basic window setup
        self.title("Exam Scheduler Login")
        self.geometry("400x500")

        try:
            self.configure(fg_color=("gray95", "gray10"))
        except Exception as e:
            print(f"Warning: Could not set window color: {e}")

        # Main container
        self.container = timetablinggui.GUIFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Create frames
        self.login_frame = LoginFrame(self.container, self.handle_login)
        self.registration_frame = RegistrationFrame(self.container, self.handle_register)
        self.invigilator_options_frame = InvigilatorOptionsFrame(
            self.container,
            self.show_register_frame,
            self.proceed_to_main,
            self.logout
        )

        # Show login frame initially
        self.show_login_frame()
        self.center_window()

    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def show_login_frame(self):
        self.registration_frame.pack_forget()
        self.invigilator_options_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_register_frame(self):
        self.login_frame.pack_forget()
        self.invigilator_options_frame.pack_forget()
        self.registration_frame.pack(fill="both", expand=True)

    def show_invigilator_options(self):
        self.login_frame.pack_forget()
        self.registration_frame.pack_forget()
        self.invigilator_options_frame.update_welcome_message(self.user_name)
        self.invigilator_options_frame.pack(fill="both", expand=True)

    def handle_login(self, username: str, password: str):
        if not username or not password:
            self.login_frame.show_error("Please fill in all fields")
            return

        success, user_type = self.db.verify_user(username, password)

        if success:
            self.success = True
            self.user_type = user_type
            self.user = username
            self.user_name = self.db.get_name(username)

            if user_type == "student":
                # Students proceed directly to main application
                self.destroy()
            else:
                # Invigilators see options
                self.show_invigilator_options()
        else:
            self.login_frame.show_error("Invalid username or password")

    def handle_register(self, username: str, password: str, full_name: str):
        if not username or not password or not full_name:
            self.registration_frame.show_error("Please fill in all fields")
            return

        if len(password) < 6:
            self.registration_frame.show_error("Password must be at least 6 characters")
            return

        if len(full_name) < 3:
            self.registration_frame.show_error("Name must be at least 3 characters")
            return

        # Only allow letters and spaces in full name
        if not all(c.isalpha() or c.isspace() for c in full_name):
            self.registration_frame.show_error("Name can only contain letters and spaces")
            return

        if self.db.add_user(username, password, "student", full_name):
            self.registration_frame.show_error("Student registration successful!", True)
            self.after(1500, self.show_invigilator_options)
        else:
            self.registration_frame.show_error("Username already exists")

    def proceed_to_main(self):
        self.success = True
        self.destroy()

    def logout(self):
        self.user = None
        self.user_type = None
        self.success = False
        self.login_frame.clear_fields()
        self.show_login_frame()


def initialize_login() -> Tuple[bool, Optional[str]]:
    """Initialize the login system and return login status and user type"""
    login_window = LoginWindow()
    login_window.wait_window()
    return login_window.success, login_window.user_type
