import sqlite3
from pathlib import Path

DB_PATH = Path("events.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery_id TEXT NOT NULL,
            event TEXT NOT NULL,
            action TEXT,
            issue_number INTEGER,
            timestamp TEXT NOT NULL,
            UNIQUE(delivery_id, action)
        )
        """
    )

    conn.commit()
    conn.close()


def save_event(
    delivery_id: str,
    event: str,
    action: str | None,
    issue_number: int | None,
    timestamp: str,
):
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute(
            """
            INSERT INTO events (
                delivery_id,
                event,
                action,
                issue_number,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                delivery_id,
                event,
                action,
                issue_number,
                timestamp,
            ),
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def get_events(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            delivery_id,
            event,
            action,
            issue_number,
            timestamp
        FROM events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]
