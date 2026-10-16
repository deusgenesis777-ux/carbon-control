import sys, json
from pathlib import Path
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QComboBox,
    QSlider, QLineEdit, QCheckBox, QMessageBox, QInputDialog, QScrollArea, QColorDialog, QSpinBox
)

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "settings.json"

DEFAULTS = {
    "app_name": "CARBON CONTROL",
    "accent": "#8b5cf6",
    "theme": "Авто (Windows)",
    "density": "Полная",
    "sidebar_size": "Стандартная",
    "ui_scale": 100,
    "show_tips": True,
    "active_profile": "Default",
    "dpi_display": 1200,
    "dpi_steps": [800, 1200, 1600, 2400],
    "active_dpi_step": 1,
    "polling_rate_display": 1000,
    "profiles": {
        "Default": {"dpi": 1200},
        "Gaming": {"dpi": 1600},
        "Precision": {"dpi": 800}
    }
}

ACCENTS = {
    "Фиолетовый": "#8b5cf6",
    "Синий": "#4f8cff",
    "Бирюзовый": "#22d3ee",
    "Зелёный": "#22c55e",
    "Оранжевый": "#f59e0b",
    "Розовый": "#ec4899",
    "Красный": "#ef4444"
}

def load_settings():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        merged = DEFAULTS.copy()
        merged.update(data)
        if not isinstance(merged.get("profiles"), dict) or not merged["profiles"]:
            merged["profiles"] = DEFAULTS["profiles"].copy()
        return merged
    except Exception:
        return json.loads(json.dumps(DEFAULTS))

def save_settings(data):
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class MouseTestSurface(QFrame):
    """Interactive area that records real mouse events received by the OS/app."""
    def __init__(self, report, parent=None):
        super().__init__(parent)
        self.report = report
        self.setObjectName("mouseTestSurface")
        self.setMouseTracking(True)
        self.setMinimumHeight(170)
        self.setCursor(Qt.CrossCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        title = QLabel("ТЕСТОВАЯ ОБЛАСТЬ")
        title.setObjectName("testSurfaceTitle")
        title.setAlignment(Qt.AlignCenter)
        help_text = QLabel("Двигай мышь здесь, нажимай левую/правую/среднюю кнопки и прокручивай колесо")
        help_text.setWordWrap(True)
        help_text.setAlignment(Qt.AlignCenter)
        help_text.setObjectName("muted")
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(help_text)
        layout.addStretch(1)

    def mouseMoveEvent(self, event):
        self.report("movement", "Движение мыши", f"X: {int(event.position().x())}, Y: {int(event.position().y())}")
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        mapping = {
            Qt.LeftButton: ("left", "Левая кнопка"),
            Qt.RightButton: ("right", "Правая кнопка"),
            Qt.MiddleButton: ("middle", "Нажатие колеса"),
            Qt.XButton1: ("side1", "Боковая кнопка 1"),
            Qt.XButton2: ("side2", "Боковая кнопка 2"),
        }
        item = mapping.get(event.button())
        if item:
            self.report(item[0], item[1], "Нажатие обнаружено")
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        direction = "вверх" if delta > 0 else "вниз" if delta < 0 else "без изменения"
        self.report("wheel", "Колесо прокрутки", f"Прокрутка {direction} ({delta})")
        super().wheelEvent(event)


class CarbonWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.settings.setdefault("dpi_steps", [800, 1200, 1600, 2400])
        self.settings.setdefault("active_dpi_step", 1)
        self.settings.setdefault("polling_rate_display", 1000)
        if not isinstance(self.settings.get("dpi_steps"), list) or len(self.settings["dpi_steps"]) != 4:
            self.settings["dpi_steps"] = [800, 1200, 1600, 2400]
        self.settings["dpi_steps"] = [max(200, min(12000, int(v))) for v in self.settings["dpi_steps"]]
        self.settings["active_dpi_step"] = max(0, min(3, int(self.settings.get("active_dpi_step", 1))))
        self.setWindowTitle(self.settings.get("app_name", "CARBON CONTROL"))
        app_icon = APP_DIR / "icons" / "ico" / "dark" / "dashboard.ico"
        if app_icon.is_file():
            self.setWindowIcon(QIcon(str(app_icon)))
        # Фиксированный размер для стабильной компоновки без обрезания карточек.
        # Размер соответствует проверенному пользователем расположению окна.
        self.setFixedSize(1060, 700)
        self.pages = {}
        self.nav_buttons = {}
        self.build_ui()
        self.apply_theme()
        self._applied_dark = self._resolve_dark_theme()
        self._theme_timer = QTimer(self)
        self._theme_timer.setInterval(3000)
        self._theme_timer.timeout.connect(self.refresh_system_theme)
        self._theme_timer.start()
        self.show_page("Overview")

    def scaled(self, n):
        return max(1, round(n * self.settings.get("ui_scale", 100) / 100))

    def build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(228)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(15, 16, 15, 12)
        side.setSpacing(8)

        brand_row = QHBoxLayout()
        logo = QLabel("C")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(42, 42)
        brand_col = QVBoxLayout()
        self.brand = QLabel(self.settings.get("app_name", "CARBON CONTROL"))
        self.brand.setObjectName("brand")
        self.brand.setWordWrap(True)
        sub = QLabel("DEVICE SUITE  •  BETA")
        sub.setObjectName("subbrand")
        brand_col.addWidget(self.brand)
        brand_col.addWidget(sub)
        brand_row.addWidget(logo)
        brand_row.addSpacing(10)
        brand_row.addLayout(brand_col, 1)
        side.addLayout(brand_row)
        side.addSpacing(20)

        section = QLabel("УСТРОЙСТВО")
        section.setObjectName("section")
        side.addWidget(section)
        nav_items = [
            ("Overview", "home", "Обзор"),
            ("DPI", "dpi", "DPI и чувствительность"),
            ("Performance", "speed", "Производительность"),
            ("MouseTest", "mouse", "Проверка мыши"),
            ("Profiles", "profiles", "Профили"),
            ("Personalization", "color", "Персонализация"),
            ("Settings", "settings", "Настройки")
        ]
        for key, icon, label in nav_items:
            b = QPushButton(label)
            icon_aliases = {"home": "dashboard", "dpi": "gauge", "speed": "activity",
                            "mouse": "mouse", "profiles": "clipboard-check",
                            "color": "sliders", "settings": "settings"}
            icon_name = icon_aliases.get(icon, icon)
            icon_path = APP_DIR / "icons" / "png" / self.current_icon_theme() / f"{icon_name}-20.png"
            if not icon_path.is_file():
                icon_path = APP_DIR / "icons" / f"{icon}.png"
            if icon_path.is_file():
                b.setIcon(QIcon(str(icon_path)))
                b.setIconSize(QSize(16, 16))
            b.setObjectName("nav")
            b.setProperty("nav_icon", icon)
            b.setProperty("nav_label", label)
            b.setToolTip(label)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked=False, k=key: self.show_page(k))
            side.addWidget(b)
            self.nav_buttons[key] = b
        side.addStretch(1)
        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        sc = QVBoxLayout(self.status_card)
        sc.setContentsMargins(12, 12, 12, 12)
        self.status_dot = QLabel("●  Ожидание HID-проверки")
        self.status_dot.setObjectName("muted")
        self.status_note = QLabel("Настройки сохраняются локально")
        self.status_note.setObjectName("tiny")
        self.status_note.setWordWrap(True)
        sc.addWidget(self.status_dot)
        sc.addWidget(self.status_note)
        side.addWidget(self.status_card)
        side.addWidget(QLabel("CARBON CONTROL • LOCAL", objectName="tiny"))
        outer.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        self.pages["Overview"] = self.page_overview()
        self.pages["DPI"] = self.page_dpi()
        self.pages["Performance"] = self.page_performance()
        self.pages["MouseTest"] = self.page_mouse_test()
        self.pages["Profiles"] = self.page_profiles()
        self.pages["Personalization"] = self.page_personalization()
        self.pages["Settings"] = self.page_settings()
        for page in self.pages.values():
            self.stack.addWidget(page)

    def page_shell(self, breadcrumb, title, description):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page = QWidget()
        page.setObjectName("pageContent")
        scroll.setWidget(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        crumb = QLabel("Устройство   /   " + breadcrumb)
        crumb.setObjectName("breadcrumb")
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        desc = QLabel(description)
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        layout.addWidget(crumb)
        layout.addSpacing(3)
        layout.addWidget(heading)
        layout.addWidget(desc)
        return scroll, layout

    def card(self, title=None):
        frame = QFrame()
        frame.setObjectName("card")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 13, 16, 13)
        lay.setSpacing(9)
        if title:
            t = QLabel(title)
            t.setObjectName("cardTitle")
            lay.addWidget(t)
        return frame, lay

    def page_overview(self):
        p, l = self.page_shell(
            "Обзор", "Обзор устройства",
            "Состояние мыши и быстрый доступ к основным функциям."
        )
        l.setContentsMargins(16, 12, 16, 14)
        l.setSpacing(10)

        # Верхняя панель устройства
        hero, hl = self.card()
        hero.setObjectName("dashboardHero")
        hero_row = QHBoxLayout()
        hero_row.setSpacing(14)
        left = QVBoxLayout()
        left.setSpacing(7)

        eyebrow = QLabel("WIRELESS GAMING MOUSE  /  AJAZZ")
        eyebrow.setObjectName("eyebrow")
        name = QLabel("AJ199 Carbon")
        name.setObjectName("dashboardHeroTitle")
        subtitle = QLabel("Локальная панель управления устройством")
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)

        state = QLabel("●  Статус устройства требует проверки")
        state.setObjectName("dashboardStatus")
        state.setWordWrap(True)
        self.device_status_label = state

        battery = QLabel("Заряд батареи: нет данных")
        battery.setObjectName("muted")
        battery.setWordWrap(True)
        self.device_battery_label = battery

        check = QPushButton("Проверить подключение")
        self.set_button_icon(check, "mouse", 18)
        check.setObjectName("primary")
        check.clicked.connect(self.check_device)

        left.addWidget(eyebrow)
        left.addWidget(name)
        left.addWidget(subtitle)
        left.addWidget(state)
        left.addWidget(battery)
        left.addSpacing(2)
        left.addWidget(check, 0, Qt.AlignLeft)
        hero_row.addLayout(left, 3)

        mouse = QLabel("AJ199")
        mouse.setObjectName("dashboardMouseArt")
        mouse.setAlignment(Qt.AlignCenter)
        mouse.setMinimumWidth(100)
        mouse.setMaximumWidth(150)
        hero_row.addWidget(mouse, 1)
        hl.addLayout(hero_row)
        l.addWidget(hero)

        # Карточки второго уровня: значения, которые действительно есть в приложении.
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        dpi, dl = self.card()
        dpi.setObjectName("dashboardMetricCard")
        dpi_head = QHBoxLayout()
        dpi_icon = QLabel("◎")
        dpi_icon.setObjectName("dashboardGlyphCyan")
        dpi_title = QLabel("Чувствительность")
        dpi_title.setObjectName("cardTitle")
        dpi_head.addWidget(dpi_icon)
        dpi_head.addWidget(dpi_title, 1)
        dl.addLayout(dpi_head)
        self.overview_dpi = QLabel(f"{self.settings.get('dpi_display', 1200):,} DPI".replace(",", " "))
        self.overview_dpi.setObjectName("dashboardMetric")
        dnote = QLabel("Локальное значение, не подтверждено мышью")
        dnote.setObjectName("muted")
        dnote.setWordWrap(True)
        db = QPushButton("Настроить DPI  ›")
        db.clicked.connect(lambda: self.show_page("DPI"))
        dl.addWidget(self.overview_dpi)
        dl.addWidget(dnote)
        dl.addStretch(1)
        dl.addWidget(db, 0, Qt.AlignLeft)

        prof, pl = self.card()
        prof.setObjectName("dashboardMetricCard")
        prof_head = QHBoxLayout()
        prof_icon = QLabel("▱")
        prof_icon.setObjectName("dashboardGlyphPurple")
        prof_title = QLabel("Активный профиль")
        prof_title.setObjectName("cardTitle")
        prof_head.addWidget(prof_icon)
        prof_head.addWidget(prof_title, 1)
        pl.addLayout(prof_head)
        self.overview_profile = QLabel(self.settings.get("active_profile", "Default"))
        self.overview_profile.setObjectName("dashboardMetricSmall")
        pnote = QLabel("Сохранённая локальная конфигурация")
        pnote.setObjectName("muted")
        pnote.setWordWrap(True)
        pb = QPushButton("Управление профилями  ›")
        pb.clicked.connect(lambda: self.show_page("Profiles"))
        pl.addWidget(self.overview_profile)
        pl.addWidget(pnote)
        pl.addStretch(1)
        pl.addWidget(pb, 0, Qt.AlignLeft)

        perf, pfl = self.card()
        perf.setObjectName("dashboardMetricCard")
        perf_head = QHBoxLayout()
        perf_icon = QLabel("⌁")
        perf_icon.setObjectName("dashboardGlyphGreen")
        perf_title = QLabel("Производительность")
        perf_title.setObjectName("cardTitle")
        perf_head.addWidget(perf_icon)
        perf_head.addWidget(perf_title, 1)
        pfl.addLayout(perf_head)
        perf_value = QLabel("HID не подтверждён")
        perf_value.setObjectName("dashboardMetricSmall")
        perf_note = QLabel("Частота опроса и аппаратные показатели пока недоступны.")
        perf_note.setObjectName("muted")
        perf_note.setWordWrap(True)
        perf_button = QPushButton("Подробнее  ›")
        perf_button.clicked.connect(lambda: self.show_page("Performance"))
        pfl.addWidget(perf_value)
        pfl.addWidget(perf_note)
        pfl.addStretch(1)
        pfl.addWidget(perf_button, 0, Qt.AlignLeft)

        diag, dgl = self.card()
        diag.setObjectName("dashboardMetricCard")
        diag_head = QHBoxLayout()
        diag_icon = QLabel("◉")
        diag_icon.setObjectName("dashboardGlyphCyan")
        diag_title = QLabel("Диагностика мыши")
        diag_title.setObjectName("cardTitle")
        diag_head.addWidget(diag_icon)
        diag_head.addWidget(diag_title, 1)
        dgl.addLayout(diag_head)
        diag_note = QLabel("Проверка движения, кнопок и колёсика по реальным событиям Windows.")
        diag_note.setObjectName("muted")
        diag_note.setWordWrap(True)
        diag_button = QPushButton("Запустить тесты  ›")
        diag_button.setObjectName("primary")
        diag_button.clicked.connect(lambda: self.show_page("MouseTest"))
        dgl.addWidget(diag_note)
        dgl.addStretch(1)
        dgl.addWidget(diag_button, 0, Qt.AlignLeft)

        grid.addWidget(dpi, 0, 0)
        grid.addWidget(prof, 0, 1)
        grid.addWidget(perf, 1, 0)
        grid.addWidget(diag, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        l.addLayout(grid)

        if self.settings.get("show_tips", True):
            tip, tl = self.card()
            tip.setObjectName("dashboardNotice")
            tip_row = QHBoxLayout()
            info = QLabel("ⓘ")
            info.setObjectName("dashboardGlyphPurple")
            tip_text = QLabel(
                "Важно: обнаружение USB HID и отправка команд настройки — разные задачи. "
                "До подтверждения протокола приложение не отправляет команды мыши."
            )
            tip_text.setObjectName("muted")
            tip_text.setWordWrap(True)
            tip_row.addWidget(info)
            tip_row.addWidget(tip_text, 1)
            tl.addLayout(tip_row)
            l.addWidget(tip)
        l.addStretch(1)
        return p

    def page_dpi(self):
        p, l = self.page_shell(
            "DPI", "DPI и чувствительность",
            "Настрой локальные ступени чувствительности. Аппаратное применение AJAZZ AJ199 пока не подтверждено."
        )
        current, current_l = self.card("Текущая чувствительность")
        current_row = QHBoxLayout()
        self.dpi_value = QLabel(f"{self.settings.get('dpi_display', 1200):,} DPI".replace(",", " "))
        self.dpi_value.setObjectName("metric")
        current_row.addWidget(self.dpi_value, 1)
        self.dpi_numeric = QSpinBox()
        self.dpi_numeric.setRange(200, 12000)
        self.dpi_numeric.setSingleStep(100)
        self.dpi_numeric.setSuffix(" DPI")
        self.dpi_numeric.setFixedWidth(150)
        self.dpi_numeric.setValue(max(200, min(12000, int(self.settings.get("dpi_display", 1200)))))
        self.dpi_numeric.valueChanged.connect(self.sync_dpi_controls)
        current_row.addWidget(self.dpi_numeric)
        current_l.addLayout(current_row)
        self.dpi_slider = QSlider(Qt.Horizontal)
        self.dpi_slider.setRange(200, 12000)
        self.dpi_slider.setSingleStep(100)
        self.dpi_slider.setPageStep(400)
        self.dpi_slider.setValue(self.dpi_numeric.value())
        self.dpi_slider.valueChanged.connect(self.sync_dpi_from_slider)
        current_l.addWidget(self.dpi_slider)
        scale_labels = QHBoxLayout()
        scale_labels.addWidget(QLabel("200 DPI"))
        scale_labels.addStretch()
        scale_labels.addWidget(QLabel("12 000 DPI"))
        current_l.addLayout(scale_labels)
        l.addWidget(current)

        steps_card, steps_l = self.card("DPI-ступени")
        hint = QLabel("Измени значения ступеней и выбери активную. Значения хранятся в профиле приложения.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        steps_l.addWidget(hint)
        steps_grid = QGridLayout()
        steps_grid.setSpacing(8)
        self.dpi_step_spins, self.dpi_step_buttons = [], []
        steps = self.settings.get("dpi_steps", [800, 1200, 1600, 2400])
        active = self.settings.get("active_dpi_step", 1)
        for idx in range(4):
            cell = QFrame()
            cell.setObjectName("dpiStepCard")
            cell_l = QVBoxLayout(cell)
            cell_l.setContentsMargins(8, 8, 8, 8)
            cell_l.setSpacing(5)
            title = QLabel(f"СТУПЕНЬ {idx + 1}")
            title.setObjectName("muted")
            spin = QSpinBox()
            spin.setRange(200, 12000)
            spin.setSingleStep(100)
            spin.setSuffix(" DPI")
            spin.setValue(int(steps[idx]))
            spin.valueChanged.connect(lambda value, i=idx: self.update_dpi_step(i, value))
            btn = QPushButton("Активная" if idx == active else "Выбрать")
            btn.setCheckable(True)
            btn.setChecked(idx == active)
            btn.clicked.connect(lambda checked=False, i=idx: self.select_dpi_step(i))
            self.dpi_step_spins.append(spin)
            self.dpi_step_buttons.append(btn)
            cell_l.addWidget(title)
            cell_l.addWidget(spin)
            cell_l.addWidget(btn)
            steps_grid.addWidget(cell, idx // 2, idx % 2)
        steps_l.addLayout(steps_grid)
        l.addWidget(steps_card)

        polling_card, polling_l = self.card("Частота опроса")
        polling_note = QLabel("Выбор сохраняется локально. Приложение пока не подтверждает и не меняет частоту опроса самой мыши.")
        polling_note.setObjectName("muted")
        polling_note.setWordWrap(True)
        polling_l.addWidget(polling_note)
        poll_row = QHBoxLayout()
        poll_row.addWidget(QLabel("Желаемое значение"))
        self.polling = QComboBox()
        self.polling.addItems(["125 Гц", "250 Гц", "500 Гц", "1000 Гц"])
        rates = [125, 250, 500, 1000]
        saved_rate = int(self.settings.get("polling_rate_display", 1000))
        self.polling.setCurrentIndex(rates.index(saved_rate) if saved_rate in rates else 3)
        poll_row.addWidget(self.polling, 1)
        self.polling_status = QLabel("Не применено к устройству")
        self.polling_status.setObjectName("muted")
        poll_row.addWidget(self.polling_status)
        polling_l.addLayout(poll_row)
        l.addWidget(polling_card)

        actions = QHBoxLayout()
        apply_btn = QPushButton("ПРИМЕНИТЬ")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self.apply_dpi_settings)
        save_btn = QPushButton("СОХРАНИТЬ ПРОФИЛЬ")
        save_btn.clicked.connect(self.save_dpi)
        reset_btn = QPushButton("СБРОСИТЬ")
        reset_btn.clicked.connect(self.reset_dpi_settings)
        actions.addWidget(apply_btn)
        actions.addWidget(save_btn)
        actions.addWidget(reset_btn)
        actions.addStretch()
        l.addLayout(actions)

        status_card, status_l = self.card("Состояние устройства")
        self.dpi_device_status = QLabel("Управление не подтверждено: настройки пока сохраняются только в приложении.")
        self.dpi_device_status.setObjectName("muted")
        self.dpi_device_status.setWordWrap(True)
        status_l.addWidget(self.dpi_device_status)
        l.addWidget(status_card)
        l.addStretch()
        return p

    def page_performance(self):
        p, l = self.page_shell("Производительность", "Производительность", "Параметры и диагностика устройства.")
        c, cl = self.card("Частота опроса")
        msg = QLabel("Частота опроса отображается как неподтверждённая: сначала нужно определить HID-интерфейс и протокол AJ199 Carbon.")
        msg.setObjectName("muted")
        msg.setWordWrap(True)
        cl.addWidget(msg)
        self.polling = QComboBox()
        self.polling.addItems(["Не определена", "125 Гц", "250 Гц", "500 Гц", "1000 Гц"])
        self.polling.setCurrentIndex(0)
        self.polling.setEnabled(False)
        cl.addWidget(QLabel("Частота опроса"))
        cl.addWidget(self.polling)
        l.addWidget(c)
        l.addStretch()
        return p

    def page_mouse_test(self):
        p, l = self.page_shell("Проверка мыши", "Тест исправности мыши", "Проверь основные физические элементы. Тест фиксирует события, поступающие в Windows и приложение; он не измеряет электрическое состояние датчика.")
        c, cl = self.card("Ввод мыши")
        intro = QLabel("По очереди проверь движение, левую и правую кнопки, нажатие колеса, прокрутку и боковые кнопки (если они есть). Для боковых кнопок нажимай их, находясь курсором над областью ниже.")
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        cl.addWidget(intro)
        self.mouse_test_area = MouseTestSurface(self.record_mouse_test)
        cl.addWidget(self.mouse_test_area)
        grid = QGridLayout()
        grid.setSpacing(8)
        self.mouse_test_status = {}
        checks = [
            ("movement", "Движение мыши"), ("left", "Левая кнопка"),
            ("right", "Правая кнопка"), ("middle", "Нажатие колеса"),
            ("wheel", "Прокрутка колеса"), ("side1", "Боковая кнопка 1"),
            ("side2", "Боковая кнопка 2")]
        for idx, (key, label) in enumerate(checks):
            cell = QFrame()
            cell.setObjectName("testStatus")
            row = QHBoxLayout(cell)
            row.setContentsMargins(10, 7, 10, 7)
            icon = QLabel("○")
            icon.setObjectName("testMark")
            text = QLabel(label + " — не проверено (0)")
            text.setWordWrap(True)
            row.addWidget(icon)
            row.addWidget(text, 1)
            grid.addWidget(cell, idx // 2, idx % 2)
            self.mouse_test_status[key] = (icon, text, label, 0)
        cl.addLayout(grid)
        actions = QHBoxLayout()
        reset = QPushButton("Сбросить результаты")
        self.set_button_icon(reset, "reset", 18)
        reset.clicked.connect(self.reset_mouse_test)
        actions.addWidget(reset)
        scan = QPushButton("Проверить USB HID")
        self.set_button_icon(scan, "search", 18)
        scan.setObjectName("primary")
        scan.clicked.connect(self.scan_hid_devices)
        actions.addWidget(scan)
        actions.addStretch(1)
        cl.addLayout(actions)
        l.addWidget(c)
        self.hid_result = QLabel("USB HID ещё не проверялся. Проверка не меняет настройки мыши.")
        self.hid_result.setObjectName("muted")
        self.hid_result.setWordWrap(True)
        hid_card, hid_layout = self.card("Обнаружение устройства")
        hid_layout.addWidget(self.hid_result)
        l.addWidget(hid_card)
        note, nl = self.card("Что этот тест проверяет")
        note_text = QLabel("Проверяются только события, которые Windows передаёт приложению. Если кнопка не сработала, это может быть связано с фокусом окна, драйвером или настройками ОС. Тест не может подтвердить состояние оптического сенсора на аппаратном уровне и не отправляет команды настройки мыши.")
        note_text.setObjectName("muted")
        note_text.setWordWrap(True)
        nl.addWidget(note_text)
        l.addStretch(1)
        return p

    def record_mouse_test(self, key, label, detail):
        if key not in self.mouse_test_status:
            return
        icon, text, original, count = self.mouse_test_status[key]
        count += 1
        self.mouse_test_status[key] = (icon, text, original, count)
        icon.setText("✓")
        text.setText(f"{original} — обнаружено ({count})")
        text.setToolTip(f"Последнее событие: {detail}\nВсего событий: {count}")
        self.status_note.setText(f"Диагностика: {label}; событий: {count}")

    def reset_mouse_test(self):
        for key, (icon, text, label, _count) in list(self.mouse_test_status.items()):
            icon.setText("○")
            text.setText(label + " — не проверено (0)")
            text.setToolTip("")
            self.mouse_test_status[key] = (icon, text, label, 0)
        self.hid_result.setText("USB HID ещё не проверялся. Проверка не меняет настройки мыши.")

    def scan_hid_devices(self):
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
        self.detected_device_modes = []

        for device in devices:
            key = (
                int(device.get("vendor_id", 0) or 0),
                int(device.get("product_id", 0) or 0),
            )
            if key not in known:
                continue

            if key not in self.detected_device_modes:
                self.detected_device_modes.append({
                    "id": key,
                    "name": known[key],
                })

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

    def page_profiles(self):
        p, l = self.page_shell("Профили", "Профили", "Создавай отдельные локальные настройки под разные сценарии.")
        c, cl = self.card("Активный профиль")
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(list(self.settings["profiles"].keys()))
        active = self.settings.get("active_profile", "Default")
        if active in self.settings["profiles"]:
            self.profile_combo.setCurrentText(active)
        self.profile_combo.currentTextChanged.connect(self.select_profile_preview)
        cl.addWidget(QLabel("Выбери профиль"))
        cl.addWidget(self.profile_combo)
        buttons = QHBoxLayout()
        apply_b = QPushButton("Выбрать профиль")
        self.set_button_icon(apply_b, "apply", 20)
        apply_b.setObjectName("primary")
        apply_b.clicked.connect(self.apply_profile)
        create_b = QPushButton("Создать профиль")
        create_b.clicked.connect(self.create_profile)
        rename_b = QPushButton("Переименовать")
        rename_b.clicked.connect(self.rename_profile)
        delete_b = QPushButton("Удалить")
        delete_b.clicked.connect(self.delete_profile)
        for b in (apply_b, create_b, rename_b, delete_b):
            buttons.addWidget(b)
        cl.addLayout(buttons)
        self.profile_detail = QLabel("")
        self.profile_detail.setObjectName("muted")
        cl.addWidget(self.profile_detail)
        l.addWidget(c)
        note, nl = self.card("Как это работает")
        n = QLabel("Профили сохраняются в settings.json на этом компьютере. До подтверждения протокола они не отправляют команды мыши.")
        n.setObjectName("muted")
        n.setWordWrap(True)
        nl.addWidget(n)
        l.addWidget(note)
        l.addStretch()
        self.select_profile_preview(self.profile_combo.currentText())
        return p

    def page_personalization(self):
        p, l = self.page_shell("Персонализация", "Персонализация", "Настрой внешний вид Carbon Control под себя.")
        c, cl = self.card("Внешний вид")
        cl.addWidget(QLabel("Цвет акцента"))
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(list(ACCENTS.keys()))
        current_accent = self.settings.get("accent", DEFAULTS["accent"])
        accent_name = next((k for k, v in ACCENTS.items() if v.lower() == current_accent.lower()), "Фиолетовый")
        self.accent_combo.setCurrentText(accent_name)
        cl.addWidget(self.accent_combo)
        self.custom_color_button = QPushButton("Выбрать собственный цвет…")
        self.set_button_icon(self.custom_color_button, "color", 20)
        self.custom_color_button.clicked.connect(self.choose_custom_color)
        cl.addWidget(self.custom_color_button)
        cl.addWidget(QLabel("Тема"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Авто (Windows)", "Тёмная", "Светлая"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "Тёмная"))
        cl.addWidget(self.theme_combo)
        cl.addWidget(QLabel("Режим боковой панели"))
        self.density_combo = QComboBox()
        self.density_combo.addItems(["Полная", "Компактная"] )
        self.density_combo.setCurrentText(self.settings.get("density", "Полная"))
        cl.addWidget(self.density_combo)
        cl.addWidget(QLabel("Размер боковой панели"))
        self.sidebar_size_combo = QComboBox()
        self.sidebar_size_combo.addItems(["Узкая", "Стандартная", "Широкая"])
        self.sidebar_size_combo.setCurrentText(self.settings.get("sidebar_size", "Стандартная"))
        cl.addWidget(self.sidebar_size_combo)
        cl.addWidget(QLabel("Масштаб интерфейса"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(80, 125)
        self.scale_slider.setSingleStep(5)
        self.scale_slider.setValue(int(self.settings.get("ui_scale", 100)))
        self.scale_label = QLabel(f"{self.scale_slider.value()}%")
        self.scale_slider.valueChanged.connect(lambda v: self.scale_label.setText(f"{v}%"))
        cl.addWidget(self.scale_slider)
        cl.addWidget(self.scale_label)
        cl.addWidget(QLabel("Название в боковой панели"))
        self.app_name_input = QLineEdit(self.settings.get("app_name", "CARBON CONTROL"))
        self.app_name_input.setMaxLength(28)
        cl.addWidget(self.app_name_input)
        self.tips_check = QCheckBox("Показывать предупреждения и подсказки на главной")
        self.tips_check.setChecked(bool(self.settings.get("show_tips", True)))
        cl.addWidget(self.tips_check)
        save = QPushButton("СОХРАНИТЬ И ПРИМЕНИТЬ")
        save.setObjectName("primary")
        save.clicked.connect(self.apply_personalization)
        cl.addWidget(save, 0, Qt.AlignLeft)
        l.addWidget(c)
        l.addStretch()
        return p

    def page_settings(self):
        p, l = self.page_shell("Настройки", "Настройки приложения", "Локальное хранение и информация о текущей сборке.")
        c, cl = self.card("Хранение")
        msg = QLabel(f"Файл настроек:\n{CONFIG_PATH}\n\nТема, цвет акцента, масштаб, название приложения и профили хранятся локально.")
        msg.setObjectName("muted")
        msg.setWordWrap(True)
        cl.addWidget(msg)
        reset = QPushButton("СБРОСИТЬ ПЕРСОНАЛИЗАЦИЮ")
        self.set_button_icon(reset, "reset", 20)
        reset.clicked.connect(self.reset_settings)
        cl.addWidget(reset, 0, Qt.AlignLeft)
        l.addWidget(c)
        info, il = self.card("О прототипе")
        i = QLabel("Carbon Control • AJAZZ AJ199 Carbon\nИнтерфейс настроек готов; реальное управление устройством требует подтверждённого HID-протокола.")
        i.setObjectName("muted")
        i.setWordWrap(True)
        il.addWidget(i)
        l.addWidget(info)
        l.addStretch()
        return p

    def current_icon_theme(self):
        return "dark" if self._resolve_dark_theme() else "light"

    def themed_icon_path(self, icon_name, size=20):
        theme = self.current_icon_theme()
        path = APP_DIR / "icons" / "png" / theme / f"{icon_name}-{size}.png"
        if not path.is_file():
            path = APP_DIR / "icons" / "ico" / theme / f"{icon_name}.ico"
        return path

    def set_button_icon(self, button, icon_name, size=20):
        """Загружает компактную цветную иконку из набора для текущей темы Windows."""
        aliases = {"apply": "check-circle", "reset": "refresh", "color": "sliders"}
        icon_name = aliases.get(icon_name, icon_name)
        path = self.themed_icon_path(icon_name, size)
        if path.is_file():
            button.setIcon(QIcon(str(path)))
            button.setIconSize(QSize(size, size))
            button.setProperty("asset_icon", icon_name)

    def refresh_themed_icons(self):
        aliases = {"home": "dashboard", "dpi": "gauge", "speed": "activity",
                   "mouse": "mouse", "profiles": "clipboard-check",
                   "color": "sliders", "settings": "settings"}
        for button in getattr(self, "nav_buttons", {}).values():
            name = aliases.get(button.property("nav_icon"), button.property("nav_icon"))
            path = self.themed_icon_path(name, 20)
            if path.is_file():
                button.setIcon(QIcon(str(path)))
                button.setIconSize(QSize(16, 16))
        # Refresh icons for action buttons that use the shared helper.
        for button in self.findChildren(QPushButton):
            old_icon = button.icon()
            if old_icon.isNull():
                continue
            name = button.property("asset_icon")
            if name:
                path = self.themed_icon_path(name, 20)
                if path.is_file():
                    button.setIcon(QIcon(str(path)))
                    button.setIconSize(QSize(16, 16))

    def show_page(self, key):
        self.stack.setCurrentWidget(self.pages[key])
        for k, b in self.nav_buttons.items():
            b.setProperty("active", k == key)
            b.style().unpolish(b)
            b.style().polish(b)

    def sync_dpi_controls(self, value):
        if hasattr(self, "dpi_slider") and self.dpi_slider.value() != value:
            self.dpi_slider.blockSignals(True)
            self.dpi_slider.setValue(value)
            self.dpi_slider.blockSignals(False)
        if hasattr(self, "dpi_value"):
            self.dpi_value.setText(f"{value:,} DPI".replace(",", " "))

    def sync_dpi_from_slider(self, value):
        if hasattr(self, "dpi_numeric") and self.dpi_numeric.value() != value:
            self.dpi_numeric.blockSignals(True)
            self.dpi_numeric.setValue(value)
            self.dpi_numeric.blockSignals(False)
        self.dpi_value.setText(f"{value:,} DPI".replace(",", " "))

    def update_dpi_step(self, index, value):
        steps = self.settings.setdefault("dpi_steps", [800, 1200, 1600, 2400])
        steps[index] = int(value)
        if self.settings.get("active_dpi_step", 1) == index:
            self.sync_dpi_controls(value)

    def select_dpi_step(self, index):
        self.settings["active_dpi_step"] = index
        value = self.dpi_step_spins[index].value()
        for i, button in enumerate(self.dpi_step_buttons):
            button.setChecked(i == index)
            button.setText("Активная" if i == index else "Выбрать")
        self.sync_dpi_controls(value)

    def apply_dpi_settings(self):
        value = self.dpi_numeric.value()
        self.settings["dpi_display"] = value
        self.settings["dpi_steps"] = [spin.value() for spin in self.dpi_step_spins]
        self.settings["active_dpi_step"] = next(
            (i for i, button in enumerate(self.dpi_step_buttons) if button.isChecked()), 1
        )
        self.settings["polling_rate_display"] = int(self.polling.currentText().split()[0])
        active = self.settings.get("active_profile", "Default")
        profile = self.settings["profiles"].setdefault(active, {})
        profile["dpi"] = value
        profile["dpi_steps"] = list(self.settings["dpi_steps"])
        profile["active_dpi_step"] = self.settings["active_dpi_step"]
        profile["polling_rate_display"] = self.settings["polling_rate_display"]
        save_settings(self.settings)
        self.overview_dpi.setText(f"{value:,} DPI".replace(",", " "))
        self.dpi_device_status.setText(
            "Локальные настройки сохранены. Реальное применение DPI и частоты опроса к AJAZZ AJ199 не подтверждено."
        )
        self.polling_status.setText("Не применено к устройству")
        QMessageBox.information(self, "Настройки сохранены",
            "Настройки сохранены локально. Приложение пока не отправляет команды мыши.")

    def save_dpi(self):
        self.apply_dpi_settings()

    def reset_dpi_settings(self):
        defaults = [800, 1200, 1600, 2400]
        for spin, value in zip(self.dpi_step_spins, defaults):
            spin.setValue(value)
        self.select_dpi_step(1)
        self.dpi_numeric.setValue(1200)
        self.polling.setCurrentIndex(3)
        self.sync_dpi_controls(1200)

    def select_profile_preview(self, name):
        if not hasattr(self, "profile_detail") or not name:
            return
        profile = self.settings["profiles"].get(name, {})
        dpi = profile.get("dpi", self.settings.get("dpi_display", 1200))
        self.profile_detail.setText(f"Профиль: {name}    •    Локальное значение: {dpi:,} DPI".replace(",", " "))

    def apply_profile(self):
        name = self.profile_combo.currentText()
        if not name:
            return
        self.settings["active_profile"] = name
        dpi = self.settings["profiles"].get(name, {}).get("dpi", 1200)
        self.settings["dpi_display"] = dpi
        save_settings(self.settings)
        self.overview_profile.setText(name)
        self.overview_dpi.setText(f"{dpi:,} DPI".replace(",", " "))
        self.dpi_slider.setValue(dpi)
        self.dpi_value.setText(f"{dpi:,} DPI".replace(",", " "))
        QMessageBox.information(self, "Профиль выбран", f"«{name}» активен в приложении. Настройки мыши не менялись.")
        self.select_profile_preview(name)

    def create_profile(self):
        name, ok = QInputDialog.getText(self, "Новый профиль", "Название профиля:")
        name = name.strip()
        if ok and name:
            if name in self.settings["profiles"]:
                QMessageBox.warning(self, "Профиль существует", "Выбери другое название.")
                return
            self.settings["profiles"][name] = {"dpi": self.settings.get("dpi_display", 1200)}
            self.profile_combo.addItem(name)
            self.profile_combo.setCurrentText(name)
            save_settings(self.settings)
            self.select_profile_preview(name)

    def rename_profile(self):
        old = self.profile_combo.currentText()
        if not old:
            return
        new, ok = QInputDialog.getText(self, "Переименовать профиль", "Новое название:", text=old)
        new = new.strip()
        if not ok or not new or new == old:
            return
        if new in self.settings["profiles"]:
            QMessageBox.warning(self, "Профиль существует", "Такое название уже используется.")
            return
        self.settings["profiles"][new] = self.settings["profiles"].pop(old)
        if self.settings.get("active_profile") == old:
            self.settings["active_profile"] = new
        self.profile_combo.setItemText(self.profile_combo.currentIndex(), new)
        save_settings(self.settings)
        self.overview_profile.setText(self.settings.get("active_profile", "Default"))
        self.select_profile_preview(new)

    def delete_profile(self):
        name = self.profile_combo.currentText()
        if len(self.settings["profiles"]) <= 1:
            QMessageBox.warning(self, "Нельзя удалить", "Нужно оставить хотя бы один профиль.")
            return
        if QMessageBox.question(self, "Удалить профиль", f"Удалить «{name}»?") != QMessageBox.Yes:
            return
        self.settings["profiles"].pop(name, None)
        if self.settings.get("active_profile") == name:
            self.settings["active_profile"] = next(iter(self.settings["profiles"]))
        self.profile_combo.removeItem(self.profile_combo.currentIndex())
        self.profile_combo.setCurrentText(self.settings["active_profile"])
        save_settings(self.settings)
        self.overview_profile.setText(self.settings["active_profile"])
        self.select_profile_preview(self.profile_combo.currentText())

    def choose_custom_color(self):
        current = QColor(self.settings.get("accent", "#4f8cff"))
        color = QColorDialog.getColor(current, self, "Выбери цвет акцента")
        if color.isValid():
            self.settings["accent"] = color.name()
            label = "Свой цвет"
            idx = self.accent_combo.findText(label)
            if idx < 0:
                self.accent_combo.addItem(label)
                idx = self.accent_combo.findText(label)
            self.accent_combo.setCurrentIndex(idx)
            self.custom_color_button.setText(f"Свой цвет: {color.name()}")

    def apply_personalization(self):
        selected_accent = self.accent_combo.currentText()
        self.settings["accent"] = self.settings.get("accent", "#4f8cff") if selected_accent == "Свой цвет" else ACCENTS[selected_accent]
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings["density"] = self.density_combo.currentText()
        self.settings["sidebar_size"] = self.sidebar_size_combo.currentText()
        self.settings["ui_scale"] = self.scale_slider.value()
        self.settings["app_name"] = self.app_name_input.text().strip() or "CARBON CONTROL"
        self.settings["show_tips"] = self.tips_check.isChecked()
        save_settings(self.settings)
        self.brand.setText(self.settings["app_name"])
        self.setWindowTitle(self.settings["app_name"])
        self.apply_theme()
        self.apply_sidebar_layout()
        QMessageBox.information(self, "Готово", "Персонализация сохранена и применена.")

    def reset_settings(self):
        if QMessageBox.question(self, "Сброс", "Сбросить все локальные настройки и профили?") != QMessageBox.Yes:
            return
        self.settings = json.loads(json.dumps(DEFAULTS))
        save_settings(self.settings)
        QMessageBox.information(self, "Сброшено", "Настройки сброшены. Перезапусти приложение.")
        self.close()

    def check_device(self):
        self.scan_hid_devices()
        modes = getattr(self, "detected_device_modes", [])

        if any(mode.get("id") == (0xA8A5, 0x2266) for mode in modes):
            self.device_status_label.setText(
                "● Приёмник 2.4 ГГц обнаружен; связь с мышью не подтверждена"
            )
        elif any(mode.get("id") == (0xA8A4, 0x2266) for mode in modes):
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

    def apply_sidebar_layout(self):
        mode = self.settings.get("density", "Полная")
        size_name = self.settings.get("sidebar_size", "Стандартная")
        widths = {"Узкая": 190, "Стандартная": 228, "Широкая": 270}
        width = widths.get(size_name, 228)
        compact = mode in ("Компактная", "Compact")
        self.sidebar.setFixedWidth(76 if compact else width)
        # Hide the brand text and section heading in icon-only mode; retain the logo and status.
        self.brand.setVisible(not compact)
        for child in self.sidebar.findChildren(QLabel):
            if child.objectName() in ("section", "subbrand"):
                child.setVisible(not compact)
        for key, button in self.nav_buttons.items():
            label = button.property("nav_label") or key
            # Цветная PNG-иконка задаётся через QIcon; текст не должен дублировать старый символ.
            button.setText("" if compact else label)
            button.setToolTip(label)
            button.setMinimumHeight(42)
            button.setIconSize(QSize(16, 16))
            button.setProperty("compact", compact)
            button.style().unpolish(button)
            button.style().polish(button)
        self.status_note.setVisible(not compact)
        self.status_dot.setText("●" if compact else "●  Ожидание HID-проверки")

    def _resolve_dark_theme(self):
        theme = self.settings.get("theme", "Авто (Windows)")
        if theme not in ("Авто (Windows)", "Автоматически", "Auto"):
            return theme in ("Тёмная", "Dark")
        if sys.platform == "win32":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize") as key:
                    apps_use_light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return int(apps_use_light) == 0
            except Exception:
                pass
        return True

    def refresh_system_theme(self):
        if self.settings.get("theme") not in ("Авто (Windows)", "Автоматически", "Auto"):
            return
        dark = self._resolve_dark_theme()
        if dark != getattr(self, "_applied_dark", None):
            self._applied_dark = dark
            self.apply_theme()

    def apply_theme(self):
        # Tech Dashboard palette: compact technical panels, restrained surfaces and crisp borders.
        # Auto mode follows the Windows app-theme preference.
        dark = self._resolve_dark_theme()
        accent = self.settings.get("accent", "#8b5cf6")
        if dark:
            bg = "#111318"
            side = "#191b22"
            card = "#20232b"
            raised = "#292c35"
            text = "#f1eff7"
            muted = "#c4c5d0"
            border = "#414450"
            tonal = "#393047"
            input_bg = "#242731"
            selected = "#4b3d65"
        else:
            bg = "#f8f6fc"
            side = "#f0edf6"
            card = "#ffffff"
            raised = "#f0ebf8"
            text = "#1b1b22"
            muted = "#62616d"
            border = "#ded9e7"
            tonal = "#eee5fa"
            input_bg = "#f5f1fa"
            selected = "#e7daf8"
        pad = "8px"
        scale = self.settings.get("ui_scale", 100) / 100
        font = max(9, round(10 * scale))
        self.setStyleSheet(f"""
            QWidget {{ background: {bg}; color: {text}; font-family: 'Segoe UI'; font-size: {font}pt; }}
            QLabel {{ background: transparent; }}
            #root {{ background: {bg}; }}
            #sidebar {{ background: {side}; border: 0; border-right: 1px solid {border}; }}
            #logo {{ background: {accent}; color: white; border-radius: 6px; font-size: 22pt; font-weight: 800; }}
            #brand {{ font-size: 12pt; font-weight: 800; letter-spacing: .3px; }}
            #subbrand, #tiny {{ color: {muted}; font-size: 8pt; }}
            #section, #eyebrow {{ color: {accent}; font-size: 8pt; font-weight: 800; letter-spacing: 1.2px; }}
            #nav {{ text-align: left; padding: {pad} 12px; border: 1px solid transparent; border-left: 3px solid transparent; border-radius: 8px; background: transparent; font-weight: 600; min-height: 22px; }}
            #nav:hover {{ background: {raised}; border-color: {border}; border-left-color: {accent}; }}\n            #nav[compact="true"] {{ text-align: center; padding: 8px 2px; }}
            #nav[active="true"] {{ border-color: {border}; border-left: 3px solid {accent}; color: {text}; background: {raised}; font-weight: 750; }}
            #statusCard, #card {{ background: {card}; border: 1px solid {border}; border-radius: 10px; }}
            #card {{ border-top: 1px solid {border}; }}
            #heroCard {{ border: 1px solid {border}; border-radius: 12px; }}
            #statusCard {{ border-left: 1px solid {border}; }}
            #mouseTestSurface {{ background: {raised}; border: 1px dashed {border}; border-radius: 10px; }}
            #testSurfaceTitle {{ color: {accent}; font-weight: 800; letter-spacing: .6px; }}
            #testStatus {{ background: {card}; border: 1px solid {border}; border-radius: 8px; }}
            #testMark {{ color: {accent}; font-size: 15pt; font-weight: 800; }}
            #breadcrumb, #muted {{ color: {muted}; }}
            #pageTitle {{ font-size: 22pt; font-weight: 750; }}
            #cardTitle {{ font-size: 11pt; font-weight: 750; }}
            #heroTitle {{ font-size: 23pt; font-weight: 800; }}
            #metric {{ color: {accent}; font-size: 22pt; font-weight: 800; }}
            #metricSmall {{ font-size: 15pt; font-weight: 750; }}
            #mouseArt {{ font-size: 58pt; color: {accent}; }}
            QPushButton {{ background: {tonal}; border: 1px solid {border}; border-radius: 8px; padding: 6px 12px; min-height: 20px; font-weight: 650; }}
            QPushButton:hover {{ background: {selected}; border-color: {border}; }}
            QPushButton:pressed {{ background: {raised}; }}
            QPushButton#primary {{ background: {accent}; color: #ffffff; border: 0; border-radius: 8px; padding: 8px 16px; min-height: 22px; font-weight: 750; }}
            QPushButton#primary:hover {{ background: {accent}; border: 1px solid {text}; }}
            QComboBox, QLineEdit {{ background: {input_bg}; border: 1px solid {border}; border-radius: 8px; padding: 6px 10px; min-height: 24px; selection-background-color: {selected}; }}
            QComboBox:hover, QLineEdit:hover {{ border-color: {accent}; }}
            QComboBox::drop-down {{ border: 0; width: 32px; border-top-right-radius: 4px; border-bottom-right-radius: 4px; }}
            QComboBox QAbstractItemView {{ background: {card}; color: {text}; border: 1px solid {border}; border-radius: 8px; padding: 5px; selection-background-color: {selected}; }}
            QCheckBox {{ spacing: 9px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px; border: 1px solid {border}; background: {input_bg}; }}
            QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}
            QScrollArea, #pageContent {{ background: {bg}; border: 0; }}
            QScrollBar:vertical {{ background: transparent; width: 10px; margin: 3px; }}
            QScrollBar::handle:vertical {{ background: {border}; min-height: 28px; border-radius: 3px; }}
            QScrollBar::handle:vertical:hover {{ background: {muted}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QSlider::groove:horizontal {{ height: 6px; background: {border}; border-radius: 3px; }}
            QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {accent}; border: 2px solid {card}; width: 14px; height: 14px; margin: -6px 0; border-radius: 2px; }}
            #dashboardHero {{ border: 1px solid {border}; border-top: 2px solid {accent}; border-radius: 12px; }}
            #dashboardHeroTitle {{ font-size: 24pt; font-weight: 850; }}
            #dashboardStatus {{ color: {muted}; font-weight: 650; }}
            #dashboardMouseArt {{ color: {accent}; font-size: 23pt; font-weight: 800; border: 1px solid {border}; border-radius: 12px; background: {raised}; padding: 12px; }}
            #dashboardMetricCard {{ border: 1px solid {border}; border-radius: 12px; }}
            #dashboardMetric {{ color: {accent}; font-size: 22pt; font-weight: 850; }}
            #dashboardMetricSmall {{ color: {text}; font-size: 16pt; font-weight: 800; }}
            #dashboardGlyphCyan {{ color: #22d3ee; font-size: 19pt; font-weight: 800; }}
            #dashboardGlyphPurple {{ color: {accent}; font-size: 19pt; font-weight: 800; }}
            #dashboardGlyphGreen {{ color: #34d399; font-size: 19pt; font-weight: 800; }}
            #dashboardNotice {{ border: 1px solid {border}; border-left: 3px solid {accent}; border-radius: 10px; }}
        """)
        # Подключаем поставляемый Tech Dashboard QSS поверх базовых стилей приложения.
        base_stylesheet = self.styleSheet()
        theme_file = APP_DIR / "themes" / ("tech_dashboard_dark.qss" if dark else "tech_dashboard_light.qss")
        if theme_file.is_file():
            try:
                qss = theme_file.read_text(encoding="utf-8")
                # Акцент из пользовательских настроек сохраняется и в подключённой теме.
                qss = qss.replace("#38B8D7", accent).replace("#14799A", accent).replace("#168DB2", accent)
                qss = qss.replace("#55BDD9", accent).replace("#245D79", accent)
                self.setStyleSheet(base_stylesheet + "\n" + qss)
            except OSError:
                pass

        # Final rendering safeguards: prevent inherited QWidget backgrounds from
        # painting opaque horizontal bands behind page headings and descriptions.
        # Keep the scroll area's viewport and page canvas on the same surface.
        final_surface = bg
        self.setStyleSheet(self.styleSheet() + f"""
            QLabel {{ background-color: transparent; }}
            QSpinBox {{ background-color: {input_bg}; color: {text}; border: 1px solid {border}; border-radius: 7px; padding: 6px; min-height: 20px; }}
            QFrame#dpiStepCard {{ background-color: {card}; border: 1px solid {border}; border-radius: 9px; }}
            QFrame#dpiStepCard QLabel {{ background-color: transparent; }}
            QFrame#dpiStepCard QPushButton:checked {{ background-color: {accent}; color: #ffffff; border-color: {accent}; }}
            QScrollArea {{ background-color: {final_surface}; border: 0; }}
            QScrollArea::viewport {{ background-color: {final_surface}; border: 0; }}
            QWidget#pageContent {{ background-color: {final_surface}; }}
        """)
        self.refresh_themed_icons()
        self.apply_sidebar_layout()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CarbonWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
