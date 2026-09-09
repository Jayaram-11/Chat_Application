
import logging
import psycopg2
import os
from dotenv import load_dotenv


load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
logger = logging.getLogger(__name__)


def create_connection():
    return psycopg2.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def create_table():

    with create_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS USERS (
            UID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            EMAIL TEXT UNIQUE NOT NULL,
            NAME TEXT NOT NULL,
            PASSWORD_HASH BYTEA NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CHAT_ROOMS (
            ROOM_ID INTEGER GENERATED ALWAYS AS IDENTITY
            (START WITH 1001)
            PRIMARY KEY,
            ROOM_NAME TEXT UNIQUE NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MESSAGES (
            MESSAGE_ID INTEGER GENERATED ALWAYS AS IDENTITY
            (START WITH 1001)
            PRIMARY KEY,
            ROOM_ID INTEGER REFERENCES NOT NULL REFERENCES CHAT_ROOMS(ROOM_ID),
            UID INTEGER NOT NULL REFERENCES USERS(UID),
            TIMESTAMP TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            MESSAGE TEXT NOT NULL
            );
        """)

        conn.commit()


def insert_user(email, name, hashed_password):

    user_exist = check_user_exists(email)
    if user_exist:
        return False

    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO USERS (EMAIL, NAME, PASSWORD_HASH)
                VALUES (%s, %s, %s);
            """,
            (email, name, hashed_password))

        return True

    except psycopg2.IntegrityError as ie:
        logger.error(f"IntegrityError:{ie}")
        return False

    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at insert users:{oe}")
        return False


def check_user_exists(email):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM USERS WHERE EMAIL = %s;
            """,
            (email,))

            record = cursor.fetchone()

            if record:
                return True

        return False

    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at user exist:{oe}")
        return False


def fetch_hashed_password(email):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT PASSWORD_HASH FROM USERS WHERE EMAIL = %s;
            """,
            (email,))

            record = cursor.fetchone()
            return record[0]

    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at fetch hash passowrd:{oe}")
        return None


def fetch_userID(email):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT UID FROM USERS WHERE EMAIL = %s;
                """,
                (email,)
            )

            record = cursor.fetchone()
            return record[0]

    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at fetch userID:{oe}")
        return None


def fetch_name(email):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT NAME FROM USERS WHERE EMAIL = %s;
                """,
                (email,)
            )

            record = cursor.fetchone()
            return record[0]

    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at fetch name:{oe}")
        return None


def fetch_room_id(room_name):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ROOM_ID FROM CHAT_ROOMS WHERE ROOM_NAME = %s;
                """,
                (room_name,)
            )

            record = cursor.fetchone()

        return record[0]

    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at fetch roomid:{oe}")
        return None

def save_message(room_id, user_id, message):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO MESSAGES (ROOM_ID, UID, MESSAGE) 
                VALUES (%s, %s, %s);""",
                (room_id, user_id, message)
            )
            conn.commit()


    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at save message:{oe}")


def get_messages(room_id):
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT M.MESSAGE_ID, M.UID, U.NAME,M.MESSAGE, M.TIMESTAMP FROM
                MESSAGES M
                JOIN USERS U ON M.UID = U.UID
                WHERE M.ROOM_ID= %s
                ORDER BY M.TIMESTAMP ASC;
                """,
                (room_id,)
            )
            record= cursor.fetchall()
        return record
    except psycopg2.OperationalError as oe:
        logger.error(f"OperationalError at get messages:{oe}")
        return None
