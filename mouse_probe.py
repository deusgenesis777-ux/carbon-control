import hid

DEVICES = [(0xA8A4, "USB"), (0xA8A5, "2.4 GHz")]

for vid, mode in DEVICES:
    devices = [
        d for d in hid.enumerate(vid, 0x2266)
        if d.get("interface_number") == 2
    ]

    for info in devices:
        print(f"\n{mode}: {info.get('product_string')}")

        dev = hid.device()
        try:
            dev.open_path(info["path"])
            print("OPEN: OK")
            print("MANUFACTURER:", dev.get_manufacturer_string())
            print("PRODUCT:", dev.get_product_string())
        except Exception as exc:
            print("OPEN: ERROR", repr(exc))
        finally:
            dev.close()
