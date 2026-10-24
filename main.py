import asyncio
import logging
from datetime import datetime
import os
import sqlite3

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from application.handlers import router

load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
bot = Bot(token=BOT_TOKEN,default_properties=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def check_birthdays_today():
    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    for user in sql.execute(F"""SELECT user_id, username, first_name, last_name, bday, sex FROM users""").fetchall():
        bday_object = datetime.strptime(user[4], "%Y-%m-%d").date()

        if bday_object.month == today.month and bday_object.day == today.day:
            if user[1] != None and user[1] != "":
                await bot.send_message(chat_id="-1003825546584",
                                       message_thread_id=3,
                                       text=f"{user[2]} {user[3]} (@{user[1]}) сегодня отмечает свой день рождения!🎊 Все срочно поздравляем 🎉")
            elif user[0] != None and user[0] != "":
                link = html.link('@'+user[2], f"tg://user?id={user[0]}")
                await bot.send_message(chat_id="-1003825546584",
                                       message_thread_id=3,
                                       text=f"{user[2]} {user[3]} ({link}) сегодня отмечает свой день рождения!🎊 Все срочно поздравляем 🎉", parse_mode=ParseMode.HTML)
            await bot.send_animation(chat_id="-1003825546584", animation='CgACAgQAAxkBAAICcWrYlN4B5EU8e0n3yrHSysak2qqIAAJSAwACtQ_FUFcodGqTLKyLPQQ')
            #await bot.send_message(chat_id="1848696190", text=f"Ало, {user[2]} {user[3]} сегодня др отмечает, поздравил быстро.")
    db.close()

@dp.startup()
async def on_startup():
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    sql.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                sex TEXT NOT NULL,
                bday DATETIME NOT NULL,
                group_id INTEGER,
                admin BOOLEAN not null DEFAULT false
            )""")
    db.commit()
    db.close()

async def main():
    dp.include_router(router)
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(check_birthdays_today, "cron", minute=39, hour=12)
    scheduler.start()

    await dp.start_polling(bot)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())