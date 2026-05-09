import os
import psycopg2
from dotenv import load_dotenv

# Load the .env file from the root
load_dotenv()


def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None
