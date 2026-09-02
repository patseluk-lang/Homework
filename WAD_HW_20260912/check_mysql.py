"""
Перевірка MySQL-частини на реальному сервері.

Використовує ОКРЕМУ базу users_app_check і видаляє її на початку та в кінці,
тому робочої бази не чіпає.

Запуск:
    export DB_HOST=localhost
    export DB_PORT=3306
    export DB_USER=root
    export DB_PASSWORD=secret
    python check_mysql.py
"""

import os

# Підміняємо ім'я бази ДО імпорту: модуль читає DB_NAME на рівні модуля.
os.environ["DB_NAME"] = "users_app_check"

import mysql.connector

import users_app_mysql as app
from users_app_mysql import SiteAccount, User, get_cursor

passed = []
failed = []


def check(name, condition, note=""):
    (passed if condition else failed).append(name)
    mark = "OK  " if condition else "ЗБІЙ"
    print(f"[{mark}] {name}" + (f"  — {note}" if note else ""))


def drop_db():
    with get_cursor(with_db=False) as cursor:
        cursor.execute(f"DROP DATABASE IF EXISTS `{app.DB_NAME}`")


def main():
    print(f"Сервер: {app.DB_CONFIG['host']}:{app.DB_CONFIG['port']}, "
          f"база: {app.DB_NAME}\n")

    with get_cursor(with_db=False) as cursor:
        cursor.execute("SELECT VERSION()")
        print("Версія сервера:", cursor.fetchone()[0], "\n")

    drop_db()

    # 1. DDL виконується без помилок (COLLATE utf8mb4_bin, зворотні лапки,
    #    складений UNIQUE, зовнішній ключ).
    try:
        app.create_tables()
        check("create_tables() виконався", True)
    except mysql.connector.Error as e:
        check("create_tables() виконався", False, str(e))
        return

    # 2. Колонка пароля справді отримала бінарне порівняння.
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT collation_name FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = 'users' "
            "AND column_name = 'password'",
            (app.DB_NAME,),
        )
        collation = cursor.fetchone()[0]
    check("users.password має бінарне порівняння", collation.endswith("_bin"),
          f"collation = {collation}")

    # 3. Звичайна реєстрація.
    vasyl = User("vasyl", "Secret", "vasyl@example.com")
    check("реєстрація користувача", vasyl.register() and vasyl.id is not None)

    # 4. Пароль чутливий до регістру — головна вада, яку виправляли.
    check("вхід із правильним паролем",
          User("", "", "").login("vasyl", "Secret"))
    check("вхід із паролем в іншому регістрі відхилено",
          not User("", "", "").login("vasyl", "secret"))

    # 5. Дублікат ловить перевірка в Python (спосіб 2), і вона узгоджена
    #    з регістронечутливим порівнянням бази.
    check("дублікат username в іншому регістрі відхилено",
          not User("VASYL", "1234", "new@example.com").register())
    check("дублікат email в іншому регістрі відхилено",
          not User("newname", "1234", "VASYL@example.com").register())

    # 6. Ключова перевірка: UNIQUE у базі (спосіб 1) називає правильне поле,
    #    коли email містить підрядок "username". Тут перевірка в Python
    #    свідомо обходиться — імітуємо гонку запитів.
    User("someone", "1234", "admin_username@example.com").register()
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, email) "
                "VALUES (%s, %s, %s)",
                ("other", "1234", "admin_username@example.com"),
            )
        check("UNIQUE спрацював на дублікаті email", False, "дублікат пройшов")
    except mysql.connector.Error as e:
        key = app.violated_key(e)
        check("ім'я порушеного ключа розібрано правильно",
              key.endswith("email"),
              f"ключ = {key!r}, текст = {e}")

    # 7. Кілька акаунтів «інша» на одному сайті дозволені, той самий логін — ні.
    uid = vasyl.id
    check("перший акаунт 'інша'",
          SiteAccount(uid, "github.com", "інша", "vasyl_dev", "p1").save())
    check("другий акаунт 'інша' з іншим логіном",
          SiteAccount(uid, "github.com", "інша", "vasyl_work", "p2").save())
    check("той самий логін удруге відхилено",
          not SiteAccount(uid, "github.com", "інша", "vasyl_dev", "p3").save())

    # 8. Соціальний вхід: NULL у базі, повтор блокується перевіркою в save().
    check("соціальний вхід збережено",
          SiteAccount(uid, "github.com", "google").save())
    check("повтор соціального входу відхилено",
          not SiteAccount(uid, "github.com", "google").save())

    with get_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM sites WHERE user_id = %s "
            "AND login_type = 'google' AND login IS NULL", (uid,))
        social_rows = cursor.fetchone()[0]
    check("соціальний вхід записаний з NULL і без дублікатів", social_rows == 1,
          f"рядків = {social_rows}")

    # 9. Зовнішній ключ з ON DELETE CASCADE.
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (uid,))
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM sites WHERE user_id = %s", (uid,))
        left = cursor.fetchone()[0]
    check("ON DELETE CASCADE прибрав сайти", left == 0, f"залишилось {left}")

    drop_db()

    print(f"\nПройдено: {len(passed)}, збоїв: {len(failed)}")
    if failed:
        print("Не пройшли:")
        for name in failed:
            print("  -", name)


if __name__ == "__main__":
    try:
        main()
    except mysql.connector.Error as e:
        print(f"Не вдалося підключитися до MySQL: {e}")
