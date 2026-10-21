import asyncio
import logging
from datetime import datetime
import os

import sqlite3

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, F

from application.handlers import router

BOT_TOKEN = os.getenv("TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def check_birthdays_today():
    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    db = sqlite3.connect('data/server_test.db')
    sql = db.cursor()
    for user in sql.execute(F"""SELECT user_id, username, first_name, bday FROM users""").fetchall():
        bday_object = datetime.strptime(user[3], "%Y-%m-%d").date()

        if bday_object.month == today.month and bday_object.day == today.day:
            await bot.send_message(chat_id="-5534575983", text=f"{user[2]} (@{user[1]}) сегодня отмечает свой день рождения! Все срочно поздравляем!!!")
            await bot.send_animation(chat_id="-5534575983", animation='CgACAgQAAxkBAAICcWrYlN4B5EU8e0n3yrHSysak2qqIAAJSAwACtQ_FUFcodGqTLKyLPQQ')
            await bot.send_message(chat_id="1848696190", text=f"Ало, {user[2]} (@{user[1]}) сегодня др отмечает, поздравил быстро.")
    db.close()

@dp.startup()
async def on_startup():
    db = sqlite3.connect('data/server_test.db')
    sql = db.cursor()
    sql.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                sex TEXT NOT NULL,
                bday DATETIME NOT NULL,
                group_id INTEGER
            )""")
    db.commit()
    db.close()

async def main():
    dp.include_router(router)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_birthdays_today, "interval", seconds=60)

    scheduler.start()
    await dp.start_polling(bot)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
