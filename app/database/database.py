from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
from ..config.config import setting

SQLALCHEMY_URL = f'postgresql://{setting.database_username}:{setting.database_password}@{setting.database_hostname}:{setting.database_port}/{setting.database_name}'

engine=create_engine(SQLALCHEMY_URL)


sessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)


Base = declarative_base()


def get_db():
    db=sessionLocal()
    try:
        yield db
    finally:
        db.close()





