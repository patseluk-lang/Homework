from datetime import datetime, timedelta

from database import SessionLocal, engine
from models import Base
import services

Base.metadata.create_all(bind=engine)

def seed_database():
    with SessionLocal() as session:
        bob = services.create_user(
            session,
            "Bob",
            "bob@gmail.com"
        )

        anna = services.create_user(
            session,
            "Anna",
            "anna@example.com"
        )

        ivan = services.create_user(
            session,
            "Ivan",
            "ivan@gamil.com"
        )


        sci_fi = services.create_genre(
            session,
            "Sci-Fi"
        )

        drama = services.create_genre(
            session,
            "Drama"
        )

        adventure = services.create_genre(
            session,
            "Adventure"
        )

        comedy = services.create_genre(
            session,
            "Comedy"
        )


        matthew = services.create_actor(
            session,
            "Matthew McConaughey",
            1969
        )

        anne  = services.create_actor(
            session,
            "Anne Hathaway",
            1982
        )

        jessica = services.create_actor(
            session,
            "Jessica Chastain",
            1977
        )

        leonardo = services.create_actor(
            session,
            "Leonardo DiCaprio",
            1974
        )

        joseph = services.create_actor(
            session,
            "Joseph Gordon-Levitt",
            1981
        )


        interstellar = services.create_movie(
            session,
            "Interstellar",
            "Команда дослідників вирушає "
            "у космос на пошуки нового дому "
            "для людства.",
            2014,
            169
        )

        inception = services.create_movie(
            session,
            "Inception",
            "Команда професіоналів може "
            "проникати у сни людей.",
            2010,
            148
        )

        matrix = services.create_movie(
            session,
            "The Matrix",
            "Хакер дізнається правду "
            "про реальність.",
            1999,
            136
        )

        dune = services.create_movie(
            session,
            "Dune",
            "Масштабна історія про планету "
            "Арракіс.",
            2021,
            155
        )


        services.add_genre_to_movie(
            session,
            interstellar.id,
            sci_fi.id
        )

        services.add_genre_to_movie(
            session,
            interstellar.id,
            drama.id
        )

        services.add_genre_to_movie(
            session,
            interstellar.id,
            adventure.id
        )

        services.add_genre_to_movie(
            session,
            inception.id,
            sci_fi.id
        )

        services.add_genre_to_movie(
            session,
            inception.id,
            drama.id
        )

        services.add_genre_to_movie(
            session,
            matrix.id,
            sci_fi.id
        )

        services.add_genre_to_movie(
            session,
            dune.id,
            sci_fi.id
        )

        services.add_genre_to_movie(
            session,
            dune.id,
            adventure.id
        )

        services.add_actor_to_movie(
            session,
            interstellar.id,
            matthew.id
        )

        services.add_actor_to_movie(
            session,
            interstellar.id,
            anne.id
        )

        services.add_actor_to_movie(
            session,
            inception.id,
            leonardo.id
        )

        services.add_actor_to_movie(
            session,
            inception.id,
            joseph.id
        )


        services.create_subscriptions(
            session,
            bob.id,
            "Premium",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(minutes=5)
        )

        services.create_subscriptions(
            session,
            anna.id,
            "Standard",
            datetime.now() - timedelta(days=5),
            datetime.now() + timedelta(minutes=2)
        )

        services.rate_movie(
            session,
            bob.id,
            interstellar.id,
            10
        )

        services.rate_movie(
            session,
            anna.id,
            interstellar.id,
            9
        )

        services.rate_movie(
            session,
            ivan.id,
            interstellar.id,
            8
        )

        services.rate_movie(
            session,
            bob.id,
            inception.id,
            9
        )

        services.rate_movie(
            session,
            anna.id,
            inception.id,
            10
        )

        services.rate_movie(
            session,
            bob.id,
            matrix.id,
            9
        )

        services.add_to_favorites(
            session,
            bob.id,
            interstellar.id
        )

        services.add_to_favorites(
            session,
            bob.id,
            inception.id
        )

        services.add_to_favorites(
            session,
            anna.id,
            matrix.id
        )

        services.watch_movie(
            session,
            bob.id,
            interstellar.id
        )

        services.watch_movie(
            session,
            bob.id,
            inception.id
        )

        services.watch_movie(
            session,
            bob.id,
            matrix.id
        )

        services.watch_movie(
            session,
            anna.id,
            interstellar.id
        )

        services.watch_movie(
            session,
            anna.id,
            inception.id
        )

if __name__ == "__main__":
    seed_database()