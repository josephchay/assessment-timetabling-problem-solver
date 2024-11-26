import hashlib
import os
from typing import Optional, Tuple
import json
from datetime import datetime


class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.login_history_file = "login_history.json"

        try:
            self._initialize_files()
        except Exception as e:
            print(f"Error initializing database files: {e}")

    def _initialize_files(self):
        """Ensure the required JSON files exist."""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                users = {
                    "student_johndoe": {
                        "password": self._hash_256("123"),
                        "type": "student",
                        "name": "John Doe",
                    },
                    "invigilator_franknewman": {
                        "password": self._hash_256("abc"),
                        "type": "invigilator",
                        "name": "Frank Newman",
                    }
                }
                json.dump(users, f)  # Start with some default users

        if not os.path.exists(self.login_history_file):
            with open(self.login_history_file, 'w') as f:
                json.dump([], f)  # Start with an empty list

    def _hash_256(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _load_users(self) -> dict:
        with open(self.users_file, 'r') as f:
            return json.load(f)

    def _save_users(self, users: dict):
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=4)

    def _log_login(self, username: str):
        try:
            with open(self.login_history_file, 'r') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

        history.append({
            "username": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        with open(self.login_history_file, 'w') as f:
            json.dump(history, f, indent=4)

    def add_user(self, username: str, password: str, user_type: str, name: str = None) -> bool:
        users = self._load_users()

        if username in users:
            return False

        users[username] = {
            "password": self._hash_256(password),
            "type": user_type,
            "name": name
        }

        self._save_users(users)
        return True

    def verify_user(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        users = self._load_users()

        if username not in users:
            return False, None

        user = users[username]
        if user["password"] == self._hash_256(password):
            self._log_login(username)
            return True, user["type"]

        return False, None

    def get_name(self, username: str) -> str:
        users = self._load_users()
        return users[username]["name"] if "name" in users[username] else username
