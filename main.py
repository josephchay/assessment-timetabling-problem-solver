from user_interface import GUIManager
from authentication import initialize_login


def main():
    # Initialize login
    login_success, user_type = initialize_login()

    if login_success:
        print(f"Successfully logged in as: {user_type}")
        app = GUIManager()
        app.run()
    else:
        print("Login failed or cancelled")


if __name__ == "__main__":
    main()
