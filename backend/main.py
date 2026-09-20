"""
Habit Tracker API
------------------
Простой бэкенд на FastAPI для трекера привычек.
Хранилище — SQLite (файл habits.db создаётся автоматически рядом с этим файлом).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).parent / "habits.db"

app = FastAPI(title="Habit Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Работа с базой данных
# --------------------------------------------------------------------------

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT NOT NULL DEFAULT '⭐',
                color TEXT NOT NULL DEFAULT '#6C5CE7',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                checkin_date TEXT NOT NULL
            )
            """
        )


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# --------------------------------------------------------------------------
# Модели
# --------------------------------------------------------------------------

class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    icon: str = Field(default="⭐", max_length=8)
    color: str = Field(default="#6C5CE7", max_length=16)


class HabitUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    icon: str = Field(default="⭐", max_length=8)
    color: str = Field(default="#6C5CE7", max_length=16)


class HabitOut(BaseModel):
    id: int
    name: str
    icon: str
    color: str
    created_at: str
    done_today: bool
    streak: int
    completion_rate: float
    total_checkins: int


class StatsOut(BaseModel):
    total_habits: int
    total_checkins: int
    best_streak: int
    done_today_count: int


# --------------------------------------------------------------------------
# Вспомогательная логика (расчёт стриков / процента выполнения)
# --------------------------------------------------------------------------

def _parse_dates(rows) -> List[date]:
    return [datetime.strptime(r["checkin_date"], "%Y-%m-%d").date() for r in rows]


def calc_streak(checkin_dates: List[date]) -> int:
    """Считает текущий стрик привычки (число дней подряд)."""
    if not checkin_dates:
        return 0

    unique_dates = sorted(set(checkin_dates))
    today = date.today()
    last = unique_dates[-1]

    # Если последняя отметка была больше суток назад — стрик прерван.
    if (today - last).days > 1:
        return 0

    streak = 1
    for i in range(len(unique_dates) - 1, 0, -1):
        diff = (unique_dates[i] - unique_dates[i - 1]).days
        if diff == 1:
            streak += 1
        else:
            break

    if last != today:
        streak += 1

    return streak


def calc_completion_rate(created_at: date, checkin_dates: List[date]) -> float:
    """Считает процент выполнения привычки с момента её создания."""
    days_since_created = (date.today() - created_at).days
    if days_since_created == 0:
        days_since_created = 1

    rate = len(checkin_dates) / days_since_created * 100
    return round(rate, 1)


def _habit_to_out(row: sqlite3.Row, checkin_rows) -> HabitOut:
    dates = _parse_dates(checkin_rows)
    today = date.today()
    created_at = datetime.strptime(row["created_at"], "%Y-%m-%d").date()

    return HabitOut(
        id=row["id"],
        name=row["name"],
        icon=row["icon"],
        color=row["color"],
        created_at=row["created_at"],
        done_today=today in dates,
        streak=calc_streak(dates),
        completion_rate=calc_completion_rate(created_at, dates),
        total_checkins=len(checkin_rows),
    )


# --------------------------------------------------------------------------
# Эндпоинты
# --------------------------------------------------------------------------

@app.get("/api/habits", response_model=List[HabitOut])
def list_habits():
    with get_db() as conn:
        habits = conn.execute("SELECT * FROM habits ORDER BY created_at ASC, id ASC").fetchall()
        result = []
        for h in habits:
            checkins = conn.execute(
                "SELECT * FROM checkins WHERE habit_id = ?", (h["id"],)
            ).fetchall()
            result.append(_habit_to_out(h, checkins))
        return result


@app.post("/api/habits", response_model=HabitOut, status_code=201)
def create_habit(payload: HabitCreate):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO habits (name, icon, color, created_at) VALUES (?, ?, ?, ?)",
            (payload.name.strip(), payload.icon, payload.color, date.today().isoformat()),
        )
        habit_id = cur.lastrowid
        h = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        return _habit_to_out(h, [])


@app.put("/api/habits/{habit_id}", response_model=HabitOut)
def update_habit(habit_id: int, payload: HabitUpdate):
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Привычка не найдена")

        conn.execute(
            "UPDATE habits SET name = ?, icon = ?, color = ? WHERE id = ?",
            (payload.name.strip(), payload.icon, payload.color, habit_id),
        )
        h = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        checkins = conn.execute(
            "SELECT * FROM checkins WHERE habit_id = ?", (habit_id,)
        ).fetchall()
        return _habit_to_out(h, checkins)


@app.delete("/api/habits/{habit_id}", status_code=204)
def delete_habit(habit_id: int):
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Привычка не найдена")
        conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    return None


@app.post("/api/habits/{habit_id}/checkins", response_model=HabitOut)
def add_checkin(habit_id: int):
    with get_db() as conn:
        h = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if not h:
            raise HTTPException(status_code=404, detail="Привычка не найдена")

        today_str = date.today().isoformat()
        conn.execute(
            "INSERT INTO checkins (habit_id, checkin_date) VALUES (?, ?)",
            (habit_id, today_str),
        )
        checkins = conn.execute(
            "SELECT * FROM checkins WHERE habit_id = ?", (habit_id,)
        ).fetchall()
        return _habit_to_out(h, checkins)


@app.delete("/api/habits/{habit_id}/checkins/{checkin_date}", response_model=HabitOut)
def remove_checkin(habit_id: int, checkin_date: str):
    with get_db() as conn:
        h = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if not h:
            raise HTTPException(status_code=404, detail="Привычка не найдена")

        conn.execute(
            "DELETE FROM checkins WHERE habit_id = ? AND checkin_date = ?",
            (habit_id, checkin_date),
        )
        checkins = conn.execute(
            "SELECT * FROM checkins WHERE habit_id = ?", (habit_id,)
        ).fetchall()
        return _habit_to_out(h, checkins)


@app.get("/api/stats", response_model=StatsOut)
def get_stats():
    with get_db() as conn:
        total_habits = conn.execute("SELECT COUNT(*) AS c FROM habits").fetchone()["c"]
        total_checkins = conn.execute("SELECT COUNT(*) AS c FROM checkins").fetchone()["c"]

        habits = conn.execute("SELECT * FROM habits").fetchall()
        best_streak = 0
        done_today_count = 0
        today = date.today()

        for h in habits:
            checkins = conn.execute(
                "SELECT * FROM checkins WHERE habit_id = ?", (h["id"],)
            ).fetchall()
            dates = _parse_dates(checkins)
            streak = calc_streak(dates)
            best_streak = max(best_streak, streak)
            if today in dates:
                done_today_count += 1

        return StatsOut(
            total_habits=total_habits,
            total_checkins=total_checkins,
            best_streak=best_streak,
            done_today_count=done_today_count,
        )


@app.get("/api/health")
def health():
    return {"status": "ok"}
