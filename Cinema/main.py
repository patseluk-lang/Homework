from database import SessionLocal, engine
from models import Base, User
from seed import seed_database

import services
import queries

from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)

menu = """
╔══════════════════════════════════════╗
║             ONLINE CINEMA            ║
╠══════════════════════════════════════╣
║                                      ║
║  1. Переглянути фільм                ║
║  2. Переглянути фільми               ║
║  3. Знайти фільм                     ║
║  4. Переглянути інформацію про фільм ║
║  5. Переглянути топ фільми за перег. ║
║  6. Переглянути топ фільми за рейт.  ║
║  7. Переглянути жанри                ║
║  8. Додати фільм до обраного         ║
║  9. Видалити фільм з обраного        ║
║  10. Переглянути фільми з обраного   ║
║  11. Оцінити фільм                   ║
║  12. Подивитися фільм                ║
║  13. Створити підписку               ║
║  14. Переглянути активну підписку    ║
║  15. Історія переглядів              ║
║  16. Моя статистика                  ║
║  17. Рекомендації                    ║
║                                      ║
║ ───────── АДМІН ──────────────────── ║
║ 18. Додати user                      ║
║ 19. Додати фільм                     ║
║ 20. Редагувати фільм                 ║
║ 21. Видалити фільм                   ║
║ 22. Додати жанр                      ║
║ 23. Додати жанр до фільму            ║
║ 24. Додати актора                    ║
║ 25. Додати актора до фільму          ║
║                                      ║
║  0. Вийти                            ║
╚══════════════════════════════════════╝
            """



def print_separator():
    print("═"*50)

def print_info(choice):
    index_choice = menu.find(choice)
    index_sb = menu.find("║", index_choice)
    result = menu[index_choice:index_sb].strip()
    print(result)
    print_separator()

def print_movie(movie):
    print(f"Title: {movie.title}")
    print(f"Description: {movie.description}")
    print(f"Duration: {movie.duration}")
    print(f"Year: {movie.year}")
    print_separator()

def print_movies(movies):
    for movie in movies:
        print_movie(movie)

def print_genres(genres):
    for genre in genres:
        print(f"Name: {genre.name}")
        print_separator()

def print_movie_details(movie_details):
    print_separator()
    for key, value in movie_details.items():
        if isinstance(value, list):
            print(f"{key.title()}: ")
            for item in value:
                print(f"\t-{item.name}")
        else:
            print(f"{key.title()}: {value}")
    print_separator()

def print_user_details(movie_details):
    print_separator()
    for key, value in movie_details.items():
        if isinstance(value, list):
            print(f"{key.title()}: ")
            for item in value:
                print(f"\t-{item}")
        else:
            print(f"{key.title()}: {value}")
    print_separator()

def main():
    # seed_database()
    # print("Database Created")
    with SessionLocal() as session:
        while True:
            print(menu)
            choice = input("Ваш вібір: ")

            if choice == "1":
                print_info(choice)
                movie_id = input("Введіть movie_id: ")
                movie = services.get_movie(session, movie_id)
                print_movie(movie)
                input("Press any key to continue...")


            if choice == "2":
                print_info(choice)
                movies = services.get_all_movies(session)
                print_movies(movies)
                input("Press any key to continue...")

            elif choice == "3":
                print_info(choice)
                query = input("Введіть назву або частину назви: ")
                movies = queries.search_movie(session, query)
                print_movies(movies)
                input("Press any key to continue...")

            elif choice == "4":
                print_info(choice)
                movie_id = input("Введіть movie_id: ")
                movie = queries.get_movie_details(session, movie_id)
                print_movie_details(movie)
                input("Press any key to continue...")

            elif choice == "5":
                print_info(choice)
                popular_movie = queries.get_popular_movies(session)
                print_movies(popular_movie)
                input("Press any key to continue...")

            elif choice == "6":
                print_info(choice)
                top_movie = queries.get_top_movies(session)
                print_movies(top_movie)
                input("Press any key to continue...")

            elif choice == "7":
                print_info(choice)
                genres = services.get_all_genres(session)
                print_genres(genres)
                input("Press any key to continue...")

            elif choice == "8":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                movie_id = input("Введіть movie_id: ")

                result = services.add_to_favorites(session, movie_id, user_id)

                if result:
                    print("Фільм додано до обраного")
                else:
                    print("Не вдалося додати фільм")
                input("Press any key to continue...")

            elif choice == "9":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                movie_id = input("Введіть movie_id: ")

                result = services.remove_from_favorites(session, movie_id, user_id)

                if result:
                    print("Фільм видалено з обраного")
                else:
                    print("Не вдалося видалити фільм")
                input("Press any key to continue...")

            elif choice == "10":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                fav_movies_by_user = services.get_favorites(session, user_id)
                print_movies(fav_movies_by_user)
                input("Press any key to continue...")

            elif choice == "11":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                movie_id = input("Введіть movie_id: ")
                value =  int(input("Оцінка 1-10: "))

                try:
                    services.rate_movie(session, movie_id, user_id, value)
                    print("Оцінку успішно додано")

                except ValueError as error:
                    print(f"Помилка: {error}")
                input("Press any key to continue...")

            elif choice == "12":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                movie_id = input("Введіть movie_id: ")
                try:
                    result = services.watch_movie(session, movie_id, user_id)
                    if result:
                        print("Приємного перегляду")
                    else:
                        print("Немає активноі підписки")
                except ValueError as error:
                    print(f"Помилка: {error}")

                input("Press any key to continue...")

            elif choice == "13":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                while True:
                    plan = input("Введіть plan (Standard or Premium): ").title()
                    if plan not in ["Standard", "Premium"]:
                        continue
                    else:
                        break
                started_at = datetime.now()
                if plan == "Standard":
                    expires_at = datetime.now() + timedelta(minutes=30)
                else:
                    expires_at = datetime.now() + timedelta(minutes=60)

                sub = services.create_subscriptions(session, user_id, plan, started_at, expires_at)
                print_separator()
                print(f"Your subscription has been created! user_id: {sub.user_id}, plan: {sub.plan}, expires_at: {sub.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
                input("Press any key to continue...")


            elif choice == "14":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                is_active = services.is_subscription_active(session, user_id)
                print(is_active)
                input("Press any key to continue...")

            elif choice == "15":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                movies = queries.get_user_history(session, user_id)
                print_separator()
                for movie in movies:
                    print(f"Title: {movie[0]}, Date: {movie[1].strftime("%d.%m.%Y %H:%M")}")
                print_separator()
                input("Press any key to continue...")

            elif choice == "16":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                statistics = queries.get_user_statistics(session, user_id)
                print_user_details(statistics)
                input("Press any key to continue...")

            elif choice == "17":
                print_info(choice)
                user_id = int(input("Введіть user_id: "))
                recommended = queries.recommend_movies(session, user_id)
                print_separator()
                for movie in recommended:
                    print(f"Title: {movie}")
                print_separator()
                input("Press any key to continue...")

            elif choice == "18":
                print_info(choice)
                email = input("Введіть email: ")
                username = input("Введіть username: ")
                new_user = services.create_user(session, username, email)
                print(f"Added new user id: {new_user.id}, username: {new_user.username}, email: {new_user.email}")
                input("Press any key to continue...")

            elif choice == "19":
                print_info(choice)
                title = input("Введіть title: ")
                description = input("Введіть description: ")
                year = input("Введіть year: ")
                duration = input("Введіть duration: ")

                new_movie = services.create_movie(session, title, description, year, duration)
                print_separator()
                print_movie(new_movie)
                input("Press any key to continue...")

            elif choice == "20":
                print_info(choice)
                movie_id = input("Введіть new movie_id: ")
                title = input("Введіть new title: ")
                description = input("Введіть new description: ")
                year = input("Введіть new year: ")
                duration = input("Введіть new duration: ")

                updated_movie = services.update_movie(session, movie_id, title, description, year, duration)
                print_separator()
                print_movie(updated_movie)
                input("Press any key to continue...")

            elif choice == "21":
                print_info(choice)
                movie_id = input("Введіть movie_id: ")

                result = services.delete_movie(session, movie_id)

                if result:
                    print("Фільм видалено")
                else:
                    print("Не вдалося видалити фільм")
                input("Press any key to continue...")

            elif choice == "22":
                print_info(choice)
                name_genre = input("Введіть назву жанру: ")
                new_genre = services.create_genre(session, name_genre)
                print(f"Added new genre id: {new_genre.id}, username: {new_genre.name}")
                input("Press any key to continue...")

            elif choice == "23":
                print_info(choice)
                movie_id = input("Введіть movie_id: ")
                genre_id = input("Введіть id жанру: ")
                add_genre_movie = services.add_genre_to_movie(session, movie_id, genre_id)
                if add_genre_movie:
                    print("Додали жанр до фільму")
                else:
                    print("Не вдалося додати жанр до фільму")
                input("Press any key to continue...")

            elif choice == "24":
                print_info(choice)
                name_actor = input("Введіть ім'я актора: ")
                bd_actor = input("Введіть рік народження актора: ")
                new_actor = services.create_actor(session, name_actor, bd_actor)
                print(f"Added new actor id: {new_actor.id}, username: {new_actor.name}")
                input("Press any key to continue...")

            elif choice == "25":
                print_info(choice)
                movie_id = input("Введіть movie_id: ")
                actor_id = input("Введіть id актора: ")
                add_actor_movie = services.add_actor_to_movie(session, movie_id, actor_id)
                if add_actor_movie:
                    print("Додали актора до фільму")
                else:
                    print("Не вдалося додати актора до фільму")
                input("Press any key to continue...")


if __name__ == "__main__":
    main()