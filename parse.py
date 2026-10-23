import re
from datetime import datetime, timedelta, timezone

# Ульяновск: UTC+4. Если бот запускают в другом поясе, поменяй число часов.
TZ = timezone(timedelta(hours=4))

# "25.11 18:00 Лабораторная", "25.11.2026 Отчёт" (время по умолчанию 23:59)
PATTERN = re.compile(
    r"^(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?"  # день.месяц[.год]
    r"(?:\s+(\d{1,2}):(\d{2}))?"            # необязательное время
    r"\s+(.+)$"                              # название
)

USAGE = "Формат: /add 25.11 18:00 Лабораторная по C (время можно не указывать)"


def parse_add(text, now=None):
    """Разбирает текст команды /add. Возвращает (название, дедлайн с поясом)."""
    now = now or datetime.now(TZ)
    match = PATTERN.match(text.strip())
    if not match:
        raise ValueError(USAGE)

    day, month, year, hour, minute, title = match.groups()
    try:
        due = datetime(
            int(year) if year else now.year,
            int(month),
            int(day),
            int(hour) if hour else 23,
            int(minute) if minute else 59,
            tzinfo=TZ,
        )
        # Год не указан и дата уже прошла: значит, имеется в виду следующий год
        if not year and due < now:
            due = due.replace(year=due.year + 1)
    except ValueError:
        raise ValueError("Такой даты не существует. " + USAGE)
    return title.strip(), due


def format_left(seconds):
    """Остаток времени человеческим языком: '2 д 3 ч', '45 мин', 'просрочено'."""
    if seconds <= 0:
        return "просрочено"
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days} д {hours} ч"
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"
