import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ParseMode, Message
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import get_pending_notifications, mark_notification_sent
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message()
async def handle_message(message: Message):
    await message.reply("Привет! Я бот FreeMarket. Используйте веб-приложение для регистрации.")

async def send_notifications():
    """Background task to send pending notifications"""
    while True:
        try:
            db: Session = SessionLocal()
            notifications = get_pending_notifications(db)

            for notification in notifications:
                try:
                    payload = notification.payload

                    text = f"""
<b>Найден партнёр: {payload['partner_name']}</b>
Категория: {payload['category']}
Описание: {payload['description']}
Контакт: {payload['contact']}
Рейтинг: {payload['rating']:.1f} ({payload['rating_count']} оценок)
                    """.strip()

                    await bot.send_message(
                        chat_id=notification.user_id,
                        text=text
                    )

                    mark_notification_sent(db, notification.id)

                except Exception as e:
                    print(f"Failed to send notification {notification.id}: {e}")

            db.close()

        except Exception as e:
            print(f"Notification loop error: {e}")

        await asyncio.sleep(60)  # Check every minute

async def main():
    # Start notification sender
    asyncio.create_task(send_notifications())

    # Start bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
