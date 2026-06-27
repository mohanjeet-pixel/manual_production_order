from contextlib import contextmanager

import psycopg2
import psycopg2.pool
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

from backend.core.config import DB_CONFIG

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def init_pool(minconn: int = 2, maxconn: int = 20) -> None:
    global _pool
    _pool = psycopg2.pool.ThreadedConnectionPool(minconn, maxconn, **DB_CONFIG)


def close_pool() -> None:
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None


@contextmanager
def get_db():
    conn = _pool.getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def get_engine():
    cfg = DB_CONFIG
    password = quote_plus(cfg["password"])
    connection_string = (
        f"postgresql+psycopg2://"
        f"{cfg['user']}:{password}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )
    return create_engine(connection_string)


def load_to_postgres(csv_file: str, table_name: str):
    from backend.core.logger import get_logger
    logger = get_logger("etl")

    logger.info("Reading CSV...")
    df = pd.read_csv(csv_file)
    logger.info(f"Records found: {len(df)}")

    engine = get_engine()
    logger.info("Loading into PostgreSQL...")
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    logger.info(f"Loaded {len(df)} rows into '{table_name}'")
