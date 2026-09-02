"""
Розширене завдання: користувачі та їхні акаунти на сайтах (MySQL).

- перевірка дублікатів логінів та email двома способами (UNIQUE у SQL + код Python);
- таблиця sites із зовнішнім ключем на users.id та класом SiteAccount;
- кабінет користувача: додавання сайтів і перегляд списку.

Запуск:
    python users_app_mysql.py
"""

import os
import re
from contextlib import contextmanager

import mysql.connector
from mysql.connector import errorcode

# --- Налаштування підключення -------------------------------------------------
# Значення перевизначаються змінними оточення, щоб не тримати пароль у коді.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}
DB_NAME = os.getenv("DB_NAME", "users_app")

# Ім'я бази підставляється в SQL напряму (параметризувати його не можна),
# тому перевіряємо його окремо й додатково беремо у зворотні лапки.
if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
    raise ValueError(f"Недопустиме ім'я бази даних: {DB_NAME!r}")

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

# Види входу. Для соціальних логін і пароль не питаємо — вони належать провайдеру.
LOGIN_TYPES = {"1": "google", "2": "apple", "3": "facebook", "4": "інша"}
SOCIAL_TYPES = ("google", "apple", "facebook")


@contextmanager
def get_cursor(with_db=True):
    """Курсор MySQL: коміт при успіху, відкат при помилці, закриття завжди."""
    config = dict(DB_CONFIG)
    if with_db:
        config["database"] = DB_NAME
    conn = mysql.connector.connect(**config)
    try:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        finally:
            cursor.close()
    finally:
        conn.close()


def violated_key(error):
    """
    Ім'я UNIQUE-ключа з повідомлення про дублікат.
    MySQL 8 пише 'users.username', MariaDB — 'username', тому далі
    порівнюємо закінченням.
    """
    match = re.search(r"for key '([^']+)'", str(error))
    return match.group(1).lower() if match else ""


def validate(username, password, email):
    """Повертає текст помилки або None, якщо дані придатні для запису."""
    if not username:
        return "username не може бути порожнім."
    if not password:
        return "password не може бути порожнім."
    if not EMAIL_PATTERN.fullmatch(email):
        return f"'{email}' не схоже на адресу електронної пошти."
    return None


def create_tables():
    """Створює базу та таблиці users і sites, якщо їх ще немає."""
    with get_cursor(with_db=False) as cursor:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(f"USE `{DB_NAME}`")

        # Спосіб 1: UNIQUE на username та email — перевірка дублікатів у самій базі.
        # Порівняння username та email нечутливе до регістру (utf8mb4_unicode_ci),
        # а пароль зберігається з utf8mb4_bin, інакше 'Secret' зайшло б як 'secret'.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE
            ) ENGINE=InnoDB
        """)

        # login і password можуть бути NULL — для входу через google/apple/facebook.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                site_name VARCHAR(100) NOT NULL,
                login VARCHAR(100) NULL,
                password VARCHAR(255) NULL,
                login_type VARCHAR(20) NOT NULL,
                CONSTRAINT uq_site_account
                    UNIQUE (user_id, site_name, login_type, login),
                CONSTRAINT fk_sites_user FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)


class User:
    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email
        self.id = None

    @staticmethod
    def find_duplicates(username, email):
        """
        Спосіб 2: перевірка дублікатів засобами Python.

        Логіни та пошти складаємо в ОКРЕМІ множини: одне й те саме значення
        може бути логіном одного користувача та поштою іншого, і плутати
        колонки не можна.

        Порівнюємо через casefold, бо саме так порівнює й база
        (utf8mb4_unicode_ci) — інакше два способи давали б різний результат.
        """
        with get_cursor() as cursor:
            cursor.execute("SELECT username, email FROM users")
            rows = cursor.fetchall()

        logins = {row[0].casefold() for row in rows}
        emails = {row[1].casefold() for row in rows}

        problems = []
        if username.casefold() in logins:
            problems.append(f"логін '{username}' вже зайнятий")
        if email.casefold() in emails:
            problems.append(f"email '{email}' вже зайнятий")
        return problems

    def register(self):
        """Зберігає користувача в базу. Повертає True / False."""
        error = validate(self.username, self.password, self.email)
        if error:
            print(f"Помилка: {error}")
            return False

        try:
            problems = self.find_duplicates(self.username, self.email)
            if problems:
                print("Помилка реєстрації: " + "; ".join(problems) + ".")
                return False

            with get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password, email) "
                    "VALUES (%s, %s, %s)",
                    (self.username, self.password, self.email),
                )
                self.id = cursor.lastrowid
        except mysql.connector.Error as e:
            # Спосіб 1 у дії: UNIQUE у базі страхує від гонки запитів.
            if e.errno == errorcode.ER_DUP_ENTRY:
                # Ім'я порушеного ключа беремо з тексту помилки, а не шукаємо
                # підрядок у всьому повідомленні: у ньому є ще й саме значення
                # (email на кшталт username@example.com збив би пошук).
                key = violated_key(e)
                if key.endswith("username"):
                    print(f"Помилка: користувач з іменем '{self.username}' вже існує.")
                elif key.endswith("email"):
                    print(f"Помилка: email '{self.email}' вже використовується.")
                else:
                    print(f"Помилка: такий запис уже існує. {e}")
            else:
                print(f"Помилка бази даних: {e}")
            return False
        else:
            print(f"Користувач '{self.username}' успішно зареєстрований!")
            return True

    def login(self, username, password):
        """Перевіряє наявність користувача. Повертає True / False."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM users "
                    "WHERE username = %s AND password = %s",
                    (username, password),
                )
                row = cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Помилка бази даних: {e}")
            return False

        if row is None:
            return False
        self.id, self.username = row
        return True


class SiteAccount:
    """Акаунт користувача на сторонньому сайті."""

    def __init__(self, user_id, site_name, login_type, login=None, password=None):
        self.user_id = user_id
        self.site_name = site_name
        self.login_type = login_type
        self.login = login
        self.password = password

    def save(self):
        """Додає запис про сайт у таблицю sites. Повертає True / False."""
        if self.login_type in SOCIAL_TYPES:
            # Вхід через сервіс — власних облікових даних на сайті не існує.
            self.login = None
            self.password = None
            # UNIQUE не ловить дублікат, коли login = NULL (у SQL два NULL
            # не рівні), тому перевіряємо соціальний вхід окремим запитом.
            if self.login_type in self.get_login_types(self.user_id, self.site_name):
                print(f"Помилка: вхід через '{self.login_type}' для сайту "
                      f"'{self.site_name}' уже збережений.")
                return False

        try:
            with get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO sites (user_id, site_name, login, password, "
                    "login_type) VALUES (%s, %s, %s, %s, %s)",
                    (self.user_id, self.site_name, self.login,
                     self.password, self.login_type),
                )
        except mysql.connector.Error as e:
            if e.errno == errorcode.ER_DUP_ENTRY:
                print(f"Помилка: логін '{self.login}' для сайту "
                      f"'{self.site_name}' уже збережений.")
            else:
                print(f"Помилка бази даних: {e}")
            return False
        else:
            print(f"Сайт '{self.site_name}' ({self.login_type}) збережено.")
            return True

    @staticmethod
    def get_login_types(user_id, site_name):
        """Повертає види входу, які користувач уже зберіг для цього сайту."""
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT login_type FROM sites "
                "WHERE user_id = %s AND site_name = %s ORDER BY login_type",
                (user_id, site_name),
            )
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def get_all(user_id):
        """Повертає всі сайти користувача."""
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT site_name, login, password, login_type FROM sites "
                "WHERE user_id = %s ORDER BY site_name, login_type, login",
                (user_id,),
            )
            return cursor.fetchall()

    @staticmethod
    def show_all(user_id):
        """Виводить на екран сайти користувача."""
        rows = SiteAccount.get_all(user_id)
        if not rows:
            print("Поки що немає жодного збереженого сайту.")
            return

        headers = ("Сайт", "Логін", "Пароль", "Вид входу")
        table = [headers] + [
            (site, login or "—", password or "—", login_type)
            for site, login, password, login_type in rows
        ]
        # Ширина кожної колонки — за найдовшим значенням у ній.
        widths = [max(len(row[i]) for row in table) + 2 for i in range(4)]

        print()
        for row in table:
            print("".join(value.ljust(width) for value, width in zip(row, widths)))
            if row is headers:
                print("-" * sum(widths))


def ask(prompt):
    """Запитує непорожнє значення."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значення не може бути порожнім.")


def ask_login_type():
    """Питає вид входу і повертає його назву."""
    print("Вид входу: 1 - google, 2 - apple, 3 - facebook, 4 - інша")
    while True:
        choice = input("Оберіть вид входу (1/2/3/4): ").strip()
        if choice in LOGIN_TYPES:
            return LOGIN_TYPES[choice]
        print("Невірний вибір. Спробуйте ще раз.")


def add_site(user):
    """Додає інформацію про сайт, на якому зареєстрований користувач."""
    site_name = ask("Назва сайту: ")

    existing = SiteAccount.get_login_types(user.id, site_name)
    if existing:
        print(f"Для сайту '{site_name}' уже збережено: {', '.join(existing)}.")

    login_type = ask_login_type()

    if login_type in SOCIAL_TYPES:
        # Не питаємо логін і пароль, яких не існує, ще й якщо запис уже є.
        if login_type in existing:
            print(f"Вхід через '{login_type}' для сайту '{site_name}' "
                  "уже збережений.")
            return
        login, password = None, None
    else:
        login = ask("Логін на сайті: ")
        password = ask("Пароль на сайті: ")

    SiteAccount(user.id, site_name, login_type, login, password).save()


def user_menu(user):
    """Меню для користувача, який увійшов у систему."""
    while True:
        print(f"\n--- Кабінет: {user.username} ---")
        print("1 - Додати сайт")
        print("2 - Показати мої сайти")
        print("3 - Вийти з акаунта")

        choice = input("Оберіть опцію (1/2/3): ").strip()

        if choice == "1":
            add_site(user)
        elif choice == "2":
            SiteAccount.show_all(user.id)
        elif choice == "3":
            print("Вихід з акаунта.")
            break
        else:
            print("Невірний вибір. Спробуйте ще раз.")


def main():
    try:
        create_tables()
    except mysql.connector.Error as e:
        print(f"Не вдалося підключитися до MySQL: {e}")
        return

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
                try:
                    user_menu(user)
                except mysql.connector.Error as e:
                    print(f"Помилка бази даних: {e}")
            else:
                print("Неправильні дані!")

        elif choice == "3":
            print("До побачення!")
            break

        else:
            print("Невірний вибір. Спробуйте ще раз.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nРоботу перервано.")
