from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8-sig")

old = '        state.setWordWrap(True)\n\n        check = QPushButton'
new = '''        state.setWordWrap(True)
        self.device_status_label = state

        battery = QLabel("Заряд батареи: нет данных")
        battery.setObjectName("muted")
        battery.setWordWrap(True)
        self.device_battery_label = battery

        check = QPushButton'''

if old not in s:
    raise SystemExit("Блок не найден. Файл не изменён.")

s = s.replace(old, new, 1)

old2 = '        left.addWidget(state)\n        left.addSpacing(2)'
new2 = '        left.addWidget(state)\n        left.addWidget(battery)\n        left.addSpacing(2)'

if old2 not in s:
    raise SystemExit("Место вставки не найдено. Файл не изменён.")

s = s.replace(old2, new2, 1)
compile(s, str(p), "exec")
p.write_text(s, encoding="utf-8")
print("Поле заряда добавлено. Синтаксис проверен.")
