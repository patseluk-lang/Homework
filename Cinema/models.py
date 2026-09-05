from datetime import datetime

from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Text,
    ForeignKey,
    DateTime,
    UniqueConstraint
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)



class Base(DeclarativeBase):
    pass


movie_genres = Base.metadata.tables.get("movie_genres")

movie_genres = Table(
    "movie_genres",
    Base.metadata,

    Column('movie_id', ForeignKey("movies.id"), primary_key=True),
    Column('genre_id', ForeignKey("genres.id"), primary_key=True),
)

movie_actors = Table(
    "movie_actors",
    Base.metadata,

    Column('movie_id', ForeignKey("movies.id"), primary_key=True),
    Column('actor_id', ForeignKey("actors.id"), primary_key=True),

)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False
    )

    create_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )

    ratings: Mapped[list["Rating"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    watch_history: Mapped[list["WatchHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    genres: Mapped[list["Genre"]] = relationship(
        back_populates="movies",
        secondary=movie_genres
    )

    actors: Mapped[list["Actor"]] = relationship(
        back_populates="movies",
        secondary=movie_actors
    )

    ratings: Mapped[list["Rating"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    watch_history: Mapped[list["WatchHistory"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"Movie("
            f"id={self.id}, "
            f"title={self.title}, "
            f"year={self.year}"
            f")"
        )


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    movies: Mapped[list["Movie"]] = relationship(
        back_populates="genres",
        secondary=movie_genres
    )

    def __repr__(self):
        return f"Genre(id={self.id}, name='{self.name}')"

class Actor(Base):
    __tablename__ = "actors"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    birth_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    movies: Mapped[list["Movie"]] = relationship(
        back_populates="actors",
        secondary=movie_actors
    )

    def __repr__(self):
        return f"Actor(id={self.id}, name='{self.name}')"


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False
    )

    value: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )


    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'movie_id',
            name="unique_user_movie_rating"
        ),
    )

    user: Mapped["User"] = relationship(
        back_populates="ratings"
    )

    movie: Mapped["Movie"] = relationship(
        back_populates="ratings"
    )

    def __repr__(self):
        return (
            f"Rating("
            f"user_id={self.user_id}, "
            f"movie_id={self.movie_id}, "
            f"value={self.value}"
            f")"
        )

class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'movie_id',
            name="unique_user_movie_favorite"
        ),
    )

    user: Mapped["User"] = relationship(
        back_populates="favorites"
    )

    movie: Mapped["Movie"] = relationship(
        back_populates="favorites"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="subscriptions"
    )


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False
    )

    watched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )

    user: Mapped["User"] = relationship(
        back_populates="watch_history"
    )

    movie: Mapped["Movie"] = relationship(
        back_populates="watch_history"
    )