
import logging
import asyncpg
import os
from dotenv import load_dotenv


load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

logger = logging.getLogger(__name__)


async def create_connection():
    return await asyncpg.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


async def create_table():

    conn = await create_connection()

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS USERS (
            UID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            EMAIL TEXT UNIQUE NOT NULL,
            NAME TEXT NOT NULL,
            PASSWORD_HASH BYTEA NOT NULL
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS CHAT_ROOMS (
            ROOM_ID INTEGER GENERATED ALWAYS AS IDENTITY
            (START WITH 101)
            PRIMARY KEY,
            ROOM_NAME TEXT UNIQUE NOT NULL
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS MESSAGES (
            MESSAGE_ID INTEGER GENERATED ALWAYS AS IDENTITY
            (START WITH 1001)
            PRIMARY KEY,
            ROOM_ID INTEGER NOT NULL REFERENCES CHAT_ROOMS(ROOM_ID),
            UID INTEGER NOT NULL REFERENCES USERS(UID),
            TIMESTAMP TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            MESSAGE TEXT NOT NULL
            );
        """)

    finally:
        await conn.close()


async def insert_user(email, name, hashed_password):

    user_exist = await check_user_exists(email)

    if user_exist:
        return False

    conn = None

    try:
        conn = await create_connection()

        await conn.execute("""
            INSERT INTO USERS (EMAIL, NAME, PASSWORD_HASH)
            VALUES ($1, $2, $3);
        """,
        email, name, hashed_password)

        return True

    except asyncpg.IntegrityError as ie:
        logger.error(f"IntegrityError:{ie}")
        return False

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at insert users:{pe}")
        return False

    finally:
        if conn:
            await conn.close()


async def insert_room(room_name):
    conn = None

    try:
        conn = await create_connection()

        await conn.execute(
            """
            INSERT INTO CHAT_ROOMS(ROOM_NAME)
            VALUES ($1);
            """,
            room_name
        )

        return True

    except asyncpg.IntegrityError as ie:
        logger.error(f"IntegrityError at chat rooms DB:{ie}")
        return False

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at chat rooms DB:{pe}")
        return None

    finally:
        if conn:
            await conn.close()


async def check_user_exists(email):
    conn = None

    try:
        conn = await create_connection()

        record = await conn.fetchrow(
            """
            SELECT * FROM USERS WHERE EMAIL = $1;
            """,
            email
        )

        if record:
            return True

        return False

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at user exist:{pe}")
        return False

    finally:
        if conn:
            await conn.close()


async def fetch_hashed_password(email):
    conn = None

    try:
        conn = await create_connection()

        record = await conn.fetchrow(
            """
            SELECT PASSWORD_HASH FROM USERS WHERE EMAIL = $1;
            """,
            email
        )

        if record is None:
            return None

        return record["password_hash"]

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at fetch hash password:{pe}")
        return None

    finally:
        if conn:
            await conn.close()


async def fetch_userID(email):
    conn = None

    try:
        conn = await create_connection()

        record = await conn.fetchrow(
            """
            SELECT UID FROM USERS WHERE EMAIL = $1;
            """,
            email
        )

        if record is None:
            return None

        return record["uid"]

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at fetch userID:{pe}")
        return None

    finally:
        if conn:
            await conn.close()


async def fetch_name(email):
    conn = None

    try:
        conn = await create_connection()

        record = await conn.fetchrow(
            """
            SELECT NAME FROM USERS WHERE EMAIL = $1;
            """,
            email
        )

        if record is None:
            return None

        return record["name"]

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at fetch name:{pe}")
        return None

    finally:
        if conn:
            await conn.close()


async def fetch_room_id(room_name):
    conn = None

    try:
        conn = await create_connection()

        record = await conn.fetchrow(
            """
            SELECT ROOM_ID FROM CHAT_ROOMS WHERE ROOM_NAME = $1;
            """,
            room_name
        )

        if record is None:
            return None

        return record["room_id"]

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at fetch roomid:{pe}")
        return None

    finally:
        if conn:
            await conn.close()


async def save_message(room_id, user_id, message):
    conn = None

    try:
        conn = await create_connection()

        await conn.execute(
            """
            INSERT INTO MESSAGES (ROOM_ID, UID, MESSAGE)
            VALUES ($1, $2, $3);
            """,
            room_id,
            user_id,
            message
        )

        return True

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at save message:{pe}")
        return False

    finally:
        if conn:
            await conn.close()


async def get_messages(room_id, prev_id=None, limit=20):
    conn = None

    try:
        conn = await create_connection()

        if prev_id is None:
            records = await conn.fetch(
                """
                SELECT M.MESSAGE_ID,
                       M.UID,
                       U.NAME,
                       M.MESSAGE,
                       M.TIMESTAMP
                FROM MESSAGES M
                JOIN USERS U ON M.UID = U.UID
                WHERE M.ROOM_ID = $1
                ORDER BY M.MESSAGE_ID DESC
                LIMIT $2;
                """,
                room_id,
                limit
            )

        else:
            records = await conn.fetch(
                """
                SELECT M.MESSAGE_ID,
                       M.UID,
                       U.NAME,
                       M.MESSAGE,
                       M.TIMESTAMP
                FROM MESSAGES M
                JOIN USERS U ON M.UID = U.UID
                WHERE M.ROOM_ID = $1
                  AND M.MESSAGE_ID < $2
                ORDER BY M.MESSAGE_ID DESC
                LIMIT $3;
                """,
                room_id,
                prev_id,
                limit
            )

        # Keep the same list/tuple-style result
        return [tuple(record) for record in records]

    except asyncpg.PostgresError as pe:
        logger.error(f"PostgreSQL error at get messages:{pe}")
        return None

    finally:
        if conn:
            await conn.close()

