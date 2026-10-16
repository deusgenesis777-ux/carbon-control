from pathlib import Path
import re
import py_compile

p = Path("main.py")
s = p.read_text(encoding="utf-8-sig")

pattern = r'    def check_device\(self\):\n.*?(?=\n    def apply_sidebar_layout\(self\):)'

replacement = '''    def check_device(self):
        self.scan_hid_devices()
        modes = getattr(self, "detected_device_modes", [])

        if any("2.4G" in mode for mode in modes):
            self.device_status_label.setText(
                "● Приёмник 2.4 ГГц обнаружен; связь с мышью не подтверждена"
            )
        elif "USB" in modes:
            self.device_status_label.setText(
                "● HID-устройство AJAZZ по USB обнаружено"
            )
        else:
            self.device_status_label.setText(
                "● Приёмник или мышь не обнаружены"
            )

        self.device_battery_label.setText("Заряд батареи: нет данных")
        QMessageBox.information(
            self, "Проверка устройства", self.hid_result.text()
        )
'''

updated, count = re.subn(pattern, replacement, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Метод check_device не найден. Файл не изменён.")

compile(updated, str(p), "exec")
p.write_text(updated, encoding="utf-8")
py_compile.compile(str(p), doraise=True)
print("Статус подключения обновлён. Синтаксис проверен.")
