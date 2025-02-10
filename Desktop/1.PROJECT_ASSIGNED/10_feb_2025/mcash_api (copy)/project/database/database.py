import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from sqlalchemy.pool import QueuePool

load_dotenv()
Base = declarative_base()



database_url = os.environ.get("DATABASE_URL","mysql+pymysql://MCash_admin:MCash_admin@127.0.0.1/mcash_api")

engine = create_engine(database_url,poolclass=QueuePool,pool_size=10, max_overflow=5,pool_timeout=30 )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_session() -> Generator:
    try:
        data_base = SessionLocal()
        yield data_base
    finally:
        data_base.close()  # noqa
