import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "7081243338:AAEuQE4cx7mXgkKdHKcvSwfGSRTBNdczR9Y"

# Список юзернеймов, которые могут стать дежурными
allowed_users = ["lolwutski", "php_bolno", "palmface1337", "Toh3mi"]

# Храним текущего дежурного в памяти
current_duty = None
bot_username = None  # Добавим глобальную переменную для имени бота

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я бот для распределения дежурных. Используйте /help для получения списка команд.")

@dp.message(Command("help"))
async def help_handler(message: Message):
    help_text = """
    Вот доступные команды:
    /start - Начать взаимодействие с ботом
    /set_duty - Назначить себя дежурным
    /drop_duty - Сбросить себя с должности дежурного
    /help - Показать этот список команд
    Внимание, дежурным может стать только один из инженеров.
    """
    if current_duty:
        help_text += f"\nТекущий дежурный: <a href='tg://user?id={current_duty}'>этот пользователь</a>"
    else:
        help_text += "\nДежурный не назначен."

    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("set_duty"))
async def set_duty(message: Message):
    global current_duty
    user_username = message.from_user.username

    # Проверяем, есть ли пользователь в списке разрешенных
    if user_username in allowed_users:
        current_duty = message.from_user.id
        await message.answer(f"Вы назначены дежурным, @{user_username}! Теперь все обращения будут направляться вам.")
    else:
        await message.answer(f"Извините, @{user_username}, вы не можете стать дежурным.")

@dp.message(Command("drop_duty"))
async def reset_duty(message: Message):
    global current_duty
    if message.from_user.id == current_duty:
        current_duty = None
        await message.answer(f"Вы сняты с должности дежурного, @{message.from_user.username}.")
    else:
        await message.answer(f"Вы не дежурный, @{message.from_user.username}.")

@dp.message()
async def forward_to_duty(message: Message):
    global bot_username
    if bot_username is None:
        bot_info = await bot.get_me()
        bot_username = bot_info.username

    # Проверяем, упомянул ли кто-то бота
    mentioned = False
    for entity in message.entities:
        if entity.type == "mention":
            mentioned_user = message.text[entity.offset:entity.offset + entity.length]
            if mentioned_user == f"@{bot_username}":
                mentioned = True
                break

    if mentioned:
        # Проверяем, если дежурный не назначен
        if current_duty is None:
            await message.answer("Дежурный не назначен.")
            return

        # Формируем ссылку на сообщение
        if message.chat.username:
            message_link = f"Ссылка на сообщение: https://t.me/{message.chat.username}/{message.message_id}\nТекст сообщения: {message.text}\n"
        else:
            message_link = f"Ссылка на сообщение недоступна: НЕПУБЛИЧНАЯ ГРУППА.\nТекст сообщения: {message.text}"

        # Отправляем сообщение дежурному
        await bot.send_message(current_duty, f"Сообщение от @{message.from_user.username}:\n{message_link}")
        await message.answer("Ваше сообщение передано дежурному.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
