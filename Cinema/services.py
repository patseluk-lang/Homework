from datetime import datetime

from sqlalchemy import select

from models import (
    User,
    Movie,
    Genre,
    Actor,
    Rating,
    Favorite,
    Subscription,
    WatchHistory
)

def create_user(session, username, email):
    user = User(username=username, email=email)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def create_movie(session, title, description, year, duration):
    movie = Movie(
        title=title,
        description=description,
        year=year,
        duration=duration
    )

    session.add(movie)
    session.commit()
    session.refresh(movie)

    return movie

def get_movie(session, movie_id):
    return session.get(Movie, movie_id)

def get_all_movies(session):
    statement = select(Movie)
    return session.scalars(statement).all()

def update_movie(session, movie_id, title=None, description=None, year=None, duration=None):
    movie = session.get(Movie, movie_id)

    if movie is None:
        return None

    if title is not None:
        movie.title = title

    if description is not None:
        movie.description = description

    if year is not None:
        movie.year = year

    if duration is not None:
        movie.duration = duration

    session.commit()
    session.refresh(movie)

    return movie


def delete_movie(session, movie_id):
    movie = session.get(Movie, movie_id)

    if movie is None:
        return False

    session.delete(movie)
    session.commit()

    return True

def create_genre(session, name):
    genre = Genre(name=name)

    session.add(genre)
    session.commit()
    session.refresh(genre)

    return genre

def get_all_genres(session):
    statement = select(Genre)
    return session.scalars(statement).all()

def add_genre_to_movie(session, movie_id, genre_id):
    movie = session.get(Movie, movie_id)
    genre = session.get(Genre, genre_id)

    if movie is None or genre is None:
        return False

    if genre not in movie.genres:
        movie.genres.append(genre)

    session.commit()

    return True

def create_actor(session, name, birth_year=None):
    actor = Actor(name=name, birth_year=birth_year)

    session.add(actor)
    session.commit()
    session.refresh(actor)

    return actor


def add_actor_to_movie(session, movie_id, actor_id):
    movie = session.get(Movie, movie_id)
    actor = session.get(Actor, actor_id)

    if movie is None or actor is None:
        return False

    if actor not in movie.actors:
        movie.actors.append(actor)

    session.commit()

    return True

def rate_movie(session, movie_id, user_id, value):
    if not 1 <= value <= 10:
        raise ValueError('Value must be between 1 and 10')

    movie = session.get(Movie, movie_id)
    user = session.get(User, user_id)

    if user is None:
        raise ValueError("User not found")

    if movie is None:
        raise ValueError("Movie not found")

    statement = select(Rating).where(
        Rating.user_id == user_id,
        Rating.movie_id == movie_id
    )

    existing_rating = session.scalar(statement)

    if existing_rating:
        raise ValueError('Rating already exists')

    rating = Rating(
        user_id=user_id,
        movie_id=movie_id,
        value=value
    )

    session.add(rating)
    session.commit()
    session.refresh(rating)

    return rating


def add_to_favorites(session, movie_id, user_id):
    movie = session.get(Movie, movie_id)
    user = session.get(User, user_id)

    if movie is None or user is None:
        return False

    statement = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.movie_id == movie_id
    )

    existing = session.scalar(statement)

    if existing:
        return False

    favorite = Favorite(
        user_id=user_id,
        movie_id=movie_id
    )

    session.add(favorite)
    session.commit()

    return True

def remove_from_favorites(session, movie_id, user_id):
    statement = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.movie_id == movie_id
    )

    favorite = session.scalar(statement)

    if favorite is None:
        return False

    session.delete(favorite)
    session.commit()

    return True

def get_favorites(session, user_id):
    statement = (
        select(Movie)
        .join(Favorite)
        .where(Favorite.user_id == user_id)
    )

    return session.scalars(statement).all()


def create_subscriptions(session, user_id, plan, started_at, expires_at):
    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        started_at=started_at,
        expires_at=expires_at
    )

    session.add(subscription)
    session.commit()
    session.refresh(subscription)

    return subscription

def is_subscription_active(session, user_id):
    now = datetime.now()

    statement = (
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.started_at <= now,
            Subscription.expires_at >=now
        )
    )

    subscription = session.scalar(statement)
    return subscription is not None

def watch_movie(session, movie_id, user_id):
    if not is_subscription_active(session, user_id):
        return False

    movie = session.get(Movie, movie_id)

    if movie is None:
        raise ValueError("Movie not found")

    history = WatchHistory(
        user_id=user_id,
        movie_id=movie_id
    )

    session.add(history)
    session.commit()

    return True