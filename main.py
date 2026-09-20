import inspect
import rubpy
from rubpy import Client


print("=" * 50)
print("Rubpy Voice API Inspector")
print("=" * 50)

print("Rubpy version:", getattr(rubpy, "__version__", "unknown"))

try:
    client = Client("TEST")

    methods = [
        "join_voice_chat",
        "voice_chat_player",
        "leave_group_voice_chat",
        "get_group_voice_chat_updates",
    ]

    for name in methods:
        print("\n" + "-" * 50)
        print(name)

        method = getattr(client, name, None)

        if method is None:
            print("NOT FOUND")
            continue

        print("FOUND")

        try:
            print("Signature:")
            print(inspect.signature(method))
        except Exception as e:
            print("Could not read signature:", e)

        try:
            print("\nDocumentation:")
            print(inspect.getdoc(method) or "No documentation")
        except Exception as e:
            print("Could not read documentation:", e)

except Exception as e:
    print("\nERROR:", type(e).__name__)
    print(e)
