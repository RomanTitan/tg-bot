from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.formatting import *

import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from random import choice, randint
import sqlite3

from application.keyboard import inline

load_dotenv()
router = Router()
BOT_TOKEN = os.getenv("TOKEN")
bot = Bot(token=BOT_TOKEN)
months = ['', 'января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

@router.message(Command("info"))
async def cmd_info(message: Message):
    me = await bot.get_me()
    await message.answer(
        "Информация о боте:\n"
        f"ID: {me.id}\n"
        f"Имя: {me.first_name}\n"
        f"Username: @{me.username}\n"
        f"Chat ID: {message.chat.id}\n"
        f"User ID: {message.from_user.id}"
    )

class Questionnaire(StatesGroup):
    waiting_for_name = State()
    waiting_for_bday = State()
    waiting_for_sex = State()


@router.message(Command("reg"))
async def cmd_reg(message: Message, state: FSMContext):
    try: await message.delete()
    except:
        pass
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    if sql.execute(f"""SELECT user_id from users WHERE user_id = {message.from_user.id}""").fetchone() is not None:
        msg = await message.answer('Вы уже зарегестрированы в системе.')
        db.close()
        await asyncio.sleep(3)
        await msg.delete()
    else:
        db.close()
        await message.answer("Привет! Для начала регистрации напиши, пожалуйста, своё имя и фамилию (Например: Иван Иванов).")
        await state.update_data(user_id=message.from_user.id,
                                username=message.from_user.username,
                                group_id=message.chat.id)
        await state.set_state(Questionnaire.waiting_for_name)

@router.message(Questionnaire.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    full_name = message.text
    await message.delete()
    name_parts = full_name.split(maxsplit=1)
    first_name = name_parts[0] if len(name_parts) > 0 else full_name
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    if last_name == "":
        await message.answer(f"{first_name}, нужно написать не только имя, а ещё и фамилию. Например: Иван Иванов.")
        await state.set_state(Questionnaire.waiting_for_name)
    else:
        await state.update_data(first_name=first_name, last_name=last_name)
        await message.answer(f"Приятно познакомиться, {first_name}! Укажи, пожалуйста, свою дату рождения в формте ДД.ММ.ГГГГ (Например: 17.01.2008).")
        await state.set_state(Questionnaire.waiting_for_bday)


@router.message(Questionnaire.waiting_for_bday)
async def process_bday(message: Message, state: FSMContext):
    await message.delete()
    try: datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer(f"Введи корректную дату в формате ДД.ММ.ГГГГ (Например: 17.01.2008).")
        await state.set_state(Questionnaire.waiting_for_bday)
    else:
        await state.update_data(bday=datetime.strptime(message.text, "%d.%m.%Y"))

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text='Мужской', callback_data='Male'))
        builder.add(InlineKeyboardButton(text='Женский', callback_data='Female'))

        await message.answer(f"Отлично, осталось указать пол.", reply_markup=builder.as_markup())


@router.callback_query(F.data.in_(["Male", "Female"]))
async def process_sex(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get('user_id')
    username = user_data.get('username')
    group_id = user_data.get('group_id')
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")
    bday = user_data.get("bday")
    sex = callback.data
    sex_ = ('Мужской' if sex == "Male" else 'Женский')
    await state.update_data(sex=sex)

    text = (F"Проверь свои данные:\n\n"
            F"Имя: {first_name}\n"
            F"Фамилия: {last_name}\n"
            F"Username: {username}\n"
            F"Пол: {sex_}\n"
            F"День рождения: {bday.date().day} {months[bday.date().month]}")

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text='Верно', style='Success', callback_data='Correct'))
    builder.add(InlineKeyboardButton(text='Заполнить заново', style='Danger', callback_data='Incorrect'))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.in_(["Correct", "Incorrect", 'Correct_check']))
async def process_correct(callback: CallbackQuery, state: FSMContext):
    if callback.data == "Correct":
        user_data = await state.get_data()
        user_id = user_data.get('user_id')
        username = user_data.get('username')
        bday = user_data.get("bday")
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")
        group_id = user_data.get("group_id")
        sex = user_data.get('sex')

        db = sqlite3.connect('/data/server.db')
        sql = db.cursor()
        sql.execute(F"""INSERT INTO users (user_id, username, first_name, last_name, sex, bday, group_id) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, sex, bday, group_id))
        db.commit()
        db.close()

        await callback.message.edit_text("Регистрация успешна.", reply_markup=None)
    elif callback.data == "Correct_check":
        if datetime.astimezone('Europe/Moscow').hour < 16:
            await callback.message.edit_text('Отлично, спасибо тебе за проверку данных, хорошего дня 😊')
        else:
            await callback.message.edit_text('Отлично, спасибо тебе за проверку данных, хорошего вечера 😊')
    else:
        await callback.message.edit_text('Пожалуйста, используй команду /reg для повторной регистриации.')
        await asyncio.sleep(3)
        await callback.message.delete()
    await state.clear()


# @router.message(Command("database"))
# async def cmd_database(message: Message):
#     db = sqlite3.connect('/data/server.db')
#     sql = db.cursor()
#     rows = sql.execute(f"SELECT * FROM users").fetchall()
#     for row in rows:
#         await message.answer(
#             f'ID: {row[0]}\nUsername: {row[1]}\nИмя: {row[2]}\nФамилия: {row[3]}\nПол: {row[4]}\nДень рождения: {row[5]}')
#     db.close()
#

# @router.message(Command("search"))
# async def cmd_search(message: Message):
#     db = sqlite3.connect('/data/server.db')
#     sql = db.cursor()
#     username = message.text.split(' ')[-1]
#
#     row = sql.execute(f"""SELECT * FROM users WHERE username = {username}""").fetchone()
#     if row is None:
#         await message.answer("Пользователь не найден.")
#     else:
#         await message.answer(
#             f'ID: {row[0]}\nUsername: {row[1]}\nИмя: {row[2]}\nФамилия: {row[3]}\nПол: {row[4]}\nДень рождения: {row[5]}')
#         db.close()


ITEMS_PER_PAGE = 5
class Pagination(CallbackData, prefix="pag"):
    page: int

async def get_users_page(page: int):
    offset = (page - 1) * ITEMS_PER_PAGE
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    users = sql.execute(
                "SELECT first_name, last_name, bday FROM users LIMIT ? OFFSET ?", (ITEMS_PER_PAGE, offset)).fetchall()

    total_count = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return users, total_count

def get_pagination_keyboard(page: int, total_count: int):
    builder = InlineKeyboardBuilder()

    if page > 1:
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=Pagination(page=page - 1).pack()))

    if page * ITEMS_PER_PAGE < total_count:
        builder.add(InlineKeyboardButton(text="Вперед ➡️", callback_data=Pagination(page=page + 1).pack()))


    builder.row(InlineKeyboardButton(text="Выйти", callback_data='delete_message', style="danger"))
    return builder.as_markup()


@router.message(F.text == "/users")
async def show_users(message: Message):
    await message.delete()
    page = 1
    users, total_count = await get_users_page(page)

    if not users:
        await message.answer("База данных пуста.")
        return

    text = f"📊 Список пользователей (Страница {page}/{total_count//ITEMS_PER_PAGE}):\n\n"
    for user in users:
        text += f"👤{user[0]} {user[1]} — 🎂{user[2]}\n"

    kb = get_pagination_keyboard(page, total_count)
    await message.answer(text, reply_markup=kb)

@router.callback_query(lambda query: query.data == "delete_message")
async def delete_message(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@router.callback_query(Pagination.filter())
async def process_pagination(callback: CallbackQuery, callback_data: Pagination):
    page = callback_data.page
    users, total_count = await get_users_page(page)

    text = f"📊 Список пользователей (Страница {page}/{total_count//ITEMS_PER_PAGE}):\n\n"
    for user in users:
        text += f"👤{user[0]} {user[1]} — 🎂{user[2]}\n"

    kb = get_pagination_keyboard(page, total_count)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.message(CommandStart)
async def cmd_start(message: Message, state: FSMContext):
    await message.delete()
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    user = sql.execute("SELECT * FROM users WHERE user_id = ? OR username = ?", (message.from_user.id, message.from_user.username)).fetchone()
    if user == None or user[1] == "" or user[1] == None:
        await cmd_reg(message=message, state=state)
        return
    elif user[0] == "" or user[0] == None:
        sql.execute("UPDATE users SET user_id = ? WHERE username = ?", (message.from_user.id, message.from_user.username))
        db.commit()

    user_id = message.from_user.id
    sex = ('Мужской' if user[4] == 'Male' else 'Женский')
    bday = datetime.strptime(user[5], "%d.%m.%Y").date()
    text = (f"👤Ваши данные:\n\n"
            f"ID: {user_id}\n"
            f"Username: @{user[1]}\n"
            f"Имя Фамилия: {user[2]} {user[3]}\n"
            f"Пол: {sex}\n"
            f"День рождения: {bday.day} {months[bday.month]} {bday.year} года")

    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text='Верно', style='Success', callback_data='Correct_check'))
    kb.add(InlineKeyboardButton(text='Заполнить заново', style='Danger', callback_data='Incorrect'))

    await message.answer(text, reply_markup=kb)

