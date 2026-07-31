import os

search_dir = r"C:\Users\akkum\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\httpx"
print(f"Scanning {search_dir} for null bytes...")
found = False

if not os.path.exists(search_dir):
    print("Directory does not exist!")
else:
    for root, dirs, files in os.walk(search_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    with open(path, "rb") as file_obj:
                        content = file_obj.read()
                        if b"\x00" in content:
                            print(f"Null byte found in: {path}")
                            found = True
                except Exception as ex:
                    print(f"Error reading {path}: {ex}")

if not found:
    print("No null bytes found in site-packages/httpx.")
