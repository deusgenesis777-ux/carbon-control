from pathlib import Path
import re

path = Path("main.py")
source = path.read_text(encoding="utf-8-sig")

def replace_method(source, name, replacement):
    pattern = rf"(?ms)^    def {re.escape(name)}\(.*?(?=^    def |\Z)"
    updated, count = re.subn(
        pattern, lambda _: replacement.rstrip() + "\n\n", source
    )
    if count != 1:
        raise RuntimeError(f"{name}: найдено функций — {count}")
    return updated

scan_method = r'''    def scan_hid_devices(self):
        try:
            import hid
            devices = hid.enumerate()
        except Exception as exc:
            self.hid_result.setText(
                "Не удалось прочитать список USB HID. "
                "Проверь установку hidapi.\n" + str(exc)
            )
            return

        known = {
            (0xA8A4, 0x2266): "USB",
            (0xA8A5, 0x2266): "2.4G (приёмник)",
        }
        found = {}

        for device in devices:
            key = (
                int(device.get("vendor_id", 0) or 0),
                int(device.get("product_id", 0) or 0),
            )
            if key not in known:
                continue

            entry = found.setdefault(key, {
                "name": known[key],
                "product": device.get("product_string") or "AJAZZ",
                "interfaces": [],
                "config_interface": False,
            })

            interface = int(device.get("interface_number", -1))
            usage_page = int(device.get("usage_page", 0) or 0)
            usage = int(device.get("usage", 0) or 0)

            if interface not in entry["interfaces"]:
                entry["interfaces"].append(interface)

            if usage_page == 0xFF01 and usage == 0x0010:
                entry["config_interface"] = True

        if not found:
            self.hid_result.setText(
                "AJAZZ AJ199 Carbon не обнаружена. "
                "Проверь подключение мыши или приёмника."
            )
            return

        lines = ["Обнаружены устройства AJAZZ AJ199 Carbon:"]
        for key, entry in found.items():
            lines.append(
                f"\n{entry['name']}: {entry['product']} "
                f"(VID:PID {key[0]:04X}:{key[1]:04X})"
            )
            interfaces = ", ".join(
                str(number) for number in sorted(entry["interfaces"])
            )
            lines.append(f"HID-интерфейсы: {interfaces or 'не определены'}")
            lines.append(
                "Интерфейс настройки FF01:0010: "
                + ("найден" if entry["config_interface"] else "не найден")
            )

        lines.append(
            "\nОбнаружение HID не подтверждает возможность менять "
            "настройки мыши."
        )
        self.hid_result.setText("\n".join(lines))

    '''

check_method = r'''    def check_device(self):
        self.scan_hid_devices()
        QMessageBox.information(
            self, "Проверка устройства", self.hid_result.text()
        )

    '''

updated = replace_method(source, "scan_hid_devices", scan_method)
updated = replace_method(updated, "check_device", check_method)

compile(updated, str(path), "exec")
path.write_text(updated, encoding="utf-8")
print("Готово: функции обновлены, синтаксис проверен.")
