#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NOIR — «± анонимный» браузер для Linux.
Только чёрная тема. Google / Яндекс. Тумблер СРАВНИТЬ (анимированный сплит).
Куки сохраняются. История поиска скрыта и открывается клавишей Ё (` / ~).
Часы на главном экране — дот-матрица в стиле Nothing Ndot.
"""

import base64
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

from PyQt6.QtCore import (Qt, QEvent, QEasingCurve, QSize, QTimer, QUrl,
                          QVariantAnimation, pyqtSignal)
from PyQt6.QtGui import (QColor, QFont, QKeySequence, QPainter, QPalette,
                         QShortcut, QPixmap, QIcon)
from PyQt6.QtWidgets import (QApplication, QButtonGroup, QFileDialog,
                             QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMainWindow, QMessageBox,
                             QProgressBar, QPushButton, QStackedWidget,
                             QVBoxLayout, QWidget)
from PyQt6.QtWebEngineCore import (QWebEnginePage, QWebEngineProfile,
                                   QWebEngineScript, QWebEngineSettings,
                                   QWebEngineUrlRequestInterceptor,
                                   QWebEngineDownloadItem)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# ─────────────────────────── константы ───────────────────────────

DATA_DIR = Path.home() / ".local/share/noir-browser"
ACCENT   = "#d71921"          # фирменный красный Nothing
UA       = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

HOMES = {"google": "https://www.google.com", "yandex": "https://yandex.ru"}
SEARCH = {
    "google": "https://www.google.com/search?q={}&hl=ru",
    "yandex": "https://yandex.ru/search/?text={}",
}
BADGE = {"google": "G", "yandex": "Я"}

QUICK_LINKS = [
    ("YouTube",   "https://www.youtube.com"),
    ("GitHub",    "https://github.com"),
    ("Wikipedia", "https://ru.wikipedia.org"),
    ("Habr",      "https://habr.com"),
    ("Reddit",    "https://www.reddit.com"),
    ("DDG",       "https://duckduckgo.com"),
]

# домены-трекеры (suffix-match). Щит можно выключить кнопкой ЩИТ.
TRACKERS = {
    "google-analytics.com", "analytics.google.com", "doubleclick.net",
    "googlesyndication.com", "googleadservices.com", "googletagmanager.com",
    "mc.yandex.ru", "an.yandex.ru", "yandexadexchange.net",
    "top-fwz1.mail.ru", "ad.mail.ru", "facebook.net", "facebook.com",
    "scorecardresearch.com", "hotjar.com", "mixpanel.com", "amplitude.com",
    "segment.io", "criteo.com", "adnxs.com", "pubmatic.com",
    "rubiconproject.com", "openx.net", "casalemedia.com", "smartadserver.com",
    "adriver.ru", "luxup.ru", "tns-counter.ru", "counter.rambler.ru",
    "top100.rambler.ru", "analytics.tiktok.com", "ads.yahoo.com",
    "taboola.com", "outbrain.com", "mouseflow.com", "fullstory.com",
}

# JS-щит: убираем WebRTC (утечка IP),_battery, часть fingerprint-поверхности
SHIELD_JS = """
(() => { try {
  Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
  Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
  Object.defineProperty(navigator, 'plugins', {get: () => []});
  window.RTCPeerConnection = undefined;
  window.webkitRTCPeerConnection = undefined;
  window.RTCDataChannel = undefined;
  navigator.getBattery = undefined;
} catch (e) {} })();
"""

STYLE_JS = """
(() => {
  const css = `
    html { color-scheme: dark; }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #222; border-radius: 5px; }
    ::-webkit-scrollbar-thumb:hover { background: #333; }
    ::selection { background: #d71921; color: #fff; }`;
  const s = document.createElement('style');
  s.textContent = css;
  document.documentElement.appendChild(s);
})();
"""

EDITABLE_JS = ("(() => { const a = document.activeElement; return !!(a && "
               "(a.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName))); })()")

WEEKDAYS = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
MONTHS = ["ЯНВАРЯ", "ФЕВРАЛЯ", "МАРТА", "АПРЕЛЯ", "МАЯ", "ИЮНЯ",
          "ИЮЛЯ", "АВГУСТА", "СЕНТЯБРЯ", "ОКТЯБРЯ", "НОЯБРЯ", "ДЕКАБРЯ"]

QSS = """
QWidget { background: #000; color: #e8e8e8; font-size: 13px; }
QToolTip { background: #111; color: #ddd; border: 1px solid #222; }
#Toolbar { background: #000; border-bottom: 1px solid #161616; }
#Brand { color: #fff; font-weight: bold; font-size: 14px; }
#NavBtn { background: #0a0a0a; border: 1px solid #1c1c1c; border-radius: 15px;
          color: #bbb; font-size: 15px; }
#NavBtn:hover { background: #161616; color: #fff; }
#NavBtn:pressed { background: #222; }
#SearchEdit { background: #0a0a0a; border: 1px solid #222; border-radius: 17px;
              padding: 0 16px; color: #f2f2f2; font-size: 14px;
              selection-background-color: #d71921; }
#SearchEdit:focus { border: 1px solid #3a3a3a; }
#EngineChip { background: #0a0a0a; border: 1px solid #1c1c1c; border-radius: 13px;
              color: #666; padding: 0 12px; font-size: 11px; }
#EngineChip:checked { color: #fff; border-color: #444; }
#EngineChip:disabled { color: #333; border-color: #141414; }
#CompareBtn { background: #0a0a0a; border: 1px solid #222; border-radius: 17px;
              color: #888; padding: 0 16px; font-size: 12px; font-weight: bold; }
#CompareBtn:hover { color: #ccc; }
#CompareBtn:checked { color: #d71921; border-color: #d71921; }
#ShieldBtn { background: #0a0a0a; border: 1px solid #1c1c1c; border-radius: 15px;
             color: #555; padding: 0 12px; font-size: 11px; }
#ShieldBtn:checked { color: #fff; border-color: #333; }
#WipeBtn { background: #0a0a0a; border: 1px solid #2a1013; border-radius: 15px;
           color: #a04048; padding: 0 12px; font-size: 11px; font-weight: bold; }
#WipeBtn:hover { color: #d71921; border-color: #d71921; }
#Progress { background: transparent; border: none; }
#Progress::chunk { background: #d71921; }
#PaneHeader { background: #0a0a0a; border-bottom: 1px solid #141414; }
#PaneHost { color: #555; font-size: 11px; }
#HomeDate { color: #8a8a8a; font-size: 13px; }
#HomeTag { color: #4a4a4a; font-size: 11px; }
#HomeStats { color: #666; font-size: 11px; }
#HomeHint { color: #3d3d3d; font-size: 11px; }
#QuickLink { background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 16px;
             color: #999; padding: 6px 16px; font-size: 12px; }
#QuickLink:hover { color: #fff; border-color: #333; }
#HistoryPanel { background: #0b0b0b; border-left: 1px solid #1f1f1f; }
#HistTitle { color: #fff; font-weight: bold; font-size: 13px; }
#HistHint { color: #4a4a4a; font-size: 10px; }
#HistFilter { background: #050505; border: 1px solid #1c1c1c; border-radius: 13px;
              padding: 0 12px; color: #ddd; selection-background-color: #d71921; }
#HistList { background: #0b0b0b; border: none; outline: none; }
#HistList::item { padding: 7px 8px; border-bottom: 1px solid #121212; color: #bbb; }
#HistList::item:hover { background: #111; color: #fff; }
#HistList::item:selected { background: #161616; color: #fff; }
#HistClear { background: transparent; border: 1px solid #2a1013; border-radius: 13px;
             color: #a04048; padding: 4px 12px; font-size: 11px; }
#HistClear:hover { color: #d71921; border-color: #d71921; }
#HistClose { background: transparent; border: none; color: #555; font-size: 14px; }
#HistClose:hover { color: #fff; }
#HistCount { color: #4a4a4a; font-size: 10px; }
QStatusBar { background: #000; border-top: 1px solid #141414; color: #666; }
QStatusBar QLabel { color: #666; font-size: 11px; }
QMessageBox { background: #0d0d0d; }
QMessageBox QLabel { color: #ddd; }
QMessageBox QPushButton { background: #161616; border: 1px solid #2a2a2a;
                          border-radius: 4px; padding: 6px 18px; color: #ddd; }
QMessageBox QPushButton:hover { border-color: #d71921; }
"""

# ─────────────────────────── хранилище ───────────────────────────

class Vault:
    """История (обфусцирована XOR+base64 — не криптография!) и конфиг."""
    KEY = hashlib.sha256(b"noir/vault/v1").digest()

    def __init__(self, directory: Path):
        self.dir = directory
        self.hist_path = directory / "history.bin"
        self.cfg_path = directory / "config.json"
        self.items = []
        self.cfg = {"engine": "google", "shield": True, "zoom": 1.0,
                    "wipe_storage": False}
        self._load()

    def _xor(self, b: bytes) -> bytes:
        return bytes(x ^ self.KEY[i % len(self.KEY)] for i, x in enumerate(b))

    def _load(self):
        try:
            self.cfg.update(json.loads(self.cfg_path.read_text()))
        except Exception:
            pass
        try:
            raw = base64.b64decode(self.hist_path.read_bytes())
            self.items = json.loads(self._xor(raw).decode())
        except Exception:
            self.items = []

    def add(self, q: str, mode: str):
        self.items.insert(0, {"t": int(time.time()), "q": q, "e": mode})
        del self.items[1000:]

    def save(self):
        try:
            blob = json.dumps(self.items, ensure_ascii=False).encode()
            self.hist_path.write_bytes(base64.b64encode(self._xor(blob)))
            os.chmod(self.hist_path, 0o600)
            self.cfg_path.write_text(json.dumps(self.cfg, ensure_ascii=False))
        except Exception:
            pass

    def clear(self):
        self.items = []
        try:
            self.hist_path.unlink(missing_ok=True)
        except Exception:
            pass

# ─────────────────────────── щит трекеров ───────────────────────────

class Shield(QWebEngineUrlRequestInterceptor):
    blocked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.enabled = True

    def interceptRequest(self, info):
        if not self.enabled:
            return
        host = info.requestUrl().host().lower()
        if not host:
            return
        parts = host.split(".")
        for i in range(len(parts) - 1):
            if ".".join(parts[i:]) in TRACKERS:
                info.block(True)
                self.blocked.emit(1)
                return

# ─────────────────────────── часы Nothing ───────────────────────────

GLYPHS = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ":": ["0", "0", "1", "0", "1", "0", "0"],
}

class DotClock(QWidget):
    """Дот-матричные часы HH:MM:SS в духе Nothing Ndot: белые точки,
    красное двоеточие, едва заметная «мёртвая» матрица на фоне."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(110)
        t = QTimer(self)
        t.timeout.connect(self.update)
        t.start(1000)

    def sizeHint(self):
        return QSize(560, 140)

    def paintEvent(self, _):
        now = time.localtime()
        text = time.strftime("%H:%M:%S", now)
        widths = [len(GLYPHS[c][0]) for c in text]
        gap = 2
        cols = sum(widths) + gap * (len(text) - 1)
        p = min(self.width() / (cols + 4), self.height() / 11.0)
        x = (self.width() - cols * p) / 2
        y = (self.height() - 7 * p) / 2

        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.setPen(Qt.PenStyle.NoPen)
        dead = QColor("#151515")
        live = QColor("#f2f2f2")
        red = QColor(ACCENT if now.tm_sec % 2 == 0 else "#4a0d10")

        for ch, w in zip(text, widths):
            rows = GLYPHS[ch]
            for r in range(7):
                for c in range(w):
                    on = rows[r][c] == "1"
                    if ch == ":":
                        color = red if on else dead
                    else:
                        color = live if on else dead
                    rad = p * (0.34 if on else 0.24)
                    qp.setBrush(color)
                    cx, cy = x + (c + 0.5) * p, y + (r + 0.5) * p
                    qp.drawEllipse(int(cx - rad), int(cy - rad),
                                   int(rad * 2), int(rad * 2))
            x += (w + gap) * p
        qp.end()

# ─────────────────────────── веб-страница ───────────────────────────

class BrowserPage(QWebEnginePage):
    def createWindow(self, _type):
        return self  # target=_blank открываем в этой же вкладке

    def acceptNavigationRequest(self, url, _nav, _main):
        return url.scheme() in ("http", "https", "about", "data", "blob",
                                "file", "chrome", "qrc")

def tune_page(page: QWebEnginePage):
    s = page.settings()
    A = QWebEngineSettings.WebAttribute
    s.setAttribute(A.JavascriptEnabled, True)
    s.setAttribute(A.LocalStorageEnabled, True)
    s.setAttribute(A.PluginsEnabled, False)
    s.setAttribute(A.FullScreenSupportEnabled, True)
    s.setAttribute(A.HyperlinkAuditingEnabled, False)   # приватность
    s.setAttribute(A.DnsPrefetchEnabled, False)         # приватность
    s.setAttribute(A.ScrollAnimatorEnabled, True)
    s.setAttribute(A.ScreenCaptureEnabled, False)
    s.setAttribute(A.AllowRunningInsecureContent, False)
    if hasattr(A, "ForceDarkMode"):                     # Qt >= 6.5
        s.setAttribute(A.ForceDarkMode, True)           # сайты — в чёрном
    page.setBackgroundColor(QColor("#000000"))

def make_script(name: str, src: str) -> QWebEngineScript:
    s = QWebEngineScript()
    s.setName(name)
    s.setSourceCode(src)
    s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    s.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    s.setRunsOnSubFrames(True)
    return s

class Pane(QWidget):
    """Панель: мини-заголовок (движок + хост) и веб-вью."""

    def __init__(self, engine: str, profile: QWebEngineProfile,
                 activate_cb, zoom: float):
        super().__init__()
        self.engine = engine
        self._progress = 100
        self.view = QWebEngineView(self)
        self.page = BrowserPage(profile, self.view)
        tune_page(self.page)
        self.view.setPage(self.page)
        self.view.setZoomFactor(zoom)
        self.page.scripts().insert(make_script("noir-style", STYLE_JS))

        self.dot = QLabel("●")
        self.name = QLabel(engine.upper())
        self.host = QLabel("")
        self.host.setObjectName("PaneHost")
        header = QWidget()
        header.setObjectName("PaneHeader")
        header.setFixedHeight(26)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(6)
        hl.addWidget(self.dot)
        hl.addWidget(self.name)
        hl.addStretch(1)
        hl.addWidget(self.host)
        header.mousePressEvent = lambda e: activate_cb(self)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(header)
        lay.addWidget(self.view, 1)

        self.page.urlChanged.connect(self._url)
        self.set_active(False)

    def _url(self, url: QUrl):
        h = url.host()
        self.host.setText(h[:42] + "…" if len(h) > 42 else h)

    def set_active(self, on: bool):
        self.dot.setStyleSheet(f"color:{ACCENT if on else '#3a3a3a'};")
        self.name.setStyleSheet(
            f"color:{'#eee' if on else '#666'}; font-size:11px; font-weight:bold;")

    def load(self, url: str):
        self.view.load(QUrl(url))

    def is_empty(self) -> bool:
        u = self.page.url()
        return u.isEmpty() or u.toString() == "about:blank"

# ─────────────────────────── анимированный сплит ───────────────────────────

class SplitContainer(QWidget):
    """Ручная геометрия + QVariantAnimation долей (f1, f2).
    Вторая панель создаётся лениво — экономия памяти."""

    def __init__(self, p1: Pane):
        super().__init__()
        self.p1, self.p2 = p1, None
        p1.setParent(self)
        p1.show()
        self.f1, self.f2 = 1.0, 0.0
        self.gap = 2
        self._anim = None

    def attach(self, p2: Pane):
        self.p2 = p2
        p2.setParent(self)
        p2.hide()

    def set_fractions(self, f1: float, f2: float, animate=True):
        if self._anim:
            self._anim.stop()
        if f1 > 0:
            self.p1.show()
        if f2 > 0 and self.p2:
            self.p2.show()
        if not animate:
            self._finish((f1, f2))
            return
        start = (self.f1, self.f2)
        anim = QVariantAnimation(self)
        anim.setDuration(340)
        anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutCubic))
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.valueChanged.connect(
            lambda t: self._apply((start[0] + (f1 - start[0]) * t,
                                   start[1] + (f2 - start[1]) * t)))
        anim.finished.connect(lambda: self._finish((f1, f2)))
        self._anim = anim
        anim.start()

    def _apply(self, fr):
        self.f1, self.f2 = fr
        self._layout()
        self.update()

    def _finish(self, target):
        self.f1, self.f2 = target
        self.p1.setVisible(target[0] > 0)
        if self.p2:
            self.p2.setVisible(target[1] > 0)
        self._layout()
        self.update()

    def _layout(self):
        w, h = self.width(), self.height()
        if self.p2 is None or self.f2 <= 0.001:
            self.p1.setGeometry(0, 0, w, h)
        elif self.f1 <= 0.001:
            self.p2.setGeometry(0, 0, w, h)
        else:
            w1 = int((w - self.gap) * self.f1)
            self.p1.setGeometry(0, 0, w1, h)
            self.p2.setGeometry(w1 + self.gap, 0, w - w1 - self.gap, h)

    def resizeEvent(self, _):
        self._layout()

    def paintEvent(self, _):
        qp = QPainter(self)
        qp.fillRect(self.rect(), QColor("#000"))
        if self.p2 and self.p1.isVisible() and self.p2.isVisible():
            qp.fillRect(self.p1.width(), 0, self.gap, self.height(),
                        QColor("#1f1f1f"))
        qp.end()

# ─────────────────────────── панель истории ───────────────────────────

class HistoryPanel(QWidget):
    rerun = pyqtSignal(str)
    cleared = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("HistoryPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(360)
        self._items = []

        title = QLabel("ИСТОРИЯ")
        title.setObjectName("HistTitle")
        hint = QLabel("Ё / ESC — СКРЫТЬ")
        hint.setObjectName("HistHint")
        close = QPushButton("✕")
        close.setObjectName("HistClose")
        close.setFixedSize(24, 24)
        close.clicked.connect(self.closed.emit)

        top = QHBoxLayout()
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(hint)
        top.addWidget(close)

        self.filter = QLineEdit()
        self.filter.setObjectName("HistFilter")
        self.filter.setPlaceholderText("фильтр…")
        self.filter.setFixedHeight(28)
        self.filter.textChanged.connect(self._rebuild)

        self.list = QListWidget()
        self.list.setObjectName("HistList")
        self.list.itemClicked.connect(
            lambda it: self.rerun.emit(it.data(Qt.ItemDataRole.UserRole)))

        self.count = QLabel("0 записей")
        self.count.setObjectName("HistCount")
        clear = QPushButton("ОЧИСТИТЬ")
        clear.setObjectName("HistClear")
        clear.clicked.connect(self.cleared.emit)
        bottom = QHBoxLayout()
        bottom.addWidget(self.count)
        bottom.addStretch(1)
        bottom.addWidget(clear)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)
        lay.addLayout(top)
        lay.addWidget(self.filter)
        lay.addWidget(self.list, 1)
        lay.addLayout(bottom)
        self.hide()

    def show_items(self, items):
        self._items = items
        self.filter.clear()
        self._rebuild()

    def _rebuild(self):
        f = self.filter.text().strip().lower()
        self.list.clear()
        n = 0
        for h in self._items:
            if f and f not in h["q"].lower():
                continue
            ts = time.strftime("%d.%m %H:%M", time.localtime(h["t"]))
            it = QListWidgetItem(f"{ts}  ·  {h['e']}  ·  {h['q']}")
            it.setData(Qt.ItemDataRole.UserRole, h["q"])
            self.list.addItem(it)
            n += 1
        self.count.setText(f"{n} записей")

# ─────────────────────────── главный экран ───────────────────────────

class Home(QWidget):
    def __init__(self, open_cb):
        super().__init__()
        self.clock = DotClock()
        self.date = QLabel("")
        self.date.setObjectName("HomeDate")
        f = QFont()
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        self.date.setFont(f)

        tag = QLabel("N O I R  //  ПРИВАТНОСТЬ ПО УМОЛЧАНИЮ")
        tag.setObjectName("HomeTag")
        self.stats = QLabel("")
        self.stats.setObjectName("HomeStats")

        links = QHBoxLayout()
        links.setSpacing(8)
        links.addStretch(1)
        for name, url in QUICK_LINKS:
            b = QPushButton("● " + name)
            b.setObjectName("QuickLink")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, u=url: open_cb(u))
            links.addWidget(b)
        links.addStretch(1)

        hint = QLabel("Ё — история   ·   CTRL+L — поиск   ·   "
                      "CTRL+SHIFT+C — сравнить   ·   F11 — фуллскрин")
        hint.setObjectName("HomeHint")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 20, 40, 24)
        lay.addStretch(2)
        lay.addWidget(self.clock, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(14)
        lay.addWidget(self.date, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(8)
        lay.addWidget(tag, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)
        lay.addLayout(links)
        lay.addSpacing(16)
        lay.addWidget(self.stats, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(2)
        lay.addWidget(hint, 0, Qt.AlignmentFlag.AlignHCenter)

        t = QTimer(self)
        t.timeout.connect(self._date)
        t.start(1000)
        self._date()

    def _date(self):
        n = time.localtime()
        self.date.setText(f"{WEEKDAYS[n.tm_wday]} · {n.tm_mday} "
                          f"{MONTHS[n.tm_mon - 1]} {n.tm_year}")

    def set_stats(self, blocked: int, queries: int):
        self.stats.setText(f"◉ заблокировано трекеров: {blocked}    ·    "
                           f"запросов за сессию: {queries}    ·    "
                           f"cookies: сохраняются")

# ─────────────────────────── главное окно ───────────────────────────

def looks_like_url(s: str) -> bool:
    if " " in s:
        return False
    if re.match(r"^https?://", s, re.I):
        return True
    return bool(re.match(r"^[\w-]+(\.[\w-]+)*\.[a-zA-Zа-яё]{2,}(:\d+)?(/\S*)?$",
                         s, re.I))

class Noir(QMainWindow):
    def __init__(self):
        super().__init__()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(DATA_DIR, 0o700)
        self.vault = Vault(DATA_DIR)

        # отложенная очистка DOM-хранилища после «СТЕРЕТЬ»
        if self.vault.cfg.get("wipe_storage"):
            shutil.rmtree(DATA_DIR / "storage", ignore_errors=True)
            self.vault.cfg["wipe_storage"] = False

        self.compare = False
        self.primary = self.vault.cfg.get("engine", "google")
        self.last_query = None
        self.blocked_count = 0
        self.session_queries = 0
        self.hist_open = False
        self._hist_anim = None
        self._fs = False

        self._init_profile()
        self._build_ui()
        self._shortcuts()
        QApplication.instance().installEventFilter(self)
        QApplication.instance().focusChanged.connect(self._focus_changed)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(800)
        self._save_timer.timeout.connect(self.vault.save)

        g = self.vault.cfg.get("geometry")
        if g and len(g) == 4:
            self.setGeometry(*g)
        else:
            self.resize(1280, 820)
        self.setMinimumSize(1060, 640)
        self.setWindowTitle("NOIR")
        self._make_icon()
        self.go_home()

    # ── профиль / куки ──
    def _init_profile(self):
        self.shield = Shield()
        self.shield.enabled = bool(self.vault.cfg.get("shield", True))
        self.shield.blocked.connect(self._on_blocked)

        self.profile = QWebEngineProfile("noir", self)
        self.profile.setPersistentStoragePath(str(DATA_DIR / "storage"))
        self.profile.setCachePath(str(DATA_DIR / "cache"))
        self.profile.setHttpCacheType(
            QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.profile.setHttpUserAgent(UA)
        self.profile.setHttpAcceptLanguage("ru-RU,ru;q=0.8,en-US;q=0.5")
        self.profile.setUrlRequestInterceptor(self.shield)
        self.profile.downloadRequested.connect(self._on_download)

    def _wire_page(self, pane: Pane):
        p = pane.page
        if self.shield.enabled:
            p.scripts().insert(make_script("noir-shield", SHIELD_JS))
        p.featurePermissionRequested.connect(
            lambda url, feat, pg=p: (
                pg.setFeaturePermission(
                    url, feat,
                    QWebEnginePage.PermissionPolicy.PermissionDeniedByUser),
                self.statusBar().showMessage(
                    "запрос доступа (гео/камера/и т.п.) отклонён", 3000)))
        p.fullScreenRequested.connect(self._on_fs)
        p.titleChanged.connect(lambda _t, pn=pane: self._update_title(pn))
        p.urlChanged.connect(lambda _u, pn=pane: self._update_status_url(pn))
        p.loadProgress.connect(lambda v, pn=pane: self._progress(v, pn))
        p.loadFinished.connect(lambda _ok, pn=pane: self._finished(pn))

    # ── UI ──
    def _build_ui(self):
        zoom = float(self.vault.cfg.get("zoom", 1.0))
        self.pane1 = Pane("google", self.profile, self.set_active, zoom)
        self._wire_page(self.pane1)
        self.pane2 = None
        self.active = self.pane1
        self.pane1.set_active(True)

        self.container = SplitContainer(self.pane1)
        self.home = Home(self.open_url)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.container)

        # тулбар
        brand = QLabel(f'NOIR<span style="color:{ACCENT}">●</span>')
        brand.setObjectName("Brand")

        def nav(txt, tip, fn):
            b = QPushButton(txt)
            b.setObjectName("NavBtn")
            b.setFixedSize(30, 30)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            return b

        self.btn_home = nav("⌂", "Домой (Alt+Home)", self.go_home)
        self.btn_back = nav("‹", "Назад (Alt+←)", lambda: self.active.page.triggerAction(QWebEnginePage.WebAction.Back))
        self.btn_fwd  = nav("›", "Вперёд (Alt+→)", lambda: self.active.page.triggerAction(QWebEnginePage.WebAction.Forward))
        self.btn_rel  = nav("↻", "Обновить (Ctrl+R)", lambda: self.active.page.triggerAction(QWebEnginePage.WebAction.Reload))

        self.chip_g = QPushButton("GOOGLE")
        self.chip_y = QPushButton("ЯНДЕКС")
        for c in (self.chip_g, self.chip_y):
            c.setObjectName("EngineChip")
            c.setCheckable(True)
            c.setFixedHeight(26)
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        grp.addButton(self.chip_g)
        grp.addButton(self.chip_y)
        self.chip_g.clicked.connect(lambda: self.set_primary("google"))
        self.chip_y.clicked.connect(lambda: self.set_primary("yandex"))

        self.search = QLineEdit()
        self.search.setObjectName("SearchEdit")
        self.search.setFixedHeight(34)
        self.search.setPlaceholderText("запрос или адрес…   (Ё — история)")
        self.search.returnPressed.connect(self.do_search)

        self.compare_btn = QPushButton("○ СРАВНИТЬ")
        self.compare_btn.setObjectName("CompareBtn")
        self.compare_btn.setCheckable(True)
        self.compare_btn.setFixedHeight(34)
        self.compare_btn.setToolTip("Google и Яндекс рядом (Ctrl+Shift+C)")
        self.compare_btn.clicked.connect(self.set_compare)

        self.shield_btn = QPushButton()
        self.shield_btn.setObjectName("ShieldBtn")
        self.shield_btn.setCheckable(True)
        self.shield_btn.setFixedHeight(30)
        self.shield_btn.setToolTip("Щит: трекеры + WebRTC + fingerprint")
        self.shield_btn.clicked.connect(self._toggle_shield)
        self._sync_shield_btn()

        self.wipe_btn = QPushButton("СТЕРЕТЬ")
        self.wipe_btn.setObjectName("WipeBtn")
        self.wipe_btn.setFixedHeight(30)
        self.wipe_btn.setToolTip("Стереть куки, кэш, историю (Ctrl+Shift+X)")
        self.wipe_btn.clicked.connect(self.panic)

        tb = QWidget()
        tb.setObjectName("Toolbar")
        tb.setFixedHeight(52)
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(10, 0, 10, 0)
        tl.setSpacing(6)
        for w in (brand, self.btn_home, self.btn_back, self.btn_fwd,
                  self.btn_rel, self.chip_g, self.chip_y):
            tl.addWidget(w)
        tl.addWidget(self.search, 1)
        tl.addWidget(self.compare_btn)
        tl.addWidget(self.shield_btn)
        tl.addWidget(self.wipe_btn)

        self.bar = QProgressBar()
        self.bar.setObjectName("Progress")
        self.bar.setFixedHeight(2)
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        self.bar.hide()

        central = QWidget()
        cl = QVBoxLayout(central)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(tb)
        cl.addWidget(self.bar)
        cl.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.hist = HistoryPanel()
        self.hist.setParent(central)
        self.hist.rerun.connect(self._rerun)
        self.hist.cleared.connect(self._clear_history)
        self.hist.closed.connect(self._close_history)

        self.stat_shield = QLabel("◉ 0")
        self.stat_shield.setToolTip("заблокировано трекеров за сессию")
        self.stat_mode = QLabel("")
        self.stat_cookies = QLabel("cookies: on")
        sb = self.statusBar()
        sb.setSizeGripEnabled(False)
        sb.addPermanentWidget(self.stat_mode)
        sb.addPermanentWidget(self.stat_shield)
        sb.addPermanentWidget(self.stat_cookies)

        self._sync_chips()
        self._sync_mode()

    def _make_icon(self):
        pm = QPixmap(32, 32)
        pm.fill(QColor("#000"))
        qp = QPainter(pm)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(ACCENT))
        qp.drawEllipse(10, 10, 12, 12)
        qp.end()
        self.setWindowIcon(QIcon(pm))

    def _shortcuts(self):
        def sc(seq, fn):
            QShortcut(QKeySequence(seq), self, activated=fn)
        sc("Ctrl+L", self._focus_search)
        sc("Ctrl+K", self._focus_search)
        sc("Ctrl+Shift+C", lambda: self.set_compare(not self.compare))
        sc("Ctrl+R", lambda: self.active.page.triggerAction(QWebEnginePage.WebAction.Reload))
        sc("F5", lambda: self.active.page.triggerAction(QWebEnginePage.WebAction.Reload))
        sc("Alt+Left", lambda: self.active.page.triggerAction(QWebEnginePage.WebAction.Back))
        sc("Alt+Right", lambda: self.active.page.triggerAction(QWebEnginePage.WebAction.Forward))
        sc("Alt+Home", self.go_home)
        sc("F11", self._toggle_fs)
        sc("Ctrl+Shift+X", self.panic)
        sc("Ctrl+Q", self.close)
        sc("Ctrl+=", lambda: self._zoom(0.1))
        sc("Ctrl++", lambda: self._zoom(0.1))
        sc("Ctrl+-", lambda: self._zoom(-0.1))
        sc("Ctrl+0", lambda: self._zoom(0, reset=True))
        sc("Esc", self._esc)

    # ── фокус / активная панель ──
    def _pane_of(self, w):
        while w is not None:
            if w is self.pane1:
                return self.pane1
            if self.pane2 is not None and w is self.pane2:
                return self.pane2
            w = w.parentWidget()
        return None

    def _focus_changed(self, _old, new):
        pane = self._pane_of(new)
        if pane:
            self.set_active(pane)

    def set_active(self, pane: Pane):
        if pane is self.active:
            return
        self.active = pane
        self.pane1.set_active(pane is self.pane1)
        if self.pane2:
            self.pane2.set_active(pane is self.pane2)
        self._update_status_url(pane)
        self._update_title(pane)
        self._progress(pane._progress, pane)

    # ── клавиша Ё: глобальный перехват ──
    def eventFilter(self, obj, ev):
        if (ev.type() == QEvent.Type.KeyPress and not ev.isAutoRepeat()
                and ev.text() in ("ё", "Ё", "`", "~")
                and not (ev.modifiers() & (Qt.KeyboardModifier.ControlModifier
                                           | Qt.KeyboardModifier.AltModifier
                                           | Qt.KeyboardModifier.MetaModifier))):
            fw = QApplication.focusWidget()
            if isinstance(fw, QLineEdit):
                return False                      # печатаем в поле — не мешаем
            pane = self._pane_of(fw)
            if pane is not None:
                # на сайте: если курсор в поле ввода — печатаем, иначе — история
                pane.page.runJavaScript(
                    EDITABLE_JS,
                    lambda ed: None if ed else self.toggle_history())
                return False
            self.toggle_history()
            return True
        return super().eventFilter(obj, ev)

    # ── движки / раскладка ──
    def pane_for(self, engine: str) -> Pane:
        if engine == "yandex":
            self._ensure_pane2()
            return self.pane2
        return self.pane1

    def _ensure_pane2(self):
        if self.pane2 is None:                     # ленивая инициализация
            self.pane2 = Pane("yandex", self.profile, self.set_active,
                              float(self.vault.cfg.get("zoom", 1.0)))
            self._wire_page(self.pane2)
            self.container.attach(self.pane2)

    def _ensure_loaded(self, pane: Pane, search=False):
        if pane.is_empty():
            if search and self.last_query:
                pane.load(SEARCH[pane.engine].format(quote_plus(self.last_query)))
            else:
                pane.load(HOMES[pane.engine])

    def apply_layout(self, animate=True):
        if self.compare:
            self._ensure_pane2()
            target = (0.5, 0.5)
        elif self.primary == "google":
            target = (1.0, 0.0)
        else:
            self._ensure_pane2()
            target = (0.0, 1.0)
        self.container.set_fractions(*target, animate=animate)
        self._sync_mode()

    def set_compare(self, on: bool, animate=True):
        self.compare = bool(on)
        self.compare_btn.blockSignals(True)
        self.compare_btn.setChecked(self.compare)
        self.compare_btn.blockSignals(False)
        self.compare_btn.setText("● СРАВНИТЬ" if self.compare else "○ СРАВНИТЬ")
        self.chip_g.setDisabled(self.compare)
        self.chip_y.setDisabled(self.compare)
        if self.compare:
            self._ensure_pane2()
            self._ensure_loaded(self.pane2, search=True)
            self.set_active(self.pane_for(self.primary))
        else:
            # выходим из сравнения в тот движок, где был фокус
            self.primary = self.active.engine
            self._sync_chips()
        self.apply_layout(animate)

    def set_primary(self, engine: str):
        if self.compare or engine == self.primary:
            return
        self.primary = engine
        pane = self.pane_for(engine)
        self._ensure_loaded(pane)
        self.set_active(pane)
        self.apply_layout()
        self._sync_chips()

    def _sync_chips(self):
        self.chip_g.setChecked(self.primary == "google")
        self.chip_y.setChecked(self.primary == "yandex")

    def _sync_mode(self):
        self.stat_mode.setText(
            "G+Я" if self.compare else BADGE[self.primary])

    # ── поиск / навигация ──
    def do_search(self):
        q = self.search.text().strip()
        if not q:
            return
        if looks_like_url(q):
            self.open_url(q if re.match(r"^https?://", q, re.I)
                          else "https://" + q)
            return
        self.last_query = q
        mode = "G+Я" if self.compare else BADGE[self.primary]
        self.vault.add(q, mode)
        self.session_queries += 1
        self._save_timer.start()
        if self.compare:
            self._ensure_pane2()
            self.pane1.load(SEARCH["google"].format(quote_plus(q)))
            self.pane2.load(SEARCH["yandex"].format(quote_plus(q)))
        else:
            self.pane_for(self.primary).load(
                SEARCH[self.primary].format(quote_plus(q)))
        self.stack.setCurrentWidget(self.container)
        self.apply_layout()
        self.home.set_stats(self.blocked_count, self.session_queries)
        self.active.view.setFocus()

    def open_url(self, url: str):
        self.active.load(url)
        self.stack.setCurrentWidget(self.container)
        self.apply_layout()
        self.active.view.setFocus()

    def go_home(self):
        self.home.set_stats(self.blocked_count, self.session_queries)
        self.stack.setCurrentWidget(self.home)
        self.bar.hide()
        self.statusBar().showMessage("NOIR // главный экран", 2000)
        self.search.setFocus()

    def _focus_search(self):
        self.search.setFocus()
        self.search.selectAll()

    def _rerun(self, q: str):
        self.search.setText(q)
        self._close_history()
        self.do_search()

    # ── история ──
    def toggle_history(self):
        self._close_history() if self.hist_open else self._open_history()

    def _open_history(self):
        self.hist_open = True
        self.hist.show_items(self.vault.items)
        self.hist.show()
        self.hist.raise_()
        self._slide_history(True)
        self.hist.list.setFocus()

    def _close_history(self):
        if not self.hist_open:
            return
        self.hist_open = False
        self._slide_history(False)

    def _slide_history(self, opening: bool):
        if self._hist_anim:
            self._hist_anim.stop()
        c = self.centralWidget()
        w, h = c.width(), c.height()
        x0 = self.hist.x() if self.hist.isVisible() else w
        x1 = w - 360 if opening else w
        self.hist.setGeometry(x0, 0, 360, h)
        anim = QVariantAnimation(self)
        anim.setDuration(260)
        anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutCubic))
        anim.setStartValue(x0)
        anim.setEndValue(x1)
        anim.valueChanged.connect(
            lambda x: self.hist.setGeometry(int(x), 0, 360,
                                            self.centralWidget().height()))
        if not opening:
            anim.finished.connect(self.hist.hide)
        self._hist_anim = anim
        anim.start()

    def _place_history(self):
        c = self.centralWidget()
        x = c.width() - 360 if self.hist_open else c.width()
        self.hist.setGeometry(x, 0, 360, c.height())
        if self.hist_open:
            self.hist.raise_()

    def _clear_history(self):
        self.vault.clear()
        self.vault.save()
        self.hist.show_items([])
        self.statusBar().showMessage("история очищена", 3000)

    # ── щит / паника ──
    def _sync_shield_btn(self):
        on = self.shield.enabled
        self.shield_btn.setChecked(on)
        self.shield_btn.setText("● ЩИТ" if on else "○ ЩИТ")

    def _toggle_shield(self):
        self.shield.enabled = self.shield_btn.isChecked()
        self.vault.cfg["shield"] = self.shield.enabled
        self._sync_shield_btn()
        for pane in (self.pane1, self.pane2):
            if pane is None:
                continue
            col = pane.page.scripts()
            for s in col.find("noir-shield"):
                col.remove(s)
            if self.shield.enabled:
                col.insert(make_script("noir-shield", SHIELD_JS))
            if not pane.is_empty():
                pane.page.triggerAction(QWebEnginePage.WebAction.Reload)
        self.statusBar().showMessage(
            "ЩИТ " + ("ВКЛ — страницы перезагружены" if self.shield.enabled
                      else "ВЫКЛ"), 3000)
        self._save_timer.start()

    def _on_blocked(self, n: int):
        self.blocked_count += n
        self.stat_shield.setText(f"◉ {self.blocked_count}")

    def panic(self):
        r = QMessageBox.question(
            self, "СТЕРЕТЬ",
            "Удалить куки, кэш и историю поиска?\n"
            "DOM-хранилища сайтов будут очищены при следующем запуске.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r != QMessageBox.StandardButton.Yes:
            return
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.profile.clearAllVisitedLinks()
        self.vault.clear()
        self.vault.cfg["wipe_storage"] = True
        self.vault.save()
        self.blocked_count = 0
        self.session_queries = 0
        self.stat_shield.setText("◉ 0")
        self.last_query = None
        self.search.clear()
        self.pane1.load("about:blank")
        if self.pane2:
            self.pane2.load("about:blank")
        self.set_compare(False, animate=False)
        self._close_history()
        self.go_home()
        self.statusBar().showMessage("следы стёрты", 4000)

    # ── загрузки / fullscreen / прогресс ──
    def _on_download(self, item: QWebEngineDownloadItem):
        dl = Path.home() / "Downloads"
        dl.mkdir(exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", str(dl / item.downloadFileName()))
        if not path:
            item.cancel()
            return
        item.setDownloadDirectory(str(Path(path).parent))
        item.setDownloadFileName(Path(path).name)
        item.stateChanged.connect(lambda st: self._dl_state(st, path))
        item.accept()
        self.statusBar().showMessage("загрузка начата…", 3000)

    def _dl_state(self, st, path):
        S = QWebEngineDownloadItem.DownloadState
        if st == S.DownloadCompleted:
            self.statusBar().showMessage(f"сохранено: {path}", 5000)
        elif st in (S.DownloadInterrupted, S.DownloadCancelled):
            self.statusBar().showMessage("загрузка прервана", 4000)

    def _on_fs(self, req):
        req.accept()
        self._fs = req.toggleOn()
        self.showFullScreen() if self._fs else self.showNormal()

    def _toggle_fs(self):
        self._fs = not self._fs
        self.showFullScreen() if self._fs else self.showNormal()

    def _esc(self):
        if self.hist_open:
            self._close_history()
        elif self._fs:
            self._toggle_fs()

    def _progress(self, v: int, pane: Pane):
        pane._progress = v
        if pane is self.active:
            self.bar.setVisible(v < 100)
            self.bar.setValue(v)

    def _finished(self, pane: Pane):
        pane._progress = 100
        if pane is self.active:
            self.bar.hide()

    def _update_title(self, pane: Pane):
        if pane is self.active:
            t = pane.page.title()
            self.setWindowTitle(f"NOIR — {t}" if t else "NOIR")

    def _update_status_url(self, pane: Pane):
        if pane is self.active:
            u = pane.page.url().toString()
            if u and u != "about:blank":
                self.statusBar().showMessage(u)

    def _zoom(self, delta: float, reset=False):
        z = 1.0 if reset else min(3.0, max(0.3,
                                self.active.view.zoomFactor() + delta))
        self.active.view.setZoomFactor(z)
        self.vault.cfg["zoom"] = z
        self.statusBar().showMessage(f"масштаб: {int(z * 100)}%", 1500)

    # ── геометрия / выход ──
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._place_history()

    def closeEvent(self, ev):
        g = self.geometry()
        self.vault.cfg.update({"engine": self.primary,
                               "geometry": [g.x(), g.y(), g.width(), g.height()]})
        self.vault.save()
        ev.accept()

# ─────────────────────────── запуск ───────────────────────────

def main():
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    flags += " --no-default-browser-check --no-first-run --disable-logging --log-level=3"
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        flags += " --no-sandbox"
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = flags.strip()

    app = QApplication(sys.argv)
    app.setApplicationName("NOIR")
    app.setStyle("Fusion")
    f = QFont()
    f.setFamilies(["JetBrains Mono", "IBM Plex Mono", "DejaVu Sans Mono", "monospace"])
    f.setPointSize(10)
    app.setFont(f)

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#0d0d0d"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#e8e8e8"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#0a0a0a"))
    pal.setColor(QPalette.ColorRole.Text, QColor("#e8e8e8"))
    pal.setColor(QPalette.ColorRole.Button, QColor("#161616"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#ddd"))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#fff"))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor("#555"))
    app.setPalette(pal)
    app.setStyleSheet(QSS)

    w = Noir()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()