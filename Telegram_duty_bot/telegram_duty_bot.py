import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "$TELEGRAM_API_TOKEN"
CHAT_ID= "$CHAT_ID"  # сюда будет отправка сообщений, если никто не стал дежурным.



# Список юзернеймов, которые могут стать дежурными
allowed_users = ["user1", "user2", "user3", "user4"]

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
    <b>OPS-4238</b>

    Вот доступные команды:
    /start - Начать взаимодействие с ботом
    /set_duty - Назначить себя дежурным
    /drop_duty - Сбросить себя с должности дежурного
    /help - Показать этот список команд
    /call - Вызвать дежурного

    Внимание! дежурным может стать только один из инженеров.
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

@dp.message(Command("call"))
async def call_duty(message: Message):
    if current_duty:
        print(f"Текущий дежурный: {current_duty}")  # Проверяем, есть ли назначенный дежурный
        
        try:
            duty_user = await bot.get_chat(current_duty)  # Получаем данные о дежурном
            if duty_user.username:
                mention = f"@{duty_user.username}"  # Тег по username
            else:
                mention = f"<a href='tg://user?id={current_duty}'>дежурный</a>"  # Ссылка, если username нет

            await message.answer(f"{mention}, вас вызывает @{message.from_user.username}!", parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка при получении чата дежурного: {e}")  # Лог ошибки
            await message.answer("Ошибка при вызове дежурного.")
    else:
        if message.chat.username:
            message_link = f"Ссылка на сообщение: https://t.me/{message.chat.username}/{message.message_id}\nТекст сообщения: {message.text}"
        else:
            chat_title = message.chat.title if message.chat.title else "Неизвестный чат"
            message_link = f"Ссылка на сообщение недоступна: НЕПУБЛИЧНАЯ ГРУППА ({chat_title}).\nТекст сообщения: {message.text}"

        await bot.send_message(
            CHAT_ID, 
            f"⚠️ Внимание! Дежурный не назначен.\nПоступил вызов от @{message.from_user.username}\n{message_link}\n"
        )
        await message.answer("Дежурный не назначен, сообщение отправлено в общий чат инженеров.")
        return

@dp.message()
async def forward_to_duty(message: Message):
    global bot_username
    if bot_username is None:
        bot_info = await bot.get_me()
        bot_username = bot_info.username

    # Проверяем, упомянул ли кто-то бота
    mentioned = False
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mentioned_user = message.text[entity.offset:entity.offset + entity.length]
                if mentioned_user == f"@{bot_username}":
                    mentioned = True
                    break

    if mentioned:
        # Формируем ссылку на сообщение
        if message.chat.username:
            message_link = f"Ссылка на сообщение: https://t.me/{message.chat.username}/{message.message_id}\nТекст сообщения: {message.text}"
        else:
            chat_title = message.chat.title if message.chat.title else "Неизвестный чат"
            message_link = f"Ссылка на сообщение недоступна: НЕПУБЛИЧНАЯ ГРУППА ({chat_title}).\nТекст сообщения: {message.text}"

        # Если дежурный не назначен — отправляем в общий чат
        if current_duty is None:
            await bot.send_message(
                CHAT_ID, 
                f"⚠️ Внимание! Дежурный не назначен.\nСообщение от @{message.from_user.username}:\n{message_link}"
            )
            await message.answer("Дежурный не назначен, сообщение отправлено в общий чат инженеров.")
            return

        # Если дежурный есть, отправляем сообщение ему
        await bot.send_message(current_duty, f"Сообщение от @{message.from_user.username}:\n{message_link}")
        await message.answer("Ваше сообщение передано дежурному.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
