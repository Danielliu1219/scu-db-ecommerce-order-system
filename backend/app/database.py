from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from .config import settings


def make_engine(url):
    if make_url(url).drivername != "postgresql+psycopg":
        raise ValueError("Configure a postgresql+psycopg database URL")
    engine = create_engine(
        url,
        isolation_level="READ COMMITTED",
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=8,
        max_overflow=8,
        connect_args={"options": "-c timezone=Asia/Shanghai"},
    )

    @event.listens_for(engine, "connect")
    def configure(dbapi, _):
        # Keep session settings outside an implicit transaction on pooled connections.
        original = dbapi.autocommit
        dbapi.autocommit = True
        try:
            with dbapi.cursor() as cursor:
                cursor.execute("SET TIME ZONE 'Asia/Shanghai'")
                cursor.execute("SET lock_timeout = '5s'")
        finally:
            dbapi.autocommit = original

    return engine


engine = make_engine(settings().database_url)
SessionFactory = sessionmaker(engine, expire_on_commit=False)
