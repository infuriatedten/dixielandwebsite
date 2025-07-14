import os
from sqlalchemy import create_engine, text

db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'postgresql://dixielandwebsite_user:gKeSGCTQcARpwDXW4k7CGpOlkDegi2KW@dpg-d1mouvje5dus73dq5p00-a.virginia-postgres.render.com/dixielandwebsite'

engine = create_engine(db_uri)

with engine.connect() as connection:
    connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
    connection.commit()

print("Alembic version table dropped successfully.")
