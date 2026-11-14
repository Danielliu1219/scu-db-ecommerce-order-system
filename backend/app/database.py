from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .config import settings

SQL_MODE = "STRICT_TRANS_TABLES,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"


def make_engine(url):
    engine = create_engine(
        url,
        isolation_level="READ COMMITTED",
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=8,
        max_overflow=8,
    )

    @event.listens_for(engine, "connect")
    def configure(dbapi, _):
        with dbapi.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci")
            cursor.execute("SET SESSION time_zone = '+08:00'")
            cursor.execute("SET SESSION sql_mode = %s", (SQL_MODE,))

    return engine


engine = make_engine(settings().database_url)
SessionFactory = sessionmaker(engine, expire_on_commit=False)
