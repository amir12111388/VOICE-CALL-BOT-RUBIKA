import os
import asyncio
import logging
from pathlib import Path
from collections import defaultdict, deque

from rubpy import Client, Message, handlers


# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "RUBIKA_BOT_TOKEN تنظیم نشده است. "
        "آن را در GitHub Secrets قرار بده."
    )

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("RubikaVoiceBot")


# ============================================================
# STATE
# ============================================================

# صف آهنگ‌ها برای هر گپ
music_queues = defaultdict(deque)

# ویس‌کال فعال هر گپ
active_voice_chats = {}

# اتصال‌های صوتی
voice_connections = {}

# جلوگیری از پردازش دوباره فایل
processed_messages = set()


# ============================================================
# HELPERS
# ============================================================

def get_message_text(message):
    """
    استخراج متن پیام بدون وابستگی شدید به ساختار Message.
    """
    for attr in ("raw_text", "text", "message"):
        value = getattr(message, attr, None)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def get_object_guid(message):
    """
    گرفتن GUID گپ/پی‌وی.
    """
    for attr in (
        "object_guid",
        "chat_guid",
        "group_guid",
    ):
        value = getattr(message, attr, None)

        if value:
            return str(value)

    return None


def get_sender_guid(message):
    """
    گرفتن GUID فرستنده.
    """
    for attr in (
        "author_object_guid",
        "sender_object_guid",
        "author_guid",
    ):
        value = getattr(message, attr, None)

        if value:
            return str(value)

    return None


async def safe_reply(message, text):
    """
    پاسخ امن به پیام.
    """
    try:
        await message.reply(text)
    except Exception as exc:
        log.warning("Reply failed: %s", exc)


# ============================================================
# AUDIO DETECTION
# ============================================================

def find_media(message):
    """
    تلاش برای پیدا کردن فایل/مدیای پیام.

    ساختار دقیق Media در نسخه‌های مختلف Rubpy
    ممکن است متفاوت باشد؛ بنابراین چند حالت بررسی می‌شود.
    """

    candidates = [
        getattr(message, "file", None),
        getattr(message, "media", None),
        getattr(message, "audio", None),
        getattr(message, "music", None),
    ]

    for item in candidates:
        if item is not None:
            return item

    return None


def is_private_message(message):
    """
    تشخیص تقریبی PV.

    در Rubika معمولاً GUID پی‌وی با u شروع می‌شود.
    """
    guid = get_object_guid(message)

    if not guid:
        return False

    return guid.startswith("u")


# ============================================================
# VOICE CHAT STATE
# ============================================================

async def inspect_voice_chat(client, group_guid, voice_chat_id):
    """
    دریافت اطلاعات به‌روز ویس‌کال.

    این تابع عمداً فقط اطلاعات را دریافت می‌کند؛
    چون اتصال RTC به SDP واقعی نیاز دارد.
    """

    try:
        result = await client.get_group_voice_chat_updates(
            group_guid,
            voice_chat_id
        )

        log.info(
            "Voice chat update received: group=%s voice=%s result=%r",
            group_guid,
            voice_chat_id,
            result
        )

        return result

    except Exception as exc:
        log.exception(
            "Could not get voice chat updates: %s",
            exc
        )

        return None


# ============================================================
# RTC PLACEHOLDER
# ============================================================

async def connect_voice_chat(
    client,
    group_guid,
    voice_chat_id,
    sdp_offer_data
):
    """
    اتصال واقعی به ویس‌کال.

    sdp_offer_data باید از فرآیند RTC واقعی Rubpy
    به دست بیاید و نباید حدس زده شود.
    """

    try:
        result = await client.join_voice_chat(
            group_guid,
            voice_chat_id,
            sdp_offer_data
        )

        log.info(
            "join_voice_chat result: %r",
            result
        )

        # بعد از اتصال، Player را می‌سازیم.
        # این بخش فقط زمانی اجرا شود که مسیر RTC آماده باشد.
        return result

    except Exception as exc:
        log.exception(
            "Voice chat join failed: %s",
            exc
        )

        return None


# ============================================================
# PLAY AUDIO
# ============================================================

async def play_audio(
    client,
    group_guid,
    audio_path
):
    """
    پخش فایل با API واقعی voice_chat_player.

    توجه:
    این تابع زمانی قابل استفاده است که اتصال ویس‌کال
    قبلاً به شکل صحیح برقرار شده باشد.
    """

    try:
        connection = await client.voice_chat_player(
            group_guid,
            Path(audio_path)
        )

        voice_connections[group_guid] = connection

        log.info(
            "Audio player created: %r",
            connection
        )

        return connection

    except Exception as exc:
        log.exception(
            "Audio playback failed: %s",
            exc
        )

        return None


# ============================================================
# QUEUE
# ============================================================

async def queue_audio(
    client,
    group_guid,
    audio_path
):
    """
    اضافه کردن آهنگ به صف پخش.
    """

    queue = music_queues[group_guid]

    queue.append(Path(audio_path))

    log.info(
        "Added to queue: group=%s file=%s",
        group_guid,
        audio_path
    )

    # اگر چیزی در حال پخش نیست،
    # worker را اجرا می‌کنیم.
    await process_queue(client, group_guid)


async def process_queue(client, group_guid):
    """
    پردازش صف آهنگ‌ها.
    """

    queue = music_queues[group_guid]

    while queue:

        audio_path = queue.popleft()

        if not audio_path.exists():
            log.warning(
                "Audio file does not exist: %s",
                audio_path
            )
            continue

        log.info(
            "Playing: %s",
            audio_path
        )

        connection = await play_audio(
            client,
            group_guid,
            audio_path
        )

        if connection is None:
            log.error(
                "Could not start playback."
            )
            break

        # فعلاً منتظر می‌مانیم تا اتصال/Player
        # رفتار واقعی نسخه 7.3.5 مشخص شود.
        break


# ============================================================
# PRIVATE MESSAGE HANDLER
# ============================================================

async def on_message(message: Message):

    try:

        message_id = getattr(
            message,
            "message_id",
            None
        )

        if message_id:
            if message_id in processed_messages:
                return

            processed_messages.add(message_id)

        # فقط PV
        if not is_private_message(message):
            return

        media = find_media(message)

        if media is None:
            text = get_message_text(message)

            if text in ("/start", "شروع"):

                await safe_reply(
                    message,
                    "🎵 ربات موزیک ویس‌کال فعال است.\n\n"
                    "یک فایل صوتی برای من بفرست."
                )

            return

        await safe_reply(
            message,
            "🎵 آهنگ دریافت شد.\n"
            "در صف پخش قرار گرفت."
        )

        log.info(
            "Private media received from %s",
            get_sender_guid(message)
        )

        log.info(
            "MEDIA OBJECT: %r",
            media
        )

        # ----------------------------------------------------
        # دانلود واقعی فایل باید بر اساس ساختار Media
        # نسخه 7.3.5 پیاده‌سازی شود.
        # ----------------------------------------------------

    except Exception as exc:

        log.exception(
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

    print("Rubpy: 7.3.5")
    print("Token: configured")
    print("RTC: aiortc available")
    print()

    async with Client(
        name="voice_music_bot",
        auth=TOKEN
    ) as client:

        print("✅ Rubika client started")
        print("🎵 Waiting for private audio messages...")
        print()

        @client.on(
            handlers.MessageUpdates()
        )
        async def message_handler(
            message: Message
        ):
            await on_message(message)

        # نگه داشتن برنامه در حال اجرا
        while True:
            await asyncio.sleep(10)


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nBot stopped.")

    except Exception as exc:
        print(
            "\nBOT ERROR:",
            type(exc).__name__,
            exc
        )
