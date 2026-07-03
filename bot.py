import asyncio
import time
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from aiogram.client.default import DefaultBotProperties

from telethon import TelegramClient, events

from config import BOT_TOKEN, API_ID, API_HASH, TARGET_CHANNEL, SOURCE_CHANNELS, ADMIN_ID

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Инициализация клиентов
aiogram_bot = Bot(
    token=BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
telethon_client = TelegramClient("session", API_ID, API_HASH)


class MessageProcessor:
    async def forward_message(self, message, source_username: str):
        try:
            final_text = message.message or ""  # текст сообщения

            if message.media:  # если есть медиа
                file_bytes = await message.download_media(bytes)
                media = BufferedInputFile(file_bytes, filename="media.jpg")

                # Убираем disable_web_page_preview для send_photo
                await aiogram_bot.send_photo(
                    chat_id=TARGET_CHANNEL,
                    photo=media,
                    caption=final_text,
                    parse_mode=ParseMode.HTML
                    # disable_web_page_preview удален отсюда
                )
            else:
                # Если нет медиа - только текст
                if final_text:
                    await aiogram_bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=final_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True  # Оставляем только для текстовых сообщений
                    )

            logger.info(f"Сообщение из {source_username} успешно переслано")

        except Exception as e:
            logger.error(f"Ошибка пересылки сообщения: {e}")


processor = MessageProcessor()


async def setup_telethon():
    try:
        await telethon_client.start()
        logger.info("Telethon клиент запущен")

        # Получаем все диалоги (чаты, где состоит клиент)
        dialogs = await telethon_client.get_dialogs()
        logger.info(f"Получено {len(dialogs)} диалогов")

        channel_entities = []
        for channel in SOURCE_CHANNELS:
            try:
                # Пытаемся получить сущность напрямую (по username или ID)
                entity = await telethon_client.get_entity(channel)
                channel_entities.append(entity)
                logger.info(f"Подключен к каналу: {channel}")
            except Exception as e:
                # Если не получилось, пробуем найти по ID среди диалогов
                try:
                    channel_id = int(channel)  # преобразуем строку в число
                    found = False
                    for dialog in dialogs:
                        if dialog.entity.id == channel_id:
                            channel_entities.append(dialog.entity)
                            logger.info(f"Найден канал по ID: {channel}")
                            found = True
                            break
                    if not found:
                        logger.error(f"Канал {channel} не найден среди диалогов")
                except ValueError:
                    logger.error(f"Не удалось подключиться к каналу {channel}: {e}")

        if not channel_entities:
            logger.error("Нет доступных каналов для мониторинга")
            return

        # Обработчик новых сообщений
        @telethon_client.on(events.NewMessage(chats=channel_entities))
        async def handler(event):
            try:
                message = event.message
                chat = await event.get_chat()
                source_username = (
                    f"@{chat.username}" if hasattr(chat, "username") and chat.username else "Unknown Source"
                )
                logger.info(f"Получено сообщение из {source_username}")
                await processor.forward_message(message, source_username)
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {e}")

        logger.info(f"Мониторинг {len(channel_entities)} каналов запущен")

    except Exception as e:
        logger.error(f"Ошибка запуска Telethon: {e}")
        raise


async def send_test_message():
    """Отправка тестового сообщения"""
    try:
        await aiogram_bot.send_message(
            chat_id=ADMIN_ID,
            text="✅ <b>Бот запущен и готов к работе!</b>\n\n"
                 f"📊 Мониторинг каналов: {len(SOURCE_CHANNELS)}\n"
                 f"🎯 Целевой канал: {TARGET_CHANNEL}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Ошибка отправки тестового сообщения: {e}")


async def main():
    """Основная функция"""
    try:
        logger.info("Запуск бота...")

        # Запускаем Telethon
        await setup_telethon()

        # Отправляем тестовое сообщение
        await send_test_message()

        logger.info("Бот успешно запущен! Ожидание сообщений...")

        # Запускаем бесконечный цикл
        await telethon_client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await aiogram_bot.close()
        await telethon_client.disconnect()


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
            break
        except Exception as e:
            logger.error(f"Перезапуск из-за ошибки: {e}")
            time.sleep(30)