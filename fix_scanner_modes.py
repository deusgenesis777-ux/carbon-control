from pathlib import Path
import py_compile

p = Path("main.py")
s = p.read_text(encoding="utf-8-sig")

old = '''        found = {}

        for device in devices:'''
new = '''        found = {}
        self.detected_device_modes = []

        for device in devices:'''

if old not in s:
    raise SystemExit("Не найден блок found = {}. Файл не изменён.")

s = s.replace(old, new, 1)

old = '''            entry = found.setdefault(key, {
                "name": known[key],'''
new = '''            if key not in self.detected_device_modes:
                self.detected_device_modes.append({
                    "id": key,
                    "name": known[key],
                })

            entry = found.setdefault(key, {
                "name": known[key],'''

if old not in s:
    raise SystemExit("Не найден блок entry = found.setdefault. Файл не изменён.")

s = s.replace(old, new, 1)
compile(s, str(p), "exec")
Path("main.py.scanner.tmp").write_text(s, encoding="utf-8")
py_compile.compile("main.py.scanner.tmp", doraise=True)
Path("main.py.scanner.tmp").replace(p)
print("Сканер обновлён. Синтаксис проверен.")
