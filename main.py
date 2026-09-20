import inspect
import pkgutil
import importlib
import rubpy

from rubpy import Client


print("=" * 70)
print("RUBPY RTC INSPECTION")
print("=" * 70)

print("Rubpy version:", getattr(rubpy, "__version__", "unknown"))

client = Client("RTC_TEST")


# ---------------------------------------------------------
# 1. بررسی متدهای اصلی Voice Chat
# ---------------------------------------------------------

targets = [
    "join_voice_chat",
    "voice_chat_player",
    "leave_group_voice_chat",
    "get_group_voice_chat_updates",
]

for name in targets:
    print("\n" + "=" * 70)
    print("METHOD:", name)

    fn = getattr(client, name, None)

    if fn is None:
        print("NOT FOUND")
        continue

    try:
        print("SIGNATURE:")
        print(inspect.signature(fn))
    except Exception as e:
        print("SIGNATURE ERROR:", repr(e))

    try:
        print("FILE:")
        print(inspect.getfile(fn))
    except Exception as e:
        print("FILE ERROR:", repr(e))


# ---------------------------------------------------------
# 2. بررسی VoiceChatConnection
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("VOICE CHAT CONNECTION")
print("=" * 70)

try:
    from rubpy.methods.advanced.voice_chat_player import VoiceChatConnection

    print("FOUND VoiceChatConnection")

    try:
        print("SIGNATURE:")
        print(inspect.signature(VoiceChatConnection))
    except Exception as e:
        print("SIGNATURE ERROR:", repr(e))

    try:
        print("\nSOURCE:")
        print(inspect.getsource(VoiceChatConnection))
    except Exception as e:
        print("SOURCE ERROR:", repr(e))

except Exception as e:
    print("VoiceChatConnection ERROR:", repr(e))


# ---------------------------------------------------------
# 3. پیدا کردن فایل مربوط به voice_chat_player
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("VOICE CHAT PLAYER MODULE")
print("=" * 70)

try:
    import rubpy.methods.advanced.voice_chat_player as player_module

    print("MODULE FILE:")
    print(inspect.getfile(player_module))

    print("\nMODULE SOURCE:")
    source = inspect.getsource(player_module)

    # برای اینکه خروجی GitHub Actions بیش از حد بزرگ نشود
    if len(source) > 30000:
        print(source[:30000])
        print("\n... SOURCE TRUNCATED ...")
    else:
        print(source)

except Exception as e:
    print("MODULE ERROR:", repr(e))


# ---------------------------------------------------------
# 4. جستجوی ماژول‌های RTC / WebRTC داخل Rubpy
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("SEARCHING RUBPY FOR RTC / SDP / WEBRTC")
print("=" * 70)

keywords = [
    "sdp",
    "rtc",
    "webrtc",
    "peerconnection",
    "voice_chat",
    "audio_track",
    "createoffer",
    "setlocaldescription",
]

found = []

try:
    for module_info in pkgutil.walk_packages(
        rubpy.__path__,
        rubpy.__name__ + "."
    ):
        module_name = module_info.name

        try:
            module = importlib.import_module(module_name)

            try:
                source_file = inspect.getfile(module)
            except Exception:
                continue

            try:
                source = inspect.getsource(module).lower()
            except Exception:
                continue

            matches = [
                keyword
                for keyword in keywords
                if keyword in source
            ]

            if matches:
                found.append(
                    (
                        module_name,
                        source_file,
                        matches
                    )
                )

        except Exception:
            continue

except Exception as e:
    print("PACKAGE SEARCH ERROR:", repr(e))


for module_name, source_file, matches in found:
    print("\nMODULE:", module_name)
    print("FILE:", source_file)
    print("MATCHES:", ", ".join(matches))


# ---------------------------------------------------------
# 5. بررسی aiortc
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("AIORTC CHECK")
print("=" * 70)

try:
    import aiortc

    print("aiortc version:",
          getattr(aiortc, "__version__", "unknown"))

    from aiortc import RTCPeerConnection

    print("RTCPeerConnection: FOUND")

    try:
        print("SIGNATURE:")
        print(inspect.signature(RTCPeerConnection))
    except Exception as e:
        print("SIGNATURE ERROR:", repr(e))

except Exception as e:
    print("AIORTC ERROR:", repr(e))


print("\n" + "=" * 70)
print("RTC INSPECTION FINISHED")
print("=" * 70)
