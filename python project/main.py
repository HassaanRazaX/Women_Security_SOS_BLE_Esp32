import json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
import os
from kivy.uix.screenmanager import Screen


# Function to load users from the JSON file
def load_users():
    try:
        with open("users.json", "r") as file:
            return json.load(file)  # Load JSON data into a dictionary
    except FileNotFoundError:
        return {}  # Return empty dictionary if file doesn't exist


# Function to save users to the JSON file
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)  # Save dictionary to JSON file




class LoginScreen(Screen):
    def login(self):
        email = self.ids.email.text.strip()  # Remove extra spaces
        password = self.ids.password.text.strip()
        error_label = self.ids.error_label  # Reference to the error label in the UI

        try:
            with open("users.json", "r") as file:
                users = json.load(file)  # Load users dictionary

            print("Loaded Users:", users)  # Debugging: Print users.json content
            print(f"User entered: {email} | Password: {password}")  # Debugging: Check entered values

            # Check if email exists and password matches
            if email in users and users[email] == password:
                print("Login Successful!")  # Debugging: Confirm login success
                self.manager.current = "home"  # Navigate to the home screen
                error_label.text = ""  # Clear any previous error message
            else:
                print("Login Failed!")  # Debugging: Confirm failed login attempt
                error_label.text = "Invalid email and password!"  # Show error message
        except FileNotFoundError:
            print("Error: users.json not found!")  # Debugging: File not found error
            self.show_error_popup("User database not found!")

    def show_error_popup(self, message):
        layout = BoxLayout(orientation='vertical', padding=10)
        label = Label(text=message)
        button = Button(text="OK", size_hint=(1, 0.3))

        popup = Popup(title="Login Error", content=layout, size_hint=(0.6, 0.3))
        button.bind(on_release=popup.dismiss)

        layout.add_widget(label)
        layout.add_widget(button)

        popup.open()



# Define the SignUp Screen
class SignUpScreen(Screen):

    def register_user(self):
        email = self.ids.email_input.text.strip()
        password = self.ids.password_input.text.strip()
        confirm_password = self.ids.confirm_password_input.text.strip()
        users_file = "users.json"

        # 1. Validate Empty Fields
        if not email or not password or not confirm_password:
            self.ids.message_label.text = "All fields are required!"
            return

        # 2. Check if Passwords Match
        if password != confirm_password:
            self.ids.message_label.text = "Passwords do not match!"
            return

        # 3. Load existing users from JSON file
        if os.path.exists(users_file):
            with open(users_file, "r") as file:
                try:
                    users = json.load(file)
                except json.JSONDecodeError:
                    users = {}
        else:
            users = {}

        # 4. Check if Email Already Exists
        if email in users:
            self.ids.message_label.text = "Email already exists!"
            return

        # 5. Store New User Data
        users[email] = {"password": password}  # Store credentials (consider hashing in a real app)
        with open(users_file, "w") as file:
            json.dump(users, file, indent=4)

        # 6. Show Success Message and Redirect to Login
        self.ids.message_label.text = "Signup successful! Redirecting..."
        self.clear_fields()
        self.manager.current = "login"

    def clear_fields(self):
        """ Clear input fields after sign up """
        self.ids.email_input.text = ""
        self.ids.password_input.text = ""
        self.ids.confirm_password_input.text = ""
        self.ids.message_label.text = ""

    def go_to_login(self):
        """ Navigate to the login screen """
        self.manager.current = "login"


# Define the Home Screen
class HomeScreen(Screen):
    pass


# App Class
class MyApp(App):
    def build(self):
        Builder.load_file("myapp.kv")  # Load the KV file
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SignUpScreen(name="signup"))
        return sm


# Run the App
if __name__ == "__main__":
    MyApp().run()