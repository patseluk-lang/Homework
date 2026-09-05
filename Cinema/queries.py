from sqlalchemy.exc import NoResultFound

from models import (
    User,
    Movie,
    Genre,
    Actor,
    Rating,
    Favorite,
    WatchHistory,
    Subscription
)

from sqlalchemy import (
    select,
    func,
    desc
)

def search_movie(session, query):
    statement = (
        select(Movie)
        .where(
            Movie.title.ilike(f"%{query}%")
        ).order_by(Movie.title)
    )

    return session.scalars(statement).all()

def get_popular_movies(session):
    statement = (
        select(
            Movie,
            func.count(
                WatchHistory.id
            ).label("watch_count")
        )
        .join(WatchHistory,
              WatchHistory.movie_id == Movie.id)
        .group_by(Movie.id).order_by(desc("watch_count"))
    )

    return session.scalars(statement).all()

def get_top_movies(session):
    statement = (
        select(
            Movie,
            func.avg(
                Rating.value
            ).label("average_rating")
        )
        .join(
            Rating,
            Rating.movie_id == Movie.id
        )
        .group_by(Movie.id).order_by(desc("average_rating"))
    )

    return session.scalars(statement).all()


def get_user_history(session, user_id):
    statement =(
        select(
            Movie.title,
            WatchHistory.watched_at
        )
        .join(
            Movie,
            WatchHistory.movie_id == Movie.id
        )
        .where(
            WatchHistory.user_id == user_id
        )
        .order_by(desc("watched_at"))
    )

    return session.execute(statement).all()


def get_user_favorite_genre(session, user_id):
    statement = (
        select(
            Genre.name,
            func.count(
                WatchHistory.id
            ).label("watch_count")
        )
        .join(
            Movie,
            WatchHistory.movie_id == Movie.id
        )
        .join(
            Movie.genres
        )
        .where(
            WatchHistory.user_id == user_id
        )
        .group_by(
            Genre.id
        )
        .order_by(desc("watch_count"))

    )

    return session.execute(statement).all()

def get_favorite_movie(session, user_id):
    statement =(
        select(
            Movie.title,
            func.count(WatchHistory.id).label("watch_count"),
        )
        .join(
            Movie,
            WatchHistory.movie_id == Movie.id
        )
        .where(
            WatchHistory.user_id == user_id
        )
        .group_by(
            Movie.id,
            Movie.title
        )
        .order_by(desc("watch_count"))
    )

    return session.execute(statement).all()

def get_favorite_by_user(session, user_id, genre=False, movie=False):
    favorite_statement = []
    if genre:
        favorite_statement = get_user_favorite_genre(session, user_id)
    if movie:
        favorite_statement = get_favorite_movie(session, user_id)
    favorites = []
    if favorite_statement:
        max_watched = favorite_statement[0][1]
        for genre_or_movie, count in favorite_statement:
            if count == max_watched:
                favorites.append(genre_or_movie)

    return favorites


def get_movie_details(session, movie_id):
    movie = session.get(Movie, movie_id)

    if movie is None:
        return None

    rating_statement = (
        select(
            func.avg(Rating.value)
        ).where(Rating.movie_id == movie_id)
    )

    average_rating = session.scalar(rating_statement)

    watch_statement = (
        select(
            func.count(WatchHistory.id)
        ).where(
            WatchHistory.movie_id == movie_id
        )
    )

    watch_count = session.scalar(watch_statement)

    last_rating_statement = (
        select(
            User.username,
            Rating.value
        )
        .join(
            User,
            Rating.user_id == User.id
        )
        .where(
            Rating.movie_id == movie_id
        )
    )

    try:
        last_rating = session.scalar(last_rating_statement)[:5]
    except:
        last_rating = []

    return {
        "title": movie.title,
        "year": movie.year,
        "duration": movie.duration,
        "description": movie.description,
        "genres": movie.genres,
        "actors": movie.actors,
        "avg_rating": average_rating,
        "watch_count": watch_count,
        "last_rating": last_rating,
    }



def get_user_statistics(session, user_id):
    user = session.get(User, user_id)

    if user is None:
        return None

    watch_count_statement = (
        select(
            func.count(WatchHistory.id)
        ).where(
            WatchHistory.user_id == user_id
        )
    )

    watch_count = session.scalar(watch_count_statement)

    rating_count_statement = (
        select(
            func.count(Rating.id)
        ).where(
            Rating.user_id == user_id
        )
    )

    rating_count = session.scalar(rating_count_statement)

    favorite_count_statement = (
        select(
            func.count(Favorite.id)
        ).where(
            Favorite.user_id == user_id
        )
    )

    favorite_count = session.scalar(favorite_count_statement)


    favorite_genres = get_favorite_by_user(session, user_id, genre=True)
    favorite_movies = get_favorite_by_user(session, user_id, movie=True)

    rating_avg_statement = (
        select(
            func.avg(Rating.value)
        ).where(
            Rating.user_id == user_id
        )
    )

    rating_avg = session.scalar(rating_avg_statement)

    subscription_plan_and_expires_statement = (
        select(
            Subscription.plan,
            Subscription.expires_at
        )
        .where(Subscription.user_id == user_id)
    )


    try:
        subscription_plan_and_expires = session.execute(subscription_plan_and_expires_statement).one()
    except NoResultFound:
        subscription_plan_and_expires = None


    return {
        "username": user.username,
        "watch_count": watch_count,
        "rating_count": rating_count,
        "favorite_count": favorite_count,
        "favorite_genres": favorite_genres,
        "favorite_movies": favorite_movies,
        "rating_avg": rating_avg,
        "subscription_plan": subscription_plan_and_expires[0] if subscription_plan_and_expires else None,
        "subscription_expires": subscription_plan_and_expires[1].strftime("%d.%m.%Y %H:%M:%S") if subscription_plan_and_expires else None,

    }

def recommend_movies(session, user_id):
    watched_subquery = (
        select(
            WatchHistory.movie_id
        )
        .where(WatchHistory.user_id == user_id)
    )

    statement = (
        select(Movie.title)
        .join(Movie.genres)
        .where(
            Movie.id.not_in(watched_subquery)
        )
        .distinct()
    )

    return session.scalars(statement).all()