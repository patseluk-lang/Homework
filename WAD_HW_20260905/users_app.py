import sqlite3

DB_NAME = "users.db"


def create_table():
    """Створює таблицю users, якщо її ще немає"""
    conn = sqlite3.connect(DB_NAME)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL
                )
            """)
    finally:
        conn.close()


class User:
    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    def register(self):
        """Зберігає дані про користувача у базу даних"""
        conn = sqlite3.connect(DB_NAME)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                    (self.username, self.password, self.email),
                )
            print(f"Користувач '{self.username}' успішно зареєстрований!")
            return True
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
        finally:
            conn.close()

    def login(self, username, password):
        """Перевіряє, чи існує користувач з вказаними username та password"""
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ? AND password = ?",
                (username, password),
            )
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Помилка бази даних: {e}")
            return False
        finally:
            conn.close()


def main():
    create_table()

    while True:
        print("\n--- Меню ---")
        print("1 - Зареєструватися")
        print("2 - Увійти")
        print("3 - Вийти")

        choice = input("Оберіть опцію (1/2/3): ").strip()

        if choice == "1":
            username = input("Введіть username: ").strip()
            password = input("Введіть password: ").strip()
            email = input("Введіть email: ").strip()
            User(username, password, email).register()

        elif choice == "2":
            username = input("Введіть username: ").strip()
            password = input("Введіть password: ").strip()
            user = User(username, password, "")
            if user.login(username, password):
                print("Вхід успішний!")
            else:
                print("Неправильні дані!")

        elif choice == "3":
            print("До побачення!")
            break

        else:
            print("Невірний вибір. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
