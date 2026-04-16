"""process_data.py — A simple CLI app for managing timestamped text items."""

import hashlib
import os
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_FILE = Path("data.txt")
MAX_ITEMS = 1000
MAX_VALUE_LENGTH = 256
MAX_LOGIN_ATTEMPTS = 3

# Passwords stored as SHA-256 hashes. In production, use bcrypt or argon2.
CREDENTIALS: dict[str, str] = {
    "admin": hashlib.sha256(b"12345").hexdigest()
}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AuthService:
    """Handles user authentication with hashed password comparison."""

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify(self, username: str, password: str) -> bool:
        """Return True if the username/password pair is valid."""
        expected = CREDENTIALS.get(username)
        if expected is None:
            return False
        return hashlib.compare_digest(self._hash(password), expected)

    def login(self) -> bool:
        """Prompt for credentials up to MAX_LOGIN_ATTEMPTS times."""
        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            if self.verify(username, password):
                print(f"Welcome, {username}!")
                return True
            remaining = MAX_LOGIN_ATTEMPTS - attempt
            msg = f"{remaining} attempt(s) remaining." if remaining else "Exiting."
            print(f"Invalid credentials. {msg}")
        return False


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

class ItemStore:
    """Manages an in-memory list of items and saves them to a file."""

    def __init__(self) -> None:
        self._items: list[str] = []

    def add(self, value: str) -> None:
        """Validate and add a new timestamped item."""
        value = value.strip()
        if not value:
            print("Error: value cannot be empty.")
            return
        if len(value) > MAX_VALUE_LENGTH:
            print(f"Error: value exceeds {MAX_VALUE_LENGTH} characters.")
            return
        if len(self._items) >= MAX_ITEMS:
            print(f"Error: maximum of {MAX_ITEMS} items reached.")
            return
        timestamp = datetime.now().isoformat(timespec="seconds")
        entry = f"[{len(self._items) + 1}] [{timestamp}] {value}"
        self._items.append(entry)
        print(f"Added: {entry}")

    def show(self) -> None:
        """Print all stored items."""
        if not self._items:
            print("No items stored yet.")
            return
        for item in self._items:
            print(f"  {item}")

    def save(self) -> None:
        """Write all items to DATA_FILE using an atomic write."""
        if not self._items:
            print("Nothing to save.")
            return
        tmp = DATA_FILE.with_suffix(".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as fh:
                fh.write("\n".join(self._items) + "\n")
            tmp.replace(DATA_FILE)
            print(f"Saved {len(self._items)} item(s) to '{DATA_FILE}'.")
        except OSError as exc:
            print(f"Error saving: {exc}")
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class CLI:
    """Runs the interactive command loop."""

    COMMANDS = ("add", "show", "save", "help", "exit")

    def __init__(self) -> None:
        self._auth = AuthService()
        self._store = ItemStore()

    def _help(self) -> None:
        print("Commands: " + ", ".join(self.COMMANDS))

    def run(self) -> None:
        """Authenticate the user then start the command loop."""
        if not self._auth.login():
            os._exit(1)

        self._help()
        while True:
            try:
                cmd = input("\nCommand: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if cmd == "add":
                self._store.add(input("Value: "))
            elif cmd == "show":
                self._store.show()
            elif cmd == "save":
                self._store.save()
            elif cmd == "help":
                self._help()
            elif cmd == "exit":
                if input("Save before exiting? (y/n): ").strip().lower() == "y":
                    self._store.save()
                print("Goodbye!")
                break
            else:
                print(f"Unknown command '{cmd}'. Type 'help' for available commands.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    CLI().run()
