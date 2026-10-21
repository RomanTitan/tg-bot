from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='1'), KeyboardButton(text='2')],
    [KeyboardButton(text='3'), KeyboardButton(text='4'), KeyboardButton(text='5')]
],                                              resize_keyboard=True)


inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Выстрелить', url='tg://user?id=d0bryna'), InlineKeyboardButton(text='Пас', url='tg://user?id=d0bryna')],
    [InlineKeyboardButton(text='Отмена', url='tg://user?id=d0bryna')]
])