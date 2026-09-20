import os
import asyncio
import rubpy


TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN تنظیم نشده است")


async def main():
    print("=" * 40)
    print("Rubika Voice Bot Test")
    print("=" * 40)

    print("Rubpy version:", getattr(rubpy, "__version__", "unknown"))
    print("Token: configured")

    try:
        from rubpy import Client

        bot = Client(TOKEN)

        print("Client: OK")

        voice_player = getattr(bot, "voice_chat_player", None)

        if voice_player:
            print("VOICE_CHAT_PLAYER: FOUND")
        else:
            print("VOICE_CHAT_PLAYER: NOT FOUND")

        methods = [
            x for x in dir(bot)
            if "voice" in x.lower() or "call" in x.lower()
        ]

        print("\nVoice/Call methods:")
        for method in methods:
            print(" -", method)

        print("\nTest completed.")

    except Exception as e:
        print("ERROR:", type(e).__name__)
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
