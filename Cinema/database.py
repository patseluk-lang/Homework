from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2

DATABASE_URL = "postgresql+psycopg2://patselukserv:d29011972@localhost:5433/online_cinema"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)