import sys
import traceback

print("Attempting to trace import of httpx...")
try:
    import httpx
except SyntaxError as e:
    print("SyntaxError caught!")
    print(f"Message: {e}")
    print(f"Filename: {e.filename}")
    print(f"Lineno: {e.lineno}")
    print(f"Offset: {e.offset}")
    print(f"Text: {repr(e.text)}")
    traceback.print_exc()
except Exception as e:
    print(f"Other exception caught: {type(e).__name__}: {e}")
    traceback.print_exc()
