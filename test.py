import asyncio
import logging
import re
import json
import os
import aiohttp
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

logging.basicConfig(level=logging.INFO)
TELEGRAM_TOKEN = "8323110038:AAHIz4DD3QiMLnaXapvcYxXQ8jvSwXzcZ2c"
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
    )
dp = Dispatcher()
baza = {
    "курица": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0},
    "говядина": {"calories": 250, "protein": 26, "fat": 16, "carbs": 0},
    "свинина": {"calories": 242, "protein": 27, "fat": 14, "carbs": 0},
    "индейка": {"calories": 135, "protein": 29, "fat": 1.5, "carbs": 0},
    "рыба": {"calories": 120, "protein": 20, "fat": 4, "carbs": 0},
    "лосось": {"calories": 208, "protein": 20, "fat": 13, "carbs": 0},
    "тунец": {"calories": 144, "protein": 23, "fat": 5, "carbs": 0},
    "рис": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
    "гречка": {"calories": 110, "protein": 4.2, "fat": 1.1, "carbs": 21},
    "овсянка": {"calories": 88, "protein": 3.1, "fat": 1.8, "carbs": 15},
    "макароны": {"calories": 131, "protein": 5, "fat": 1, "carbs": 25},
    "хлеб": {"calories": 265, "protein": 8, "fat": 3.2, "carbs": 49},
    "картофель": {"calories": 77, "protein": 2, "fat": 0.4, "carbs": 17},
    "морковь": {"calories": 41, "protein": 0.9, "fat": 0.2, "carbs": 10},
    "огурец": {"calories": 15, "protein": 0.7, "fat": 0.1, "carbs": 2.5},
    "помидор": {"calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 3.9},
    "капуста": {"calories": 25, "protein": 1.3, "fat": 0.1, "carbs": 5},
    "банан": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23},
    "яблоко": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
    "апельсин": {"calories": 47, "protein": 0.9, "fat": 0.1, "carbs": 12},
    "молоко": {"calories": 60, "protein": 3.2, "fat": 3.2, "carbs": 4.8},
    "сыр": {"calories": 350, "protein": 25, "fat": 27, "carbs": 0},
    "творог": {"calories": 121, "protein": 18, "fat": 5, "carbs": 3},
    "йогурт": {"calories": 59, "protein": 3.5, "fat": 0.5, "carbs": 10},
    "яйцо": {"calories": 155, "protein": 13, "fat": 11, "carbs": 0.7},
    "масло сливочное": {"calories": 748, "protein": 0.5, "fat": 82.5, "carbs": 0.8},
    "масло оливковое": {"calories": 884, "protein": 0, "fat": 100, "carbs": 0},
    "масло подсолнечное": {"calories": 899, "protein": 0, "fat": 99.9, "carbs": 0},
}


API_CACHE_FILE = "api_cache.json"
MEALS_CACHE_FILE = "meals_cache.json"


def load_api_cache():
    if os.path.exists(API_CACHE_FILE):
        with open(API_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_api_cache(cache):
    with open(API_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def load_meals_cache():
    if os.path.exists(MEALS_CACHE_FILE):
        with open(MEALS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_meals_cache(cache):
    with open(MEALS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


API_CACHE = load_api_cache()
MEALS_CACHE = load_meals_cache()



LOCAL_MEALS = {
    "утка по-пекински": {"calories": 308, "protein": 13.5, "fat": 28.6, "carbs": 7},
    "борщ": {"calories": 50, "protein": 2, "fat": 3, "carbs": 5},
    "оливье": {"calories": 180, "protein": 5, "fat": 12, "carbs": 8},
    "цезарь": {"calories": 190, "protein": 12, "fat": 14, "carbs": 6},
    "пельмени": {"calories": 220, "protein": 9, "fat": 8, "carbs": 25},
    "шаурма": {"calories": 250, "protein": 12, "fat": 14, "carbs": 18},
    "пицца маргарита": {"calories": 270, "protein": 11, "fat": 11, "carbs": 30},
    "суши": {"calories": 140, "protein": 6, "fat": 2, "carbs": 24},
}

def parse_food_description(text: str):
    pattern = r'(\d+)\s*[г]?\s*([а-яё\s]+)'
    matches = re.findall(pattern, text.lower())
    result = []
    for weight, food in matches:
        food = food.strip()
        found = False
        for db_food in baza:
            if db_food in food or food in db_food:
                result.append((db_food, int(weight)))
                found = True
                break
        if not found:
            result.append((food, int(weight)))
    return result


def calculate_nutrition(foods):
    total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    unknown_foods = []
    for food_name, weight in foods:
        if food_name in baza:
            data = baza[food_name]
            ratio = weight / 100
            total["calories"] += data["calories"] * ratio
            total["protein"] += data["protein"] * ratio
            total["fat"] += data["fat"] * ratio
            total["carbs"] += data["carbs"] * ratio
        else:
            unknown_foods.append(food_name)
    return total, unknown_foods


def is_ingredients_format(text: str) -> bool:
    return bool(re.search(r'\d+\s*[г]', text))





async def search_openfoodfacts(product_name: str):
    cache_key = product_name.lower().strip()
    if cache_key in API_CACHE:
        return API_CACHE[cache_key]

    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": product_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
        "lang": "ru"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                results = []
                for product in data.get('products', []):
                    nutriments = product.get('nutriments', {})
                    calories = nutriments.get('energy-kcal_100g', 0)
                    if calories == 0:
                        continue
                    results.append({
                        "name": product.get('product_name_ru') or product.get('product_name', 'Неизвестно'),
                        "brand": product.get('brands', 'Бренд не указан'),
                        "calories": calories,
                        "protein": nutriments.get('proteins_100g', 0),
                        "fat": nutriments.get('fat_100g', 0),
                        "carbs": nutriments.get('carbohydrates_100g', 0)
                    })
                if results:
                    API_CACHE[cache_key] = results
                    save_api_cache(API_CACHE)
                return results
    except Exception as e:
        print(f"Ошибка Open Food Facts: {e}")
        return []









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
        "Опиши состав своего блюда (например: 150г курицы, 100г риса)",
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == 'Набрать вес')
async def button_nb(message: Message):
    await message.answer(
        "Опиши состав своего блюда (например: 150г курицы, 100г риса)",
        parse_mode="Markdown"
    )


@dp.message(lambda message: message.text == 'Назад')
async def button_back(message: Message):
    keyboard = get_main_keyboard()
    await message.answer(
        "Назад в главное меню",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "help")
async def button_help(message: Message):
    await message.answer(
        'ℹ**Как пользоваться ботом:**\n\n'
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
    await message.answer('Информация о боте: версия 1.0, умеет определять калории в еде и блюдах')












async def main():
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())