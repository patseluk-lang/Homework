import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Example: postgresql+psycopg2://user:password@localhost:5432/online_cinema
DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
