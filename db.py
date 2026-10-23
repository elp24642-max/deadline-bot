import sqlite3

conn = sqlite3.connect("deadlines.db")
conn.row_factory = sqlite3.Row
conn.execute(
    """CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        due_ts INTEGER NOT NULL,
        notified_day INTEGER NOT NULL DEFAULT 0,
        notified_hour INTEGER NOT NULL DEFAULT 0,
        done INTEGER NOT NULL DEFAULT 0
    )"""
)


def add(chat_id, title, due_ts):
    cur = conn.execute(
        "INSERT INTO deadlines (chat_id, title, due_ts) VALUES (?, ?, ?)",
        (chat_id, title, due_ts),
    )
    conn.commit()
    return cur.lastrowid


def active(chat_id):
    return conn.execute(
        "SELECT * FROM deadlines WHERE chat_id = ? AND done = 0 ORDER BY due_ts",
        (chat_id,),
    ).fetchall()


def mark_done(chat_id, deadline_id):
    """Помечает сданным. chat_id в условии не даёт трогать чужие записи."""
    cur = conn.execute(
        "UPDATE deadlines SET done = 1 WHERE id = ? AND chat_id = ? AND done = 0",
        (deadline_id, chat_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete(chat_id, deadline_id):
    cur = conn.execute(
        "DELETE FROM deadlines WHERE id = ? AND chat_id = ?", (deadline_id, chat_id)
    )
    conn.commit()
    return cur.rowcount > 0


def upcoming(now_ts):
    """Несданные дедлайны, которые ещё не наступили."""
    return conn.execute(
        "SELECT * FROM deadlines WHERE done = 0 AND due_ts > ?", (now_ts,)
    ).fetchall()


def mark_notified(deadline_id, day, hour):
    conn.execute(
        "UPDATE deadlines SET notified_day = ?, notified_hour = ? WHERE id = ?",
        (day, hour, deadline_id),
    )
    conn.commit()
