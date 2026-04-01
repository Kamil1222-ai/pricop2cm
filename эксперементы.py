import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

logging.basicConfig(level=logging.INFO)
try:
    session = AiohttpSession(timeout=60)

    bot = Bot(
        token="8323110038:AAHIz4DD3QiMLnaXapvcYxXQ8jvSwXzcZ2c",
        session=session,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    print("✅ Бот успешно создан!")

except Exception as e:
    print(f"❌ Ошибка при создании бота: {e}")
    print("Проверьте интернет-соединение и токен")
    exit(1)

dp = Dispatcher()

FOOD_DB = {
    # Мясо и птица
    "курица": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0},
    "говядина": {"calories": 250, "protein": 26, "fat": 16, "carbs": 0},
    "свинина": {"calories": 242, "protein": 27, "fat": 14, "carbs": 0},
    "индейка": {"calories": 135, "protein": 29, "fat": 1.5, "carbs": 0},

    # Рыба и морепродукты
    "рыба": {"calories": 120, "protein": 20, "fat": 4, "carbs": 0},
    "лосось": {"calories": 208, "protein": 20, "fat": 13, "carbs": 0},
    "тунец": {"calories": 144, "protein": 23, "fat": 5, "carbs": 0},

    # Крупы и зерновые
    "рис": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
    "гречка": {"calories": 110, "protein": 4.2, "fat": 1.1, "carbs": 21},
    "овсянка": {"calories": 88, "protein": 3.1, "fat": 1.8, "carbs": 15},
    "макароны": {"calories": 131, "protein": 5, "fat": 1, "carbs": 25},
    "хлеб": {"calories": 265, "protein": 8, "fat": 3.2, "carbs": 49},

    # Овощи
    "картофель": {"calories": 77, "protein": 2, "fat": 0.4, "carbs": 17},
    "морковь": {"calories": 41, "protein": 0.9, "fat": 0.2, "carbs": 10},
    "огурец": {"calories": 15, "protein": 0.7, "fat": 0.1, "carbs": 2.5},
    "помидор": {"calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 3.9},
    "капуста": {"calories": 25, "protein": 1.3, "fat": 0.1, "carbs": 5},

    # Фрукты
    "банан": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23},
    "яблоко": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
    "апельсин": {"calories": 47, "protein": 0.9, "fat": 0.1, "carbs": 12},

    # Молочные продукты
    "молоко": {"calories": 60, "protein": 3.2, "fat": 3.2, "carbs": 4.8},
    "сыр": {"calories": 350, "protein": 25, "fat": 27, "carbs": 0},
    "творог": {"calories": 121, "protein": 18, "fat": 5, "carbs": 3},
    "йогурт": {"calories": 59, "protein": 3.5, "fat": 0.5, "carbs": 10},

    # Яйца
    "яйцо": {"calories": 155, "protein": 13, "fat": 11, "carbs": 0.7},

    # Масла
    "масло сливочное": {"calories": 748, "protein": 0.5, "fat": 82.5, "carbs": 0.8},
    "масло оливковое": {"calories": 884, "protein": 0, "fat": 100, "carbs": 0},
    "масло подсолнечное": {"calories": 899, "protein": 0, "fat": 99.9, "carbs": 0},
}


# ========== ФУНКЦИИ ДЛЯ РАСЧЕТА ==========

def parse_food_description(text: str):
    """Разбирает текст описания блюда. Пример: "150г курицы, 100г риса" """
    pattern = r'(\d+)\s*[г]?\s*([а-яё\s]+)'
    matches = re.findall(pattern, text.lower())

    result = []
    for weight, food in matches:
        food = food.strip()
        found = False
        for db_food in FOOD_DB:
            if db_food in food or food in db_food:
                result.append((db_food, int(weight)))
                found = True
                break
        if not found:
            result.append((food, int(weight)))

    return result


def calculate_nutrition(foods):
    """Рассчитывает суммарное КБЖУ для списка продуктов"""
    total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    unknown_foods = []

    for food_name, weight in foods:
        if food_name in FOOD_DB:
            data = FOOD_DB[food_name]
            ratio = weight / 100
            total["calories"] += data["calories"] * ratio
            total["protein"] += data["protein"] * ratio
            total["fat"] += data["fat"] * ratio
            total["carbs"] += data["carbs"] * ratio
        else:
            unknown_foods.append(food_name)

    return total, unknown_foods


# ========== КЛАВИАТУРЫ ==========

def get_main_keyboard():
    """Главная клавиатура"""
    button_start = KeyboardButton(text="start")
    button_help = KeyboardButton(text="help")
    button_info = KeyboardButton(text="info")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_start, button_help, button_info]],
        resize_keyboard=True
    )
    return keyboard


def get_dva_keyboard():
    """Вторая клавиатура - выбор цели"""
    button_hud = KeyboardButton(text="Сбросить вес")
    button_nab = KeyboardButton(text="Набрать вес")
    button_back = KeyboardButton(text="Назад")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button_hud, button_nab],
            [button_back]
        ],
        resize_keyboard=True
    )
    return keyboard


# ========== ОБРАБОТЧИКИ ==========

@dp.message(Command('start'))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    keyboard = get_main_keyboard()
    await message.answer(
        'Привет, это бот для определения калорий.\nВыбери нужную тебе задачу:',
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "start")
async def button_start(message: Message):
    """Обработчик нажатия на кнопку start"""
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
    await message.answer('🤖 Информация о боте: версия 1.0, умеет определять калории в еде')


# ========== ГЛАВНЫЙ ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ (включая расчет КБЖУ) ==========
@dp.message()
async def handle_food_description(message: Message):
    """Обработчик описания блюда - парсит и считает КБЖУ"""

    # Список кнопок, которые НЕ нужно обрабатывать
    buttons = ["start", "help", "info", "Сбросить вес", "Набрать вес", "Назад"]

    # Если это кнопка - пропускаем (они уже обработаны выше)
    if message.text in buttons:
        return

    user_text = message.text

    # 1. Парсим описание
    foods = parse_food_description(user_text)

    if not foods:
        await message.answer(
            "❓ Не могу распознать продукты. Попробуй написать так:\n\n"
            "📝 **Примеры:**\n"
            "• 150г курицы, 100г риса\n"
            "• 2 яйца, 50г овсянки\n"
            "• 100г творога, 1 банан\n\n"
            "Указывай вес в граммах (г) или просто цифрой.",
            parse_mode="Markdown"
        )
        return

    # 2. Рассчитываем КБЖУ
    total, unknown = calculate_nutrition(foods)

    # 3. Формируем ответ
    response = "🍽️ **Результат расчета:**\n\n"

    for food_name, weight in foods:
        if food_name in FOOD_DB:
            data = FOOD_DB[food_name]
            ratio = weight / 100
            response += f"• {food_name.capitalize()} ({weight}г): "
            response += f"{int(data['calories'] * ratio)} ккал, "
            response += f"{data['protein'] * ratio:.1f}г белков\n"
        else:
            response += f"• {food_name.capitalize()} ({weight}г): ❓ не найден в базе\n"

    response += f"\n📊 **Итого:**\n"
    response += f"🔥 Калории: {int(total['calories'])} ккал\n"
    response += f"💪 Белки: {total['protein']:.1f} г\n"
    response += f"🧈 Жиры: {total['fat']:.1f} г\n"
    response += f"🍚 Углеводы: {total['carbs']:.1f} г\n"

    if unknown:
        response += f"\n⚠️ Не найдены в базе: {', '.join(unknown)}"

    # Добавляем рекомендацию
    if total['protein'] < 20:
        response += f"\n\n💡 **Совет:** Добавьте больше белка (курица, рыба, яйца) для насыщения!"
    elif total['carbs'] > 60:
        response += f"\n\n💡 **Совет:** Для баланса можно добавить больше овощей!"

    await message.answer(response, parse_mode="Markdown")


# ========== ЗАПУСК ==========
async def main():
    logging.info("Бот запущен!")
    print("🚀 Бот работает! Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())