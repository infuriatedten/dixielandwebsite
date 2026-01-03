import os
from sqlalchemy import create_engine, text

from dotenv import load_dotenv

load_dotenv()
db_uri = os.environ.get('DATABASE_URL')
if db_uri and 'postgresql://' in db_uri:
    if 'sslmode' not in db_uri:
        db_uri += '?sslmode=require'
else:
    raise RuntimeError("DATABASE_URL is not properly set.")

engine = create_engine(db_uri)

with engine.connect() as connection:
    connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
    connection.commit()

print("Alembic version table dropped successfully.")
