from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.formatting import *

from datetime import datetime
import os
from dotenv import load_dotenv
from random import choice, randint
import sqlite3


load_dotenv()
router = Router()
BOT_TOKEN = os.getenv("TOKEN")
bot = Bot(token=BOT_TOKEN)

# @router.my_chat_member(F.chat.type.in_({"group", "supergroup"}))
# async def bot_added_or_removed(event: ChatMemberUpdated):
#     new_status = event.new_chat_member.statu
#     chat_id = event.chat.id
#
#     if new_status in ["member", "administrator"]:
#         pass
#
#
#     elif new_status in ["left", "kicked"]:
#         pass




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

# @router.message(Command("roll"))
# async def cmd_roll(message: Message):
#     if randint(1,2) == 1:
#         await message.reply(text='Лох, ты умер')
#     else:
#         await message.reply(text='Что ж, ты жив. Пока что.')


class Questionnaire(StatesGroup):
    waiting_for_name = State()
    waiting_for_bday = State()
    waiting_for_sex = State()


@router.message(Command("reg"))
async def cmd_reg(message: Message, state: FSMContext):
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    if sql.execute(f"""SELECT user_id from users WHERE user_id = {message.from_user.id}""").fetchone() is not None:
        await message.answer('Вы уже зарегестрированы в системе.')
        db.close()
    else:
        db.close()
        await message.answer("Привет! Для начала регистрации напиши, пожалуйста, своё имя и фамилию (Например: Иван Иванов).")
        await state.set_state(Questionnaire.waiting_for_name)

@router.message(Questionnaire.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    full_name = message.text
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
    try: datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer(f"Введи корректную дату в формате ДД.ММ.ГГГГ (Например: 17.01.2008).")
        await state.set_state(Questionnaire.waiting_for_bday)
    else:
        await state.update_data(bday=datetime.strptime(message.text, "%d.%m.%Y").date())

        await message.answer(f"Отлично, осталось указать пол. Укажи 1 - мужской, или 2 - женский.")
        await state.set_state(Questionnaire.waiting_for_sex)

@router.message(Questionnaire.waiting_for_sex)
async def process_sex(message: Message, state: FSMContext):
    if message.text != '1' and message.text != '2':
        await message.answer('Укажи свой пол: 1 — мужской, 2 — женский')
        await state.set_state(Questionnaire.waiting_for_sex)
    else:
        user_data = await state.get_data()
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")
        bday = user_data.get("bday")
        sex = ('Male' if message.text == '1' else 'Female')

        db = sqlite3.connect('/data/server.db')
        sql = db.cursor()
        sql.execute(F"""INSERT INTO users (user_id, username, first_name, last_name, sex, bday, group_id) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (message.from_user.id, message.from_user.username, first_name, last_name, sex, bday, message.chat.id))
        db.commit()
        db.close()
        await message.answer(f"Спасибо за ответы! Регистрация успешна)")
        await state.clear()


@router.message(Command("database"))
async def cmd_database(message: Message):
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    rows = sql.execute(f"SELECT * FROM users").fetchall()
    for row in rows:
        await message.answer(
            f'ID: {row[0]}\nUsername: {row[1]}\nИмя: {row[2]}\nФамилия: {row[3]}\nПол: {row[4]}\nДень рождения: {row[5]}')
    db.close()


@router.message(Command("search"))
async def cmd_search(message: Message):
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    username = message.text.split(' ')[-1]

    row = sql.execute(f"""SELECT * FROM users WHERE username = {username}""").fetchone()
    if row is None:
        await message.answer("Пользователь не найден.")
    else:
        await message.answer(
            f'ID: {row[0]}\nUsername: {row[1]}\nИмя: {row[2]}\nФамилия: {row[3]}\nПол: {row[4]}\nДень рождения: {row[5]}')
        db.close()


ITEMS_PER_PAGE = 5
class Pagination(CallbackData, prefix="pag"):
    page: int


async def get_users_page(page: int):
    offset = (page - 1) * ITEMS_PER_PAGE
    db = sqlite3.connect('/data/server.db')
    sql = db.cursor()
    users = sql.execute(
                "SELECT user_id, username FROM users LIMIT ? OFFSET ?", (ITEMS_PER_PAGE, offset)).fetchall()

    total_count = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return users, total_count

def get_pagination_keyboard(page: int, total_count: int):
    builder = InlineKeyboardBuilder()

    if page > 1:
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=Pagination(page=page - 1).pack()))

    if page * ITEMS_PER_PAGE < total_count:
        builder.add(InlineKeyboardButton(text="Вперед ➡️", callback_data=Pagination(page=page + 1).pack()))

    return builder.as_markup()


@router.message(F.text == "/users")
async def show_users(message: Message):
    page = 1
    users, total_count = await get_users_page(page)

    if not users:
        await message.answer("База данных пуста.")
        return

    text = f"📊 ", Bold('Список пользователей'), " (Страница {page}):\n\n"
    for user in users:
        text += f"🆔 {user[0]} — @{user[1]}\n"

    kb = get_pagination_keyboard(page, total_count)
    await message.answer(text, reply_markup=kb)


@router.callback_query(Pagination.filter())
async def process_pagination(callback: CallbackQuery, callback_data: Pagination):
    page = callback_data.page
    users, total_count = await get_users_page(page)

    text = f"📊 ", Bold('Список пользователей'), " (Страница {page}):\n\n"
    for user in users:
        text += f"🆔 {user[0]} — @{user[1]}\n"

    kb = get_pagination_keyboard(page, total_count)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()