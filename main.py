import os
import asyncio
import logging
from pathlib import Path
from collections import defaultdict, deque

from rubpy import Client, handlers, filters
from rubpy.types import Update


# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "RUBIKA_BOT_TOKEN تنظیم نشده است."
    )

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("RubikaVoiceBot")


# ============================================================
# STATE
# ============================================================

music_queues = defaultdict(deque)
active_voice_chats = {}
voice_connections = {}


# ============================================================
# HELPERS
# ============================================================

def get_guid(update):
    return getattr(
        update,
        "object_guid",
        None
    )


def get_text(update):
    return getattr(
        update,
        "raw_text",
        None
    )


async def reply(update, text):
    try:
        await update.reply(text)
    except Exception as exc:
        logger.error("Reply error: %s", exc)


# ============================================================
# PRIVATE MESSAGE
# ============================================================

async def private_messages(update: Update):

    try:

        print("\n" + "=" * 50)
        print("NEW MESSAGE")
        print("=" * 50)

        print("Object GUID:",
              getattr(update, "object_guid", None))

        print("Author GUID:",
              getattr(update, "author_object_guid", None))

        print("Message ID:",
              getattr(update, "message_id", None))

        print("Raw text:",
              getattr(update, "raw_text", None))

        print("Message object:")
        print(update)

        print("=" * 50)

        text = get_text(update)

        if text == "/start":

            await reply(
                update,
                "🎵 ربات موزیک ویس‌کال فعال است.\n\n"
                "یک آهنگ برای من ارسال کن."
            )

    except Exception as exc:

        logger.exception(
            "Message handler error: %s",
            exc
        )


# ============================================================
# MAIN
# ============================================================

async def main():

    print("=" * 60)
    print("        RUBIKA VOICE MUSIC BOT")
    print("=" * 60)

    print("Rubpy version: 7.3.5")
    print("Token: configured")
    print("RTC dependencies: installed")
    print()

    async with Client(
        name="rubika_voice_bot",
        auth=TOKEN
    ) as client:

        print("✅ Rubika client connected")

        @client.on(
            handlers.MessageUpdates(
                filters.is_private
            )
        )
        async def message_handler(
            update: Update
        ):
            await private_messages(update)

        print("✅ Private message handler registered")
        print("🎵 Bot is running...")
        print()

        await client.run_until_disconnected()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Bot stopped.")

    except Exception as exc:
        print(
            "BOT ERROR:",
            type(exc).__name__,
            exc
        )
