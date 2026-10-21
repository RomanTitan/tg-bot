from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, user, ChatMemberUpdated
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from datetime import datetime
from random import choice, randint
import config
import sqlite3

router = Router()
bot = Bot(token=config.BOT_TOKEN)

@router.my_chat_member(F.chat.type.in_({"group", "supergroup"}))
async def bot_added_or_removed(event: ChatMemberUpdated):
    new_status = event.new_chat_member.status
    chat_id = event.chat.id

    if new_status in ["member", "administrator"]:
        pass


    elif new_status in ["left", "kicked"]:
        pass




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
    db = sqlite3.connect('../data/server_test.db')
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

        db = sqlite3.connect('../data/server_test.db')
        sql = db.cursor()
        sql.execute(F"""INSERT INTO users (user_id, username, first_name, last_name, sex, bday, group_id) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (message.from_user.id, message.from_user.username, first_name, last_name, sex, bday, message.chat.id))
        db.commit()
        db.close()
        await message.answer(f"Спасибо за ответы! Регистрация успешна)")
        await state.clear()


@router.message(Command("database"))
async def cmd_database(message: Message):
    db = sqlite3.connect('../data/server_test.db')
    sql = db.cursor()
    rows = sql.execute(f"SELECT * FROM users").fetchall()
    for row in rows:
        await message.answer(
            f'ID: {row[0]}\nUsername: {row[1]}\nИмя: {row[2]}\nФамилия: {row[3]}\nПол: {row[4]}\nДень рождения: {row[5]}')
    db.close()


@router.message(Command("search"))
async def cmd_search(message: Message):
    db = sqlite3.connect('../data/server_test.db')
    sql = db.cursor()
    username = message.text.split(' ')[-1]

    row = sql.execute(f"""SELECT * FROM users WHERE username = {username}""").fetchone()
    if row is None:
        await message.answer("Пользователь не найден.")
    else:
        await message.answer(
            f'ID: {row[0]}\nUsername: {row[1]}\nИмя: {row[2]}\nФамилия: {row[3]}\nПол: {row[4]}\nДень рождения: {row[5]}')
        db.close()