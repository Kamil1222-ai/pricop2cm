import asyncio
import logging
import re
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(level=logging.INFO)

# ========== СОЗДАНИЕ БОТА ==========
try:
    session = AiohttpSession(timeout=60)

    # ⚠️ ЗАМЕНИТЕ НА НОВЫЙ ТОКЕН!
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


# ========== БАЗА ДАННЫХ ==========

def init_db():
    """Создает таблицу для хранения записей питания"""
    conn = sqlite3.connect('food_log.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            description TEXT,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL
        )
    ''')
    conn.commit()
    conn.close()


def save_food_entry(user_id, description, nutrition):
    """Сохраняет запись о приеме пищи"""
    conn = sqlite3.connect('food_log.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO food_entries (user_id, date, description, calories, protein, fat, carbs)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        datetime.now().strftime("%Y-%m-%d"),
        description,
        nutrition["calories"],
        nutrition["protein"],
        nutrition["fat"],
        nutrition["carbs"]
    ))
    conn.commit()
    conn.close()


def get_today_stats(user_id):
    """Получает статистику питания за сегодня"""
    conn = sqlite3.connect('food_log.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(calories), SUM(protein), SUM(fat), SUM(carbs), COUNT(*)
        FROM food_entries
        WHERE user_id = ? AND date = ?
    ''', (user_id, datetime.now().strftime("%Y-%m-%d")))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        return {
            "calories": result[0],
            "protein": result[1],
            "carbs": result[3],
            "fat": result[2],
            "count": result[4]
        }
    return None


# ========== БАЗА ПРОДУКТОВ ==========
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
    """
    Разбирает текст описания блюда
    Пример: "150г курицы, 100г риса"
    Возвращает список кортежей (название, вес)
    """
    pattern = r'(\d+)\s*[г]?\s*([а-яё\s]+)'
    matches = re.findall(pattern, text.lower())

    result = []
    for weight, food in matches:
        food = food.strip()
        # Ищем похожее название в базе
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
    """
    Рассчитывает суммарное КБЖУ для списка продуктов
    """
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
    """Главная клавиатура с кнопками start, help, info"""
    button_start = KeyboardButton(text="start")
    button_help = KeyboardButton(text="help")
    button_info = KeyboardButton(text="info")
    button_stats = KeyboardButton(text="📊 Статистика")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button_start, button_help, button_info],
            [button_stats]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_dva_keyboard():
    """Вторая клавиатура - выбор цели (сбросить/набрать вес)"""
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
    init_db()  # Создаем базу данных при старте


@dp.message(lambda message: message.text == "start")
async def button_start(message: Message):
    """Обработчик нажатия на кнопку start - показывает выбор цели"""
    keyboard = get_dva_keyboard()
    await message.answer(
        '🎯 Бот для определения калорий готов к работе!\n\n'
        'Выбери свою цель:',
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "📊 Статистика")
async def button_stats(message: Message):
    """Показывает статистику питания за сегодня"""
    stats = get_today_stats(message.from_user.id)

    if stats:
        await message.answer(
            f"📊 **Статистика питания за сегодня:**\n\n"
            f"🍽️ Приемов пищи: {stats['count']}\n"
            f"🔥 Калории: {int(stats['calories'])} ккал\n"
            f"💪 Белки: {stats['protein']:.1f} г\n"
            f"🧈 Жиры: {stats['fat']:.1f} г\n"
            f"🍚 Углеводы: {stats['carbs']:.1f} г\n\n"
            f"💡 Совет: Для здорового питания старайтесь распределять калории равномерно в течение дня.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "📊 За сегодня еще нет записей о питании.\n\n"
            "Нажми 'start', выбери цель и опиши свой прием пищи!"
        )


@dp.message(lambda message: message.text == 'Сбросить вес')
async def button_sb(message: Message):
    await message.answer(
        "📝 **Опиши состав своего блюда**\n\n"
        "Примеры:\n"
        "• 150г курицы, 100г риса, 20г масла\n"
        "• 2 яйца, 50г овсянки, 200мл молока\n"
        "• 100г творога, 1 банан\n\n"
        "Указывай вес в граммах (г) или просто цифрой.",
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == 'Набрать вес')
async def button_nb(message: Message):
    await message.answer(
        "📝 **Опиши состав своего блюда**\n\n"
        "Примеры:\n"
        "• 200г говядины, 150г гречки, 30г масла\n"
        "• 3 яйца, 100г овсянки с орехами\n"
        "• 200г лосося, 150г риса, 100г брокколи\n\n"
        "Указывай вес в граммах (г) или просто цифрой.",
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == 'Назад')
async def button_back(message: Message):
    """Возврат в главное меню"""
    keyboard = get_main_keyboard()
    await message.answer(
        "🔙 Назад в главное меню",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "help")
async def button_help(message: Message):
    """Обработчик кнопки help"""
    await message.answer(
        'ℹ️ **Как пользоваться ботом:**\n\n'
        '1. Нажми кнопку "start"\n'
        '2. Выбери цель: "Сбросить вес" или "Набрать вес"\n'
        '3. Опиши состав блюда (например: 150г курицы, 100г риса)\n'
        '4. Бот рассчитает калорийность и сохранит результат\n'
        '5. Нажми "📊 Статистика" чтобы увидеть итоги за день\n\n'
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
    """Обработчик кнопки info"""
    await message.answer(
        '🤖 **Информация о боте:**\n\n'
        'Версия: 1.0\n'
        'Функции:\n'
        '• Подсчет калорий и КБЖУ в продуктах\n'
        '• Сохранение истории питания\n'
        '• Статистика за день\n'
        '• Рекомендации по питанию\n\n'
        '📚 База данных содержит 30+ продуктов\n'
        '🔧 В разработке: расширенная база и индивидуальные нормы\n\n'
        'Автор: ваш любимый разработчик 😊',
        parse_mode="Markdown"
    )


@dp.message()
async def handle_food_description(message: Message):
    """Обработчик описания блюда - парсит и считает КБЖУ"""
    # Пропускаем если это кнопка
    if message.text in ["start", "help", "info", "📊 Статистика", "Сбросить вес", "Набрать вес", "Назад"]:
        return

    user_text = message.text
    user_id = message.from_user.id

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

    # 3. Сохраняем в базу данных
    save_food_entry(user_id, user_text, total)

    # 4. Формируем ответ
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

    # Показываем статистику за деньрит43ъ


    stats = get_today_stats(user_id)
    if stats:
        await message.answer(
            f"📊 **Статистика за сегодня:** {int(stats['calories'])} ккал, "
            f"{stats['protein']:.1f}г белков, "
            f"{stats['fat']:.1f}г жиров, "
            f"{stats['carbs']:.1f}г углеводов\n\n"
            f"Нажми '📊 Статистика' для подробной информации.",
            parse_mode="Markdown"
        )


# ========== ЗАПУСК ==========
async def main():
    """Главная функция запуска бота"""
    logging.info("Бот запущен!")
    print("🚀 Бот работает! Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    init_db()  # Инициализируем базу данных
    asyncio.run(main())