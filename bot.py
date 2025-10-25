import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from sqlalchemy.orm import Session
from .database import SessionLocal
from .crud import get_pending_notifications, mark_notification_sent
from .models import User
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

def _resolve_chat_id(db: Session, user_id: int) -> int | None:
    """Resolve Telegram chat_id for a given internal user id.
    Heuristics:
    - If user.contact looks like "tg:<digits>" or is digits only, treat as chat id.
    - Otherwise, return None (can't send by @username reliably without prior chat).
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        contact = getattr(user, "contact", None)
        if not contact:
            return None
        contact_str = str(contact).strip()
        if contact_str.startswith("tg:"):
            cid = contact_str.split(":", 1)[1].strip()
            return int(cid) if cid.isdigit() else None
        if contact_str.isdigit():
            return int(contact_str)
        # Could be @username; bots cannot initiate chats by username
        return None
    except Exception:
        return None

async def send_notifications():
    """Background task to send pending notifications"""
    while True:
        try:
            db: Session = SessionLocal()
            notifications = get_pending_notifications(db)

            for notification in notifications:
                try:
                    payload = notification.payload or {}

                    # Build message depending on payload shape
                    text: str
                    if isinstance(payload, dict) and payload.get("type") == "mutual_match":
                        partner_item = payload.get("partner_item", {}) or {}
                        partner_user = payload.get("partner_user", {}) or {}
                        title = partner_item.get("title", "—")
                        category = partner_item.get("category", "—")
                        description = partner_item.get("description", "—")
                        contact = partner_user.get("contact", "—")
                        trust = partner_user.get("trust_score")
                        trust_str = f"{float(trust):.1f}" if isinstance(trust, (int, float)) else "—"
                        text = (
                            f"<b>Взаимный матч!</b>\n"
                            f"Предмет: {title}\nКатегория: {category}\nОписание: {description}\n"
                            f"Контакт партнёра: {contact}\nДоверие: {trust_str}"
                        )
                    else:
                        # Legacy payload format support
                        partner_name = payload.get("partner_name", "—")
                        category = payload.get("category", "—")
                        description = payload.get("description", "—")
                        contact = payload.get("contact", "—")
                        rating = payload.get("rating")
                        rating_count = payload.get("rating_count", 0)
                        rating_str = f"{float(rating):.1f}" if isinstance(rating, (int, float)) else "—"
                        text = (
                            f"<b>Найден партнёр: {partner_name}</b>\n"
                            f"Категория: {category}\nОписание: {description}\n"
                            f"Контакт: {contact}\nРейтинг: {rating_str} ({rating_count} оценок)"
                        )

                    # Determine chat_id to send to
                    try:
                        user_id_val = getattr(notification, "user_id", None)
                        user_id_int = int(user_id_val) if user_id_val is not None else None
                    except (TypeError, ValueError):
                        user_id_int = None
                    chat_id = _resolve_chat_id(db, user_id_int) if user_id_int is not None else None
                    if chat_id is None:
                        # Fallback: try to use stored user_id as chat id (if you store tg chat id there)
                        try:
                            # Try converting stored user_id to int again as a last resort
                            user_id_val = getattr(notification, "user_id", None)
                            chat_id = int(user_id_val) if user_id_val is not None else None
                        except Exception:
                            chat_id = None

                    if chat_id is not None:
                        await bot.send_message(chat_id=chat_id, text=text)

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
