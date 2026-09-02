"""
Базове завдання: база даних користувачів і система логування (модуль sqlite3).

Запуск:
    python users_app.py          — інтерактивне меню
    python users_app.py --demo   — автоматична перевірка на тестових користувачах
"""

import os
import re
import sqlite3
import sys
from contextlib import contextmanager

DB_NAME = "users.db"

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@contextmanager
def get_connection():
    """З'єднання з базою: коміт при успіху, відкат при помилці, закриття завжди."""
    conn = sqlite3.connect(DB_NAME)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def create_table():
    """Створює таблицю users, якщо її ще немає."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        """)


def validate(username, password, email):
    """Повертає текст помилки або None, якщо дані придатні для запису."""
    if not username:
        return "username не може бути порожнім."
    if not password:
        return "password не може бути порожнім."
    if not EMAIL_PATTERN.fullmatch(email):
        return f"'{email}' не схоже на адресу електронної пошти."
    return None


class User:
    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email
        self.id = None

    def register(self):
        """Зберігає дані про користувача у базу даних. Повертає True / False."""
        error = validate(self.username, self.password, self.email)
        if error:
            print(f"Помилка: {error}")
            return False

        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                    (self.username, self.password, self.email),
                )
                self.id = cursor.lastrowid
        except sqlite3.IntegrityError as e:
            text = str(e).lower()
            if "users.username" in text:
                print(f"Помилка: користувач з іменем '{self.username}' вже існує.")
            elif "users.email" in text:
                print(f"Помилка: email '{self.email}' вже використовується.")
            else:
                print(f"Помилка реєстрації: {e}")
            return False
        except sqlite3.Error as e:
            print(f"Помилка бази даних: {e}")
            return False
        else:
            print(f"Користувач '{self.username}' успішно зареєстрований!")
            return True

    def login(self, username, password):
        """Перевіряє, чи існує користувач з вказаними username та password."""
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id FROM users WHERE username = ? AND password = ?",
                    (username, password),
                )
                row = cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Помилка бази даних: {e}")
            return False

        if row is None:
            return False
        self.id = row[0]
        self.username = username
        return True


def ask(prompt):
    """Запитує непорожнє значення."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значення не може бути порожнім.")


def main():
    create_table()

    while True:
        print("\n--- Меню ---")
        print("1 - Зареєструватися")
        print("2 - Увійти")
        print("3 - Вийти")

        choice = input("Оберіть опцію (1/2/3): ").strip()

        if choice == "1":
            username = ask("Введіть username: ")
            password = ask("Введіть password: ")
            email = ask("Введіть email: ")
            User(username, password, email).register()

        elif choice == "2":
            username = ask("Введіть username: ")
            password = ask("Введіть password: ")
            # За умовою login — метод екземпляра, тому спершу створюємо об'єкт.
            user = User(username, password, email="")
            if user.login(username, password):
                print("Успішний вхід!")
            else:
                print("Неправильні дані!")

        elif choice == "3":
            print("До побачення!")
            break

        else:
            print("Невірний вибір. Спробуйте ще раз.")


def demo():
    """Перевірка реалізації на кількох тестових користувачах (окрема база)."""
    global DB_NAME
    DB_NAME = "demo_users.db"

    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    create_table()

    print("--- Реєстрація трьох користувачів ---")
    User("vasyl", "1234", "vasyl@example.com").register()
    User("olena", "qwerty", "olena@example.com").register()
    User("petro", "pass", "petro@example.com").register()

    print("\n--- Спроби зареєструвати некоректні дані ---")
    User("", "1234", "empty@example.com").register()          # порожній username
    User("bohdan", "1234", "не-пошта").register()             # хибний email

    print("\n--- Спроби зареєструвати дублікати ---")
    User("vasyl", "9999", "new@example.com").register()       # дублікат username
    User("newname", "9999", "olena@example.com").register()   # дублікат email

    print("\n--- Спроби входу ---")
    checks = [("vasyl", "1234"), ("vasyl", "невірний"), ("немає", "1234")]
    for username, password in checks:
        result = User(username, password, email="").login(username, password)
        print(f"{username} / {password} -> "
              f"{'Успішний вхід!' if result else 'Неправильні дані!'}")


if __name__ == "__main__":
    try:
        demo() if "--demo" in sys.argv else main()
    except (EOFError, KeyboardInterrupt):
        print("\nРоботу перервано.")
