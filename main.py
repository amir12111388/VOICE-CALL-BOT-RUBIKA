import os
import asyncio
import logging
import wave
import math
from pathlib import Path

from rubpy import Client


# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")
CHAT_GUID = os.getenv("TEST_CHAT_GUID")

TEST_AUDIO = Path("rtc_test.wav")
PLAY_SECONDS = 15


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("RubikaRTC")


# =========================================================
# CREATE TEST AUDIO
# =========================================================

def create_test_audio(path: Path):
    """
    یک فایل WAV ساده می‌سازد.
    نیاز به دانلود هیچ فایل صوتی خارجی ندارد.
    """

    sample_rate = 48000
    duration = 5
    frequency = 440

    channels = 1
    sample_width = 2

    total_samples = sample_rate * duration

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)

        frames = bytearray()

        for i in range(total_samples):
            t = i / sample_rate

            # صدای سینوسی تست
            value = int(
                16000 * math.sin(
                    2 * math.pi * frequency * t
                )
            )

            frames.extend(
                value.to_bytes(
                    2,
                    byteorder="little",
                    signed=True
                )
            )

        wav.writeframes(frames)

    logger.info(
        "Test audio created: %s",
        path
    )


# =========================================================
# RTC TEST
# =========================================================

async def run_rtc_test(client: Client):

    if not CHAT_GUID:
        logger.error(
            "TEST_CHAT_GUID is not configured."
        )
        logger.error(
            "Add your Rubika group GUID as a GitHub Secret."
        )
        return

    logger.info("=" * 60)
    logger.info("STARTING REAL RUBIKA RTC TEST")
    logger.info("=" * 60)

    logger.info(
        "Chat GUID: %s",
        CHAT_GUID
    )

    # -----------------------------------------------------
    # Create audio
    # -----------------------------------------------------

    create_test_audio(TEST_AUDIO)

    # -----------------------------------------------------
    # Start Voice Chat Player
    # -----------------------------------------------------

    logger.info(
        "Calling client.voice_chat_player()..."
    )

    connection = None

    try:

        connection = await client.voice_chat_player(
            CHAT_GUID,
            TEST_AUDIO
        )

        if connection is None:
            logger.error(
                "voice_chat_player returned None."
            )
            return

        logger.info(
            "VoiceChatConnection created successfully."
        )

        # -------------------------------------------------
        # Print information
        # -------------------------------------------------

        try:
            info = connection.get_info()

            logger.info(
                "VOICE CHAT INFO: %s",
                info
            )

        except Exception as e:
            logger.warning(
                "Could not read connection info: %s",
                e
            )

        # -------------------------------------------------
        # Keep audio playing
        # -------------------------------------------------

        logger.info(
            "Audio playback started."
        )

        logger.info(
            "Waiting %s seconds...",
            PLAY_SECONDS
        )

        await asyncio.sleep(PLAY_SECONDS)

        logger.info(
            "Playback test finished."
        )

    except Exception as e:

        logger.exception(
            "RTC TEST FAILED: %s",
            e
        )

    finally:

        # -------------------------------------------------
        # Stop connection
        # -------------------------------------------------

        if connection is not None:

            try:
                connection.stop()

                logger.info(
                    "Voice chat connection stopped."
                )

            except Exception as e:

                logger.warning(
                    "Error while stopping connection: %s",
                    e
                )

        # -------------------------------------------------
        # Delete test audio
        # -------------------------------------------------

        try:

            if TEST_AUDIO.exists():
                TEST_AUDIO.unlink()

                logger.info(
                    "Temporary audio deleted."
                )

        except Exception as e:

            logger.warning(
                "Could not delete temporary audio: %s",
                e
            )


# =========================================================
# MAIN
# =========================================================

async def main():

    logger.info("=" * 60)
    logger.info("RUBIKA REAL RTC TEST")
    logger.info("=" * 60)

    if not TOKEN:
        logger.error(
            "RUBIKA_BOT_TOKEN is not configured."
        )
        return

    logger.info(
        "Bot token: configured"
    )

    async with Client(
        name="rubika_rtc_test",
        auth=TOKEN
    ) as client:

        logger.info(
            "Rubpy client connected."
        )

        await run_rtc_test(client)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
