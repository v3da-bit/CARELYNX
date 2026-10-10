# pyrefly: ignore [missing-import]
from deep_translator import MyMemoryTranslator

try:
    res = MyMemoryTranslator(source='en-GB', target='hi-IN').translate("Azithromycin")
    print(f"SUCCESS: {res}")
except Exception as e:  # noqa: BLE001
    print(f"ERROR: {e}")
