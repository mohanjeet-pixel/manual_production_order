import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus


def get_engine():

    username = "postgres"
    password = quote_plus("bull@123")
    host = "localhost"
    port = "5432"
    database = "Manual_order"

    connection_string = (
        f"postgresql+psycopg2://"
        f"{username}:{password}@{host}:{port}/{database}"
    )

    return create_engine(connection_string)


def load_to_postgres(csv_file, table_name):

    print("📥 Reading CSV...")

    df = pd.read_csv(csv_file)

    print(f"📊 Records Found : {len(df)}")

    engine = get_engine()

    print("🔄 Loading into PostgreSQL...")

    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False
    )

    print(
        f"✅ Successfully loaded {len(df)} rows into '{table_name}' table"
    )
