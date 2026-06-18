import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
logging.basicConfig(level=logging.INFO)
ELEGRAM_TOKEN = "8882016017:AAGC9yaMbfKAEw3AbGDVzxjStzqyygXj1Uw"
def get_main_keyboard():
    button_start = KeyboardButton(text="start")
    button_help = KeyboardButton(text="help")
    button_info = KeyboardButton(text="info")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_start, button_help, button_info]],
        resize_keyboard=True
    )
    return keyboard


def get_dva_keyboard():
    button_hud = KeyboardButton(text="Сбросить вес")
    button_nab = KeyboardButton(text="Набрать вес")
    button_back = KeyboardButton(text="Назад")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_hud, button_nab], [button_back]],
        resize_keyboard=True
    )
    return keyboard


# ========== ОБРАБОТЧИКИ КНОПОК ==========
@dp.message(Command('start'))
async def cmd_start(message: Message):
    keyboard = get_main_keyboard()
    await message.answer(
        'Привет, это бот для определения калорий.\nВыбери нужную тебе задачу:',
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "start")
async def button_start(message: Message):
    keyboard = get_dva_keyboard()
    await message.answer(
        'Бот для определения калорий готов к работе!\n\nВыбери свою цель:',
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == 'Сбросить вес')
async def button_sb(message: Message):
    await message.answer(
        "📝 Опиши состав своего блюда (например: 150г курицы, 100г риса)",
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == 'Набрать вес')
async def button_nb(message: Message):
    await message.answer(
        "📝 Опиши состав своего блюда (например: 150г курицы, 100г риса)",
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == 'Назад')
async def button_back(message: Message):
    keyboard = get_main_keyboard()
    await message.answer(
        "🔙 Назад в главное меню",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "help")
async def button_help(message: Message):
    await message.answer(
        'ℹ️ **Как пользоваться ботом:**\n\n'
        '1. Нажми кнопку "start"\n'
        '2. Выбери цель: "Сбросить вес" или "Набрать вес"\n'
        '3. Опиши состав блюда (например: 150г курицы, 100г риса)\n'
        '4. Бот рассчитает калорийность\n\n'
        '**Доступные продукты:**\n'
        '• Мясо: курица, говядина, свинина, индейка\n'
        '• Крупы: рис, гречка, овсянка, макароны\n'
        '• Овощи: картофель, морковь, огурец, помидор\n'
        '• Фрукты: банан, яблоко, апельсин\n'
        '• Молочка: молоко, сыр, творог, йогурт\n'
        '• Яйца, масла и другие продукты',
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == "info")
async def button_info(message: Message):
    await message.answer('🤖 Информация о боте: версия 2.0, умеет определять калории в еде и блюдах')


# ========== ГЛАВНЫЙ УМНЫЙ ОБРАБОТЧИК ==========
@dp.message()
async def handle_user_input(message: Message):
    user_text = message.text.strip()

    buttons = ["start", "help", "info", "Сбросить вес", "Набрать вес", "Назад"]
    if user_text in buttons:
        return