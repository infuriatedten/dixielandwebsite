import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_uri = os.environ.get('DATABASE_URL')

engine = create_engine(db_uri)

with engine.connect() as connection:
    connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
    connection.commit()

print("Alembic version table dropped successfully.")
