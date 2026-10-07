import os

import psycopg
import redis
from flask import Flask, request

app = Flask(__name__)


POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "flask_app")
POSTGRES_USER = os.getenv("POSTGRES_USER", "flask_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")


def get_db_connection():
    return psycopg.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True,
)

def init_db():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL
                )
                """
            )

        connection.commit()


@app.get("/")
def hello():
    visits = redis_client.incr("visits")

    return f"Ура, я считаю что-то: {visits}"


@app.get("/notes/add")
def add_note():
    text = request.args.get("text")

    if not text:
        return {"error": "text is required"}, 400

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO notes (text) VALUES (%s)",
                (text,),
            )

        connection.commit()

    return {"message": "note added", "text": text}


@app.get("/notes")
def get_notes():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, text FROM notes ORDER BY id"
            )
            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "text": row[1],
        }
        for row in rows
    ]


if __name__ == "__main__":
    init_db()

    app.run(host="0.0.0.0", port=8000)
