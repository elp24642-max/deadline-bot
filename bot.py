import asyncio
import logging
import os
import time
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from dotenv import load_dotenv

import db
from parse import TZ, USAGE, format_left, parse_add

load_dotenv()
dp = Dispatcher()

HELP = (
    "Я слежу за дедлайнами и напоминаю за сутки и за час.\n\n"
    "/add 25.11 18:00 Лабораторная по C: добавить\n"
    "/list: что висит\n"
    "/done 3: отметить сданным (номер из /list)\n"
    "/del 3: удалить\n\n"
    "Время можно не указывать, тогда дедлайн в 23:59."
)


@dp.message(Command("start", "help"))
async def start(message: Message):
    await message.answer(HELP)


@dp.message(Command("add"))
async def add(message: Message, command: CommandObject):
    try:
        title, due = parse_add(command.args or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    deadline_id = db.add(message.chat.id, title, int(due.timestamp()))
    await message.answer(
        f"Добавил #{deadline_id}: {title}, {due:%d.%m.%Y %H:%M}"
    )


@dp.message(Command("list"))
async def list_deadlines(message: Message):
    rows = db.active(message.chat.id)
    if not rows:
        await message.answer("Дедлайнов нет. Добавь: " + USAGE)
        return
    now = time.time()
    lines = [
        f"#{row['id']} {row['title']}: "
        f"{datetime.fromtimestamp(row['due_ts'], TZ):%d.%m %H:%M} "
        f"({format_left(row['due_ts'] - now)})"
        for row in rows
    ]
    await message.answer("\n".join(lines))


def parse_id(command):
    """Достаёт номер из '/done 3'. Возвращает None, если номера нет."""
    arg = (command.args or "").strip().lstrip("#")
    return int(arg) if arg.isdigit() else None


@dp.message(Command("done"))
async def done(message: Message, command: CommandObject):
    deadline_id = parse_id(command)
    if deadline_id is None:
        await message.answer("Укажи номер из /list, например: /done 3")
    elif db.mark_done(message.chat.id, deadline_id):
        await message.answer("Отметил как сданное. Молодец!")
    else:
        await message.answer("Не нашёл такой дедлайн.")


@dp.message(Command("del"))
async def delete(message: Message, command: CommandObject):
    deadline_id = parse_id(command)
    if deadline_id is None:
        await message.answer("Укажи номер из /list, например: /del 3")
    elif db.delete(message.chat.id, deadline_id):
        await message.answer("Удалил.")
    else:
        await message.answer("Не нашёл такой дедлайн.")


async def reminders(bot: Bot):
    """Раз в минуту проверяет базу и шлёт напоминания."""
    while True:
        now = time.time()
        for row in db.upcoming(int(now)):
            left = row["due_ts"] - now
            if left <= 3600 and not row["notified_hour"]:
                text, day, hour = f"Меньше часа: {row['title']}", 1, 1
            elif left <= 86400 and not row["notified_day"]:
                text, day, hour = f"Меньше суток: {row['title']} ({format_left(left)})", 1, 0
            else:
                continue
            try:
                await bot.send_message(row["chat_id"], text)
            except Exception:
                # Например, пользователь заблокировал бота: пропускаем, но не падаем
                logging.exception("Не удалось отправить напоминание #%s", row["id"])
            db.mark_notified(row["id"], day, hour)
        await asyncio.sleep(60)


async def main():
    logging.basicConfig(level=logging.INFO)
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Нет BOT_TOKEN. Скопируй .env.example в .env и вставь токен.")
    bot = Bot(token)
    reminder_task = asyncio.create_task(reminders(bot))
    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
