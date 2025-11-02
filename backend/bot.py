import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.crud import get_pending_notifications, mark_notification_sent
from backend.models import User
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
    retry_delay = 5  # Start with 5 seconds
    max_retry_delay = 60  # Max 60 seconds

    while True:
        try:
            db: Session = SessionLocal()

            try:
                notifications = get_pending_notifications(db)
            except Exception as db_error:
                # Handle database connection errors gracefully
                db.close()
                print(f"⚠️  Database connection error (will retry in {retry_delay}s): {type(db_error).__name__}")
                await asyncio.sleep(retry_delay)
                # Increase retry delay up to max
                retry_delay = min(retry_delay * 1.5, max_retry_delay)
                continue

            # Reset retry delay on success
            retry_delay = 5

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
            print(f"⚠️  Notification loop error: {type(e).__name__}: {e}")

        await asyncio.sleep(60)  # Check every minute

async def send_match_notification_with_retry(
    user_telegram_id: int,
    partner_username: str,
    partner_wants: str,
    your_offers: str,
    score: float,
    match_id: int = 0,
    max_retries: int = 3
) -> bool:
    """
    Send a notification about a found match to Telegram user with retry logic.

    Uses exponential backoff: 1s, 2s, 4s delays between retries.
    Includes idempotency protection via match_id + user_telegram_id.

    Args:
        user_telegram_id: Telegram chat_id of the user
        partner_username: Telegram username of the partner (@username)
        partner_wants: What the partner is looking for
        your_offers: What you can offer
        score: Match score (0.0-1.0)
        match_id: ID of the match for cabinet link
        max_retries: Maximum number of retry attempts

    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not user_telegram_id:
        print(f"⚠️  No telegram_id for notification")
        return False

    # Idempotency key for this notification
    notification_key = f"match_{match_id}_user_{user_telegram_id}"

    # Check if already sent (basic in-memory deduplication)
    # In production, use Redis or database for persistent deduplication
    if hasattr(send_match_notification_with_retry, '_sent_notifications'):
        if notification_key in send_match_notification_with_retry._sent_notifications:
            print(f"ℹ️  Notification {notification_key} already sent, skipping")
            return True
    else:
        send_match_notification_with_retry._sent_notifications = set()

    cabinet_url = f"https://freemarket.com/cabinet?match={match_id}" if match_id else "https://freemarket.com/cabinet"

    message = f"""
🎉 <b>Совпадение найдено!</b>

👤 <b>Партнер:</b> {partner_username}
🎯 <b>Он ищет:</b> {partner_wants}
🎁 <b>Вы можете дать:</b> {your_offers}

📊 <b>Оценка совпадения:</b> {int(score * 100)}%

<a href="{cabinet_url}">👉 Смотреть в кабинете</a>
"""

    for attempt in range(max_retries):
        try:
            await bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode=ParseMode.HTML
            )

            # Mark as sent
            send_match_notification_with_retry._sent_notifications.add(notification_key)

            print(f"✅ Match notification sent to {user_telegram_id} (attempt {attempt + 1})")
            return True

        except TelegramBadRequest as e:
            if attempt == max_retries - 1:
                print(f"❌ Failed to send match notification to {user_telegram_id} after {max_retries} attempts: {e}")
                return False
            else:
                print(f"⚠️  Attempt {attempt + 1} failed, retrying: {e}")

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ Unexpected error sending notification to {user_telegram_id}: {e}")
                return False
            else:
                print(f"⚠️  Attempt {attempt + 1} failed with unexpected error, retrying: {e}")

        # Exponential backoff: 1s, 2s, 4s
        if attempt < max_retries - 1:
            delay = 2 ** attempt
            print(f"⏳  Waiting {delay}s before retry...")
            await asyncio.sleep(delay)

    return False


# Backward compatibility alias
async def send_match_notification(
    user_telegram_id: int,
    partner_username: str,
    partner_wants: str,
    your_offers: str,
    score: float,
    match_id: int = 0
) -> bool:
    """Legacy alias for backward compatibility"""
    return await send_match_notification_with_retry(
        user_telegram_id, partner_username, partner_wants, your_offers, score, match_id
    )

async def main():
    # Start notification sender
    asyncio.create_task(send_notifications())

    # Start bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
