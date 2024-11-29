# This import statement brings in the GUIManager class from the user_interface module
# The GUIManager is responsible for creating and managing the graphical user interface
# It handles all window creation, component layout, and event handling for the application
# Without this import, we wouldn't have any visual interface for users to interact with
from user_interface import GUIManager

# This imports the initialize_login function from the authentication module
# This function handles all user authentication processes including:
# - Displaying the login window
# - Validating user credentials
# - Managing different user types (student vs invigilator)
# - Returning the authentication status and user role
from authentication import initialize_login


# This is the main entry point function for the application
# It orchestrates the high-level flow of the program
# All core application logic starts from this function
# It's kept separate from the global scope for better organization and encapsulation
def main():
    # Call the initialize_login function to start the authentication process
    # This will show a login dialog to the user and wait for them to log in
    # The function returns two values:
    # - login_success: boolean indicating if login was successful
    # - user_type: string indicating the type of user (student/invigilator)
    # These values are stored in variables for further processing
    login_success, user_type = initialize_login()

    # Check if the login was successful by evaluating the login_success boolean
    # This ensures that only authenticated users can access the main application
    # The if statement creates a branch in program flow based on authentication
    # This is a critical security check that prevents unauthorized access
    if login_success:
        # Output a success message to the console for logging purposes
        # This helps with debugging and monitoring application usage
        # The f-string formatting allows us to include the user_type dynamically
        # This provides immediate feedback about who is using the system
        print(f"Successfully logged in as: {user_type}")

        # Create a new instance of the GUIManager class
        # This initializes all the necessary GUI components
        # Sets up the main application window and all its child elements
        # Prepares the application's visual interface for user interaction
        app = GUIManager()

        # Start the main application loop
        # This begins the event processing for the GUI
        # Handles all user interactions with the interface
        # Keeps the application running until the user closes it
        app.run()
    else:
        # Output a failure message if login was unsuccessful
        # This provides feedback for failed login attempts
        # Helps with debugging authentication issues
        # Gives users immediate feedback about the failed login
        print("Login failed or cancelled")


# This is a standard Python idiom that checks if this file is being run directly
# It prevents code from being executed if the file is imported as a module
# This is a Python best practice for controlling code execution
# Helps maintain clean separation between import behavior and direct execution
if __name__ == "__main__":
    # Call the main function to start the application
    # This is the actual entry point of program execution
    # Everything starts from this line when the script is run
    # This keeps the global scope clean and follows Python best practices
    main()
