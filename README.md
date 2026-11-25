# NOIR

[Русский](#русский-ru) · [English](#english-en)

---

## Русский (RU)

### Установка (Linux (Debian))

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip binutils
sudo apt install -y python3-pyqt6.qtwebengine
mkdir -p ~/noir && cd ~/noir
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -U PyQt6 PyQt6-WebEngine pyinstaller
python noir.py
```

### СБОРКА

```bash
cd ~/noir
source .venv/bin/activate
pyinstaller --noconfirm --clean --windowed --name noir \
  --collect-all PyQt6.QtWebEngineCore \
  --collect-all PyQt6.QtWebEngineWidgets \
  noir.py
./dist/noir/noir
```

Получишь папку `dist/noir/` с бинарником `noir` внутри. Это нормально, что она весит ~300–450 МБ — внутри Chromium.

### иф нужен один вайл

```bash
pyinstaller --noconfirm --clean --windowed --onefile --name noir \
  --collect-all PyQt6.QtWebEngineCore \
  --collect-all PyQt6.QtWebEngineWidgets \
  noir.py
./dist/noir
```

### Управление

- Ё / \` / ~ — история (скрыта при каждом запуске; не срабатывает, когда печатаешь в поле ввода)
- Enter — поиск: в один движок или в оба, если СРАВНИТЬ включён
- Ctrl+Shift+C — тумблер СРАВНИТЬ
- Ctrl+L / Ctrl+K — фокус в строку поиска
- Alt+← / → / Home — назад / вперёд / домой
- Ctrl+R / F5, Ctrl+± / 0 — обновить, зум
- F11, Esc — фуллскрин / закрыть историю
- Ctrl+Shift+X — СТЕРЕТЬ всё

### АЛЬТЕРНАТИВА ЕСЛИ ВЫДАЕТ ОШИБКУ ПО v

```bash
sudo apt install -y libnss3 libnspr4 libxkbcommon0 libxcomposite1 libxdamage1 \
  libxrandr2 libxfixes3 libxext6 libx11-xcb1 libgbm1 libdrm2 libasound2 \
  libdbus-1-3 libexpat1 libfontconfig1 libfreetype6 libglib2.0-0 \
  libcups2 libatk1.0-0 libatk-bridge2.0-0 libxslt1.1 libegl1 libgl1
```

### ОШИБКИ

Ошибка `Could not find QtWebEngineProcess`:

```bash
QTWEBENGINEPROCESS_PATH="$HOME/noir/dist/noir/_internal/PyQt6/Qt6/libexec/QtWebEngineProcess" ./dist/noir/noir
```

#### чЕРНЫЙ экран \ артефакты

```bash
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu" ./dist/noir/noir
```

---

## English (EN)

### Installation (Linux (Debian))

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip binutils
sudo apt install -y python3-pyqt6.qtwebengine
mkdir -p ~/noir && cd ~/noir
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -U PyQt6 PyQt6-WebEngine pyinstaller
python noir.py
```

### BUILD

```bash
cd ~/noir
source .venv/bin/activate
pyinstaller --noconfirm --clean --windowed --name noir \
  --collect-all PyQt6.QtWebEngineCore \
  --collect-all PyQt6.QtWebEngineWidgets \
  noir.py
./dist/noir/noir
```

You'll get a `dist/noir/` folder with the `noir` binary inside. ~300–450 MB is totally normal — there's a whole Chromium in there.

### if u need just one file (onefile, yeah)

```bash
pyinstaller --noconfirm --clean --windowed --onefile --name noir \
  --collect-all PyQt6.QtWebEngineCore \
  --collect-all PyQt6.QtWebEngineWidgets \
  noir.py
./dist/noir
```

### Controls

The app UI is in Russian — button names below are shown as they actually appear.

- Ё / \` / ~ — history (hidden on every launch; won't fire while you're typing into an input field)
- Enter — search: one engine, or both if СРАВНИТЬ (COMPARE) is on
- Ctrl+Shift+C — СРАВНИТЬ (COMPARE) toggle
- Ctrl+L / Ctrl+K — focus the search bar
- Alt+← / → / Home — back / forward / home
- Ctrl+R / F5, Ctrl+± / 0 — reload, zoom
- F11, Esc — fullscreen / close history
- Ctrl+Shift+X — СТЕРЕТЬ (WIPE) everything

### PLAN B IF IT STARTS YELLING ERRORS AT U

```bash
sudo apt install -y libnss3 libnspr4 libxkbcommon0 libxcomposite1 libxdamage1 \
  libxrandr2 libxfixes3 libxext6 libx11-xcb1 libgbm1 libdrm2 libasound2 \
  libdbus-1-3 libexpat1 libfontconfig1 libfreetype6 libglib2.0-0 \
  libcups2 libatk1.0-0 libatk-bridge2.0-0 libxslt1.1 libegl1 libgl1
```

### ERRORS

`Could not find QtWebEngineProcess` error:

```bash
QTWEBENGINEPROCESS_PATH="$HOME/noir/dist/noir/_internal/PyQt6/Qt6/libexec/QtWebEngineProcess" ./dist/noir/noir
```

#### bLACK screen \ artifacts

```bash
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu" ./dist/noir/noir
```

Unfortunately, this code was written by an AI, so it might contain bugs. \ эт крч квен писал а не клод поэтому хз
