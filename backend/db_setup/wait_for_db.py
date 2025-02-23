import time
import os
import psycopg2
from psycopg2 import OperationalError


while True:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="db",
            port="5432"
        )
        conn.close()
        break
    except OperationalError:
        time.sleep(1)
