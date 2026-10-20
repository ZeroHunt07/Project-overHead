import sys, os, math, time, platform, json, atexit, subprocess, ctypes
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

if (
    sys.platform.startswith("linux")
    and os.environ.get("WAYLAND_DISPLAY")
    and os.environ.get("DISPLAY")
):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import QApplication, QInputDialog, QMenu, QWidget
from PyQt6.QtCore import (
    Qt, QTimer, QRectF, QUrl, QUrlQuery, QObject, QRunnable, QThreadPool,
    pyqtSignal, pyqtSlot,
)
from PyQt6.QtGui import (
    QPainter, QColor, QCursor, QFont, QPainterPath, QPen, QFontDatabase,
    QLinearGradient, QBrush,
)
from PyQt6.QtDBus import (
    QDBusConnection, QDBusInterface, QDBusObjectPath, QDBusVariant,
)

# --- Configuration Persistence ---
CONFIG_DIR = os.path.expanduser("~/.config/project-overhead")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"theme": "liquid_glass", "size_scale": 1.0}


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


# --- Clean Sans-Serif Typography ---
def get_font_family():
    try:
        fams = QFontDatabase.families()
        for f in ["Adwaita Sans", "Ubuntu", "DejaVu Sans"]:
            if f in fams:
                return f
    except Exception:
        pass
    return "sans-serif"


FONT_FAMILY = "sans-serif"

# --- Theme Presets ---
THEMES = {
    "liquid_glass": {
        "name": "Liquid Glass (Obsidian)",
        "bg_top": QColor(28, 30, 42, 225),
        "bg_mid": QColor(14, 15, 22, 240),
        "bg_bot": QColor(6, 6, 10, 252),
        "rim_top": QColor(255, 255, 255, 80),
        "rim_bot": QColor(255, 255, 255, 18),
        "sheen": True,
        "accent": QColor(48, 209, 88),         # Apple Green
        "accent_alt": QColor(94, 156, 255),    # Electric Blue
        "badge_bg": QColor(40, 42, 56, 210),
        "btn_bg": QColor(42, 44, 58, 210),
        "btn_border": QColor(255, 255, 255, 35),
    },
    "pitch_black": {
        "name": "Pitch Black (OLED)",
        "bg_top": QColor(0, 0, 0, 255),
        "bg_mid": QColor(0, 0, 0, 255),
        "bg_bot": QColor(0, 0, 0, 255),
        "rim_top": QColor(255, 255, 255, 35),
        "rim_bot": QColor(255, 255, 255, 10),
        "sheen": False,
        "accent": QColor(48, 209, 88),
        "accent_alt": QColor(94, 156, 255),
        "badge_bg": QColor(28, 28, 30),
        "btn_bg": QColor(36, 36, 38),
        "btn_border": QColor(56, 56, 58),
    },
    "cyber_neon": {
        "name": "Cyber Neon",
        "bg_top": QColor(12, 18, 38, 230),
        "bg_mid": QColor(8, 12, 26, 245),
        "bg_bot": QColor(4, 6, 15, 255),
        "rim_top": QColor(0, 240, 255, 100),
        "rim_bot": QColor(255, 46, 147, 45),
        "sheen": True,
        "accent": QColor(0, 240, 255),         # Cyan
        "accent_alt": QColor(255, 46, 147),    # Neon Magenta
        "badge_bg": QColor(18, 28, 52, 220),
        "btn_bg": QColor(22, 34, 62, 220),
        "btn_border": QColor(0, 240, 255, 65),
    },
    "aurora_emerald": {
        "name": "Aurora Emerald",
        "bg_top": QColor(10, 30, 22, 230),
        "bg_mid": QColor(6, 18, 14, 245),
        "bg_bot": QColor(3, 10, 8, 255),
        "rim_top": QColor(52, 211, 153, 95),
        "rim_bot": QColor(16, 185, 129, 35),
        "sheen": True,
        "accent": QColor(52, 211, 153),        # Mint
        "accent_alt": QColor(56, 189, 248),    # Sky Blue
        "badge_bg": QColor(14, 42, 30, 220),
        "btn_bg": QColor(18, 48, 36, 220),
        "btn_border": QColor(52, 211, 153, 65),
    },
    "amethyst_purple": {
        "name": "Amethyst Purple",
        "bg_top": QColor(26, 14, 40, 230),
        "bg_mid": QColor(16, 9, 26, 245),
        "bg_bot": QColor(8, 4, 15, 255),
        "rim_top": QColor(192, 132, 252, 95),
        "rim_bot": QColor(168, 85, 247, 35),
        "sheen": True,
        "accent": QColor(192, 132, 252),       # Lavender
        "accent_alt": QColor(244, 114, 182),   # Pink
        "badge_bg": QColor(38, 22, 58, 220),
        "btn_bg": QColor(46, 26, 70, 220),
        "btn_border": QColor(192, 132, 252, 65),
    },
    "sunset_amber": {
        "name": "Sunset Amber",
        "bg_top": QColor(32, 20, 14, 230),
        "bg_mid": QColor(20, 12, 8, 245),
        "bg_bot": QColor(10, 6, 4, 255),
        "rim_top": QColor(251, 191, 36, 95),
        "rim_bot": QColor(245, 158, 11, 35),
        "sheen": True,
        "accent": QColor(251, 191, 36),        # Amber Gold
        "accent_alt": QColor(251, 113, 133),   # Coral
        "badge_bg": QColor(48, 30, 20, 220),
        "btn_bg": QColor(56, 36, 24, 220),
        "btn_border": QColor(251, 191, 36, 65),
    },
}

WEATHER_LOCATION = "Yamunanagar"
MPRIS_PATH = "/org/mpris/MediaPlayer2"
MPRIS_PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
DBUS_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
_WEATHER_FETCHES = set()


def _wait_for_weather_fetches():
    if _WEATHER_FETCHES:
        QThreadPool.globalInstance().waitForDone(15000)


atexit.register(_wait_for_weather_fetches)


class WeatherFetchSignals(QObject):
    finished = pyqtSignal(object, str, object, str)


class WeatherFetch(QRunnable):
    def __init__(self, url, stage):
        super().__init__()
        self.url = url
        self.stage = stage
        self.signals = WeatherFetchSignals()

    @pyqtSlot()
    def run(self):
        request = Request(self.url, headers={"User-Agent": "ProjectOverhead/1.0"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read()
        except (URLError, TimeoutError, OSError) as error:
            self.signals.finished.emit(self, self.stage, b"", str(error))
            return
        self.signals.finished.emit(self, self.stage, payload, "")


class Spring:
    """Near-critically damped spring for organic motion without size overshoot."""
    def __init__(self, stiffness=190.0, damping=28.0, mass=1.0):
        self.value = self.target = self.velocity = 0.0
        self.k, self.c, self.m = stiffness, damping, mass

    def step(self, dt=1 / 60):
        force = -self.k * (self.value - self.target) - self.c * self.velocity
        self.velocity += (force / self.m) * dt
        self.value += self.velocity * dt
        if abs(self.value - self.target) < 0.05 and abs(self.velocity) < 0.05:
            self.value, self.velocity = self.target, 0.0
        return self.value


class _XClientMessageEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("message_type", ctypes.c_ulong),
        ("format", ctypes.c_int),
        ("data_l", ctypes.c_long * 5),
    ]


def make_window_persistent_all_desktops(window_title="Dynamic Island"):
    """Configures the window as an un-minimizable dock visible across all virtual desktops."""
    try:
        x11 = ctypes.CDLL("libX11.so.6")
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XDefaultRootWindow.restype = ctypes.c_ulong
        x11.XInternAtom.restype = ctypes.c_ulong
        x11.XSendEvent.restype = ctypes.c_int
        x11.XQueryTree.restype = ctypes.c_int
        x11.XFetchName.restype = ctypes.c_int

        display = x11.XOpenDisplay(None)
        if not display:
            return False
        root = x11.XDefaultRootWindow(display)

        root_ret = ctypes.c_ulong()
        parent_ret = ctypes.c_ulong()
        children_ptr = ctypes.POINTER(ctypes.c_ulong)()
        nchildren = ctypes.c_uint()

        target_wid = None
        if x11.XQueryTree(
            display, root, ctypes.byref(root_ret), ctypes.byref(parent_ret),
            ctypes.byref(children_ptr), ctypes.byref(nchildren)
        ):
            for i in range(nchildren.value):
                wid = children_ptr[i]
                name_ptr = ctypes.c_char_p()
                if x11.XFetchName(display, wid, ctypes.byref(name_ptr)) and name_ptr.value:
                    if window_title.encode() in name_ptr.value:
                        target_wid = wid
                        break

        if not target_wid:
            x11.XCloseDisplay(display)
            return False

        net_wm_state = x11.XInternAtom(display, b"_NET_WM_STATE", False)
        net_wm_state_sticky = x11.XInternAtom(display, b"_NET_WM_STATE_STICKY", False)
        net_wm_state_above = x11.XInternAtom(display, b"_NET_WM_STATE_ABOVE", False)
        net_wm_state_skip_taskbar = x11.XInternAtom(display, b"_NET_WM_STATE_SKIP_TASKBAR", False)
        net_wm_state_skip_pager = x11.XInternAtom(display, b"_NET_WM_STATE_SKIP_PAGER", False)
        net_wm_desktop = x11.XInternAtom(display, b"_NET_WM_DESKTOP", False)
        net_wm_window_type = x11.XInternAtom(display, b"_NET_WM_WINDOW_TYPE", False)
        net_wm_window_type_dock = x11.XInternAtom(display, b"_NET_WM_WINDOW_TYPE_DOCK", False)
        atom_type = x11.XInternAtom(display, b"ATOM", False)
        card_type = x11.XInternAtom(display, b"CARDINAL", False)

        # 1. Dock window type: never minimized by window manager or Show Desktop
        dock_atom = ctypes.c_ulong(net_wm_window_type_dock)
        x11.XChangeProperty(display, target_wid, net_wm_window_type, atom_type, 32, 0, ctypes.byref(dock_atom), 1)

        # 2. Sticky + Always on Top + Skip taskbar & pager
        sticky_atoms = (ctypes.c_ulong * 4)(
            net_wm_state_sticky, net_wm_state_above, net_wm_state_skip_taskbar, net_wm_state_skip_pager
        )
        x11.XChangeProperty(display, target_wid, net_wm_state, atom_type, 32, 0, ctypes.byref(sticky_atoms), 4)

        # 3. All virtual desktops / workspaces (-1 / 0xFFFFFFFF)
        all_desk = ctypes.c_ulong(0xFFFFFFFF)
        x11.XChangeProperty(display, target_wid, net_wm_desktop, card_type, 32, 0, ctypes.byref(all_desk), 1)

        # 4. ClientMessages to root window for instant WM notification
        mask = 0x00100000 | 0x00080000
        ev_state = _XClientMessageEvent()
        ev_state.type = 33
        ev_state.window = target_wid
        ev_state.message_type = net_wm_state
        ev_state.format = 32
        ev_state.data_l[0] = 1  # _NET_WM_STATE_ADD
        ev_state.data_l[1] = net_wm_state_sticky
        ev_state.data_l[2] = net_wm_state_above
        ev_state.data_l[3] = 1
        x11.XSendEvent(display, root, False, mask, ctypes.byref(ev_state))

        ev_desk = _XClientMessageEvent()
        ev_desk.type = 33
        ev_desk.window = target_wid
        ev_desk.message_type = net_wm_desktop
        ev_desk.format = 32
        ev_desk.data_l[0] = -1
        ev_desk.data_l[1] = 1
        x11.XSendEvent(display, root, False, mask, ctypes.byref(ev_desk))

        x11.XFlush(display)
        x11.XCloseDisplay(display)
        return True
    except Exception:
        return False


class DynamicIsland(QWidget):
    # All diagram states:
    COMPACT = 0       # Stage 1 for all: Minimal pill with status dot
    MUSIC_S2 = 1      # Diagram 1: Music Stage 2 (00:00 + Equalizer)
    MUSIC_S3 = 2      # Diagram 1: Music Stage 3 (Expanded Player + Scrubber)
    CHARGING = 3      # Diagram 1: Charging Stage 2 (Auto pop up: Charging 85% ⚡)
    TIMER = 4         # Diagram 1: Timer Stage 2 (Timer 00:00 + Operations)
    BG_APP = 5        # Diagram 2: Background App Stage 2 (Detached Island: Logo + Pill)
    ALL_TOGETHER = 6  # Diagram 3: All Together Stage 2 (Multi-tasking composite card)

    # Base reference sizes optimized for 1600x900 screens
    STATES = {
        COMPACT:      dict(w=120, h=32, r=16),
        MUSIC_S2:     dict(w=230, h=38, r=19),
        MUSIC_S3:     dict(w=320, h=148, r=24),
        CHARGING:     dict(w=260, h=38, r=19),
        TIMER:        dict(w=270, h=112, r=22),
        BG_APP:       dict(w=136, h=34, r=17),
        ALL_TOGETHER: dict(w=330, h=140, r=24),
    }

    def __init__(self):
        super().__init__()
        # Frameless, Always on Top, Non-minimizing top overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMinimumSize(0, 0)
        self.setMouseTracking(True)
        self.setWindowTitle("Dynamic Island")

        global FONT_FAMILY
        FONT_FAMILY = get_font_family()

        # Load persisted settings
        cfg = load_config()
        self.current_theme_key = cfg.get("theme", "liquid_glass")
        if self.current_theme_key not in THEMES:
            self.current_theme_key = "liquid_glass"
        self.theme = THEMES[self.current_theme_key]

        self.size_scale = float(cfg.get("size_scale", 1.0))
        self.size_scale = max(0.65, min(1.60, self.size_scale))

        # Springs for width, height, radius, and vertical position
        self.s_w = Spring()
        self.s_h = Spring()
        self.s_r = Spring()
        self.s_y = Spring(stiffness=210.0, damping=29.0)

        self.state = self.COMPACT
        self.hidden = False
        self.hidden_since = 0.0
        self._cursor_has_left = True

        # Geometry for 1600x900 display
        screen_geometry = QApplication.primaryScreen().geometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        self.ui_scale = min(1.0, self.screen_width / 1600.0, self.screen_height / 900.0)

        self.center_x = screen_geometry.center().x()
        self.screen_top = screen_geometry.top()
        self.top_y = self.screen_top + 6

        init = self.STATES[self.COMPACT]
        self.s_w.value = self.s_w.target = init["w"]
        self.s_h.value = self.s_h.target = init["h"]
        self.s_r.value = self.s_r.target = init["r"]
        self.s_y.value = self.s_y.target = float(self.top_y)

        eff_scale = self.ui_scale * self.size_scale
        self.resize(int(self.s_w.value * eff_scale), int(self.s_h.value * eff_scale))
        self.move(int(self.center_x - self.width() / 2), self.top_y)

        # Dragging support
        self._drag_origin = None
        self._drag_window_origin = None
        self._dragged = False

        # Timer state
        self.timer_running = False
        self.timer_remaining = 0
        self.timer_deadline = 0.0

        # Battery state
        self.charging = False
        self.battery_level = 85
        self.charge_notice_until = 0.0

        # Music player state
        self.player_service = None
        self.player_status = "Stopped"
        self.track_title = "Starboy"
        self.track_artist = "The Weeknd"
        self.track_length = 230_000_000
        self.track_position = 45_000_000
        self.track_id = None
        self._player_interface = None
        self.demo_mode = False

        # Background app state
        self.bg_app_active = False
        self.bg_app_name = "Terminal"
        self.bg_app_icon = ">_"

        # Main animation / frame loop
        self.last_activity = time.monotonic()
        self._last_tick = self.last_activity
        self._last_displayed_minute = datetime.now().minute
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

        # Persistence timer: keeps window on all desktops and un-minimizable
        self.persistence_timer = QTimer(self)
        self.persistence_timer.timeout.connect(self._ensure_persistence)
        self.persistence_timer.start(3000)
        QTimer.singleShot(150, self._ensure_persistence)
        QTimer.singleShot(800, self._ensure_persistence)

        # DBus MPRIS connection
        self.bus = QDBusConnection.sessionBus()
        self.player_timer = QTimer(self)
        self.player_timer.timeout.connect(self._refresh_player)
        self.player_timer.start(1000)
        self._refresh_player()

        # Weather service
        self.weather_pool = QThreadPool.globalInstance()
        self.weather_text = ""
        self._refresh_weather()
        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self._refresh_weather)
        self.weather_timer.start(15 * 60 * 1000)

        # Battery polling
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self._refresh_battery)
        self.battery_timer.start(8000)
        self._refresh_battery()

        # Background app detection polling
        self.bg_app_timer = QTimer(self)
        self.bg_app_timer.timeout.connect(self._detect_background_app)
        self.bg_app_timer.start(5000)
        self._detect_background_app()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(50, self._ensure_persistence)

    def _ensure_persistence(self):
        make_window_persistent_all_desktops(self.windowTitle())

    def set_theme(self, theme_key):
        if theme_key in THEMES:
            self.current_theme_key = theme_key
            self.theme = THEMES[theme_key]
            save_config({"theme": self.current_theme_key, "size_scale": self.size_scale})
            self.update()

    def set_size_scale(self, scale):
        self.size_scale = max(0.65, min(1.60, float(scale)))
        save_config({"theme": self.current_theme_key, "size_scale": self.size_scale})
        eff_scale = self.ui_scale * self.size_scale
        if not self.hidden:
            s = self.STATES[self.state]
            self.s_w.target = float(s["w"])
            self.s_h.target = float(s["h"])
            self.s_r.target = float(s["r"])
        self.timer.setInterval(16)
        self.timer.start()

    # ---------- state transitions ----------
    def set_state(self, state):
        if state == self.state:
            return
        self.state = state
        self.last_activity = time.monotonic()
        if not self.hidden:
            s = self.STATES[state]
            self.s_w.target = float(s["w"])
            self.s_h.target = float(s["h"])
            self.s_r.target = float(s["r"])
            self.s_y.target = float(self.top_y)
        if self.timer.interval() > 16:
            self.timer.setInterval(16)
        self.timer.start()

    def _place_window(self):
        nw = self.width()
        cur_y = int(self.s_y.value)
        self.move(int(self.center_x - nw / 2), cur_y)

    def _set_hidden(self, hidden):
        if self.hidden == hidden:
            return
        self.hidden = hidden
        self.hidden_since = time.monotonic()
        self._cursor_has_left = False

        if hidden:
            # Diagram 2 Row 1: Morph into a sleek screen-edge tab anchored at y=0
            self.s_w.target = 96.0
            self.s_h.target = 14.0
            self.s_r.target = 8.0
            self.s_y.target = float(self.screen_top)
        else:
            # Restore active state
            s = self.STATES[self.state]
            self.s_w.target = float(s["w"])
            self.s_h.target = float(s["h"])
            self.s_r.target = float(s["r"])
            self.s_y.target = float(self.top_y)
            self._cursor_has_left = True
            self.raise_()

        if self.timer.interval() > 16:
            self.timer.setInterval(16)
        self.timer.start()

    # ---------- mouse & gestures ----------
    def enterEvent(self, event):
        if self.hidden and self._cursor_has_left:
            self._set_hidden(False)
        self.last_activity = time.monotonic()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.last_activity = time.monotonic()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.hidden:
                self._set_hidden(True)
            else:
                self._set_hidden(False)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_origin
            if delta.manhattanLength() >= QApplication.startDragDistance():
                self._dragged = True
                self.move(self._drag_window_origin + delta)
            self.last_activity = time.monotonic()
            return
        self.last_activity = time.monotonic()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, e):
        self.last_activity = time.monotonic()
        if self.hidden:
            self._set_hidden(False)
            return
        if e.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(e.globalPosition().toPoint())
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = e.globalPosition().toPoint()
            self._drag_window_origin = self.pos()
            self._dragged = False

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_origin is not None:
            dragged = self._dragged
            eff_scale = self.ui_scale * self.size_scale
            click_x = event.position().x() / eff_scale
            click_y = event.position().y() / eff_scale
            self._drag_origin = None
            self._drag_window_origin = None
            self._dragged = False
            if dragged and self.y() <= self.top_y - 3:
                self._set_hidden(True)
            else:
                self._place_window()
                if not dragged:
                    self._handle_click(click_x, click_y)
        super().mouseReleaseEvent(event)

    def _handle_click(self, x, y):
        # Hidden peek click: restore
        if self.hidden:
            self._set_hidden(False)
            return

        # Stage 3 Music clicks: controls & scrubber
        if self.state == self.MUSIC_S3:
            if self._handle_music_stage3_click(x, y):
                return
            self.set_state(self.MUSIC_S2)
            return

        # Stage 2 Music clicks: expand to Stage 3
        if self.state == self.MUSIC_S2:
            self.set_state(self.MUSIC_S3)
            return

        # Stage 2 Timer clicks: operations
        if self.state == self.TIMER:
            if self._handle_timer_click(x, y):
                return
            self.set_state(self.COMPACT)
            return

        # Stage 2 Charging clicks: dismiss
        if self.state == self.CHARGING:
            self.set_state(self.COMPACT)
            return

        # Stage 2 Background App clicks: expand
        if self.state == self.BG_APP:
            if self.player_status == "Playing" or self.demo_mode or self.timer_remaining:
                self.set_state(self.ALL_TOGETHER)
            else:
                self.set_state(self.COMPACT)
            return

        # Stage 2 All Together clicks
        if self.state == self.ALL_TOGETHER:
            eff_scale = self.ui_scale * self.size_scale
            w = self.width() / eff_scale
            if x > w - 105 and 35 <= y <= 70:
                self.set_state(self.TIMER)
                return
            if x <= w - 105 and 35 <= y <= 70:
                self.set_state(self.MUSIC_S3)
                return
            self.set_state(self.COMPACT)
            return

        # Stage 1 Compact clicks: open appropriate active stage
        if self.state == self.COMPACT:
            self._open_active_state()

    def _open_active_state(self):
        has_music = (self.player_status == "Playing") or self.demo_mode
        has_timer = self.timer_remaining > 0
        has_bg = self.bg_app_active

        if has_music and has_timer:
            self.set_state(self.ALL_TOGETHER)
        elif has_timer:
            self.set_state(self.TIMER)
        elif has_music:
            self.set_state(self.MUSIC_S2)
        elif has_bg:
            self.set_state(self.BG_APP)
        else:
            self.set_state(self.MUSIC_S2)

    def _handle_music_stage3_click(self, x, y):
        eff_scale = self.ui_scale * self.size_scale
        w = self.width() / eff_scale
        cx = w / 2

        # Scrubber bar click: y in [118, 142]
        if y >= 118:
            x1, x2 = 24.0, w - 24.0
            ratio = min(1.0, max(0.0, (x - x1) / (x2 - x1)))
            self._seek_player(ratio)
            return True

        # Media controls row: y in [76, 114]
        if 76 <= y <= 114:
            if cx - 70 <= x <= cx - 30:
                self._control_player("Previous")
                return True
            if cx - 22 <= x <= cx + 22:
                self._control_player("PlayPause")
                return True
            if cx + 22 < x <= cx + 70:
                self._control_player("Next")
                return True

        return False

    def _handle_timer_click(self, x, y):
        w_unscaled = self.width() / (self.ui_scale * self.size_scale)

        # Close (✕) button: top-right corner
        if x >= w_unscaled - 36 and y <= 44:
            return False  # triggers set_state(COMPACT) in caller

        # Click on time display to set duration
        if y < 50 and 24 <= x <= w_unscaled - 40:
            self._prompt_timer_duration()
            return True

        btn_y = 60.0
        btn_h = 36.0
        if btn_y <= y <= btn_y + btn_h:
            btn_w = (w_unscaled - 44) / 4
            bx = 22.0
            # Pause/Start
            if bx <= x <= bx + btn_w:
                self._pause_or_resume_timer()
                return True
            bx += btn_w + 4
            # Reset
            if bx <= x <= bx + btn_w:
                self.timer_running = False
                self.timer_remaining = 0
                self.update()
                return True
            bx += btn_w + 4
            # +1m
            if bx <= x <= bx + btn_w:
                self.timer_remaining += 60
                self.timer_running = True
                self.timer_deadline = time.monotonic() + self.timer_remaining
                self.update()
                return True
            bx += btn_w + 4
            # +5m
            if bx <= x <= bx + btn_w:
                self.timer_remaining += 300
                self.timer_running = True
                self.timer_deadline = time.monotonic() + self.timer_remaining
                self.update()
                return True
        return False

    # ---------- timer operations ----------
    def _prompt_timer_duration(self):
        minutes, accepted = QInputDialog.getInt(
            self, "Set Timer", "Duration (minutes):", 5, 1, 24 * 60
        )
        if accepted:
            self.timer_remaining = minutes * 60
            self._start_timer()
            self.set_state(self.TIMER)

    def _start_timer(self):
        if self.timer_remaining:
            self.timer_running = True
            self.timer_deadline = time.monotonic() + self.timer_remaining

    def _pause_or_resume_timer(self):
        if self.timer_running:
            self.timer_remaining = max(0, int(self.timer_deadline - time.monotonic() + 0.999))
            self.timer_running = False
        else:
            if not self.timer_remaining:
                self.timer_remaining = 300
            self._start_timer()
        self.update()

    # ---------- context menu ----------
    def _show_context_menu(self, position):
        menu = QMenu(self)

        # 🎨 Themes Submenu
        theme_menu = menu.addMenu("🎨 Theme")
        for key, tdata in THEMES.items():
            check = " ✓" if key == self.current_theme_key else ""
            action = theme_menu.addAction(f"{tdata['name']}{check}")
            action.triggered.connect(lambda checked, k=key: self.set_theme(k))

        # 📐 Size Submenu
        size_menu = menu.addMenu("📐 Island Size")
        presets = [
            ("Small (85%)", 0.85),
            ("Normal (100% - Recommended)", 1.0),
            ("Medium-Large (115%)", 1.15),
            ("Large (130%)", 1.30),
        ]
        for label, val in presets:
            check = " ✓" if abs(self.size_scale - val) < 0.02 else ""
            action = size_menu.addAction(f"{label}{check}")
            action.triggered.connect(lambda checked, v=val: self.set_size_scale(v))

        size_menu.addSeparator()
        custom_act = size_menu.addAction("Custom Size…")
        custom_act.triggered.connect(self._prompt_custom_size)

        menu.addSeparator()

        # Direct state selectors matching diagram
        act_s1 = menu.addAction("Stage 1: Compact (Default)")
        act_music_s2 = menu.addAction("Stage 2: Music (00:00 + Equalizer)")
        act_music_s3 = menu.addAction("Stage 3: Music (Expanded Player)")
        act_charging = menu.addAction("Stage 2: Charging Popup (Charging [battery%] ⚡)")
        act_timer = menu.addAction("Stage 2: Timer Operations")
        act_bg_app = menu.addAction("Stage 2: Background App (Detached Island)")
        act_all = menu.addAction("Stage 2: All Together (Multi-tasking Card)")

        menu.addSeparator()
        if self.hidden:
            act_hide = menu.addAction("Unhide island")
        else:
            act_hide = menu.addAction("Hide to screen edge (Diagram 2)")

        act_set_timer = menu.addAction("Set custom timer…")
        menu.addSeparator()

        # Demo toggles
        demo_music_title = "Demo: Pause Music" if (self.player_status == "Playing" or self.demo_mode) else "Demo: Play Simulated Music"
        act_demo_music = menu.addAction(demo_music_title)

        act_demo_charge = menu.addAction("Demo: Trigger Charging Popup (3s)")
        bg_title = "Demo: Turn Off Background App" if self.bg_app_active else "Demo: Turn On Background App"
        act_demo_bg = menu.addAction(bg_title)

        menu.addSeparator()
        act_quit = menu.addAction("Quit Dynamic Island")

        chosen = menu.exec(position)
        if not chosen:
            return

        if chosen == act_s1:
            self._set_hidden(False)
            self.set_state(self.COMPACT)
        elif chosen == act_music_s2:
            self._set_hidden(False)
            self.set_state(self.MUSIC_S2)
        elif chosen == act_music_s3:
            self._set_hidden(False)
            self.set_state(self.MUSIC_S3)
        elif chosen == act_charging:
            self._set_hidden(False)
            self.last_activity = time.monotonic()
            self.charge_notice_until = time.monotonic() + 3.0
            self.set_state(self.CHARGING)
        elif chosen == act_timer:
            self._set_hidden(False)
            if not self.timer_remaining:
                self.timer_remaining = 300
                self.timer_running = True
                self.timer_deadline = time.monotonic() + 300
            self.set_state(self.TIMER)
        elif chosen == act_bg_app:
            self._set_hidden(False)
            self.bg_app_active = True
            self.set_state(self.BG_APP)
        elif chosen == act_all:
            self._set_hidden(False)
            self.demo_mode = True
            if not self.timer_remaining:
                self.timer_remaining = 245
                self.timer_running = True
                self.timer_deadline = time.monotonic() + 245
            self.bg_app_active = True
            self.set_state(self.ALL_TOGETHER)
        elif chosen == act_hide:
            self._set_hidden(not self.hidden)
        elif chosen == act_set_timer:
            self._prompt_timer_duration()
        elif chosen == act_demo_music:
            if self.player_status == "Playing" or self.demo_mode:
                self.demo_mode = False
                self.player_status = "Paused"
            else:
                self.demo_mode = True
                self.player_status = "Playing"
            self.update()
        elif chosen == act_demo_charge:
            self._set_hidden(False)
            self.last_activity = time.monotonic()
            self.charge_notice_until = time.monotonic() + 3.0
            self.set_state(self.CHARGING)
        elif chosen == act_demo_bg:
            self.bg_app_active = not self.bg_app_active
            self.update()
        elif chosen == act_quit:
            QApplication.quit()

    def _prompt_custom_size(self):
        val, accepted = QInputDialog.getInt(
            self, "Custom Size", "Scale percentage (70 - 160%):", int(self.size_scale * 100), 70, 160
        )
        if accepted:
            self.set_size_scale(val / 100.0)

    # ---------- hardware & services ----------
    def _detect_background_app(self):
        try:
            out = subprocess.check_output(
                ["ps", "-u", os.environ.get("USER", "noroot"), "-o", "comm"],
                stderr=subprocess.DEVNULL
            ).decode()
            procs = set(out.splitlines())
            if any(p in procs for p in ["gnome-terminal", "alacritty", "kitty", "xterm", "bash"]):
                self.bg_app_name = "Terminal"
                self.bg_app_icon = ">_"
                self.bg_app_active = True
            elif any(p in procs for p in ["code", "antigravity-ide"]):
                self.bg_app_name = "Code"
                self.bg_app_icon = "</>"
                self.bg_app_active = True
            elif any(p in procs for p in ["firefox", "chrome", "chromium"]):
                self.bg_app_name = "Browser"
                self.bg_app_icon = "🌐"
                self.bg_app_active = True
        except Exception:
            pass

    def _refresh_battery(self):
        power_path = "/sys/class/power_supply"
        charging = False
        battery_level = None
        if os.path.isdir(power_path):
            try:
                for name in os.listdir(power_path):
                    supply = os.path.join(power_path, name)
                    try:
                        with open(os.path.join(supply, "type"), encoding="utf-8") as f:
                            stype = f.read().strip()
                        if stype == "Battery":
                            with open(os.path.join(supply, "capacity"), encoding="utf-8") as f:
                                battery_level = int(f.read().strip())
                            with open(os.path.join(supply, "status"), encoding="utf-8") as f:
                                charging = charging or (f.read().strip().lower() == "charging")
                    except Exception:
                        continue
            except Exception:
                pass

        if battery_level is not None:
            self.battery_level = battery_level
        was_charging = self.charging
        self.charging = charging

        # Diagram 1: Auto pop up when plugged in / charging starts
        if charging and not was_charging:
            self.last_activity = time.monotonic()
            self.charge_notice_until = time.monotonic() + 3.0
            self._set_hidden(False)
            self.set_state(self.CHARGING)
        self.update()

    @staticmethod
    def _unwrap_dbus(value):
        if isinstance(value, QDBusVariant):
            return DynamicIsland._unwrap_dbus(value.variant())
        if isinstance(value, dict):
            return {k: DynamicIsland._unwrap_dbus(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [DynamicIsland._unwrap_dbus(v) for v in value]
        return value

    def _get_player_property(self, properties, name):
        reply = properties.call("Get", MPRIS_PLAYER_INTERFACE, name)
        if reply.type().name == "ErrorMessage":
            return None
        args = reply.arguments()
        return self._unwrap_dbus(args[0]) if args else None

    def _refresh_player(self):
        if not self.bus.isConnected():
            return

        names_reply = self.bus.interface().registeredServiceNames()
        if not names_reply.isValid():
            return

        services = sorted(
            n for n in names_reply.value() if n.startswith("org.mpris.MediaPlayer2.")
        )
        candidates = []
        for service in services:
            props = QDBusInterface(service, MPRIS_PATH, DBUS_PROPERTIES_INTERFACE, self.bus)
            if not props.isValid():
                continue
            status = self._get_player_property(props, "PlaybackStatus")
            meta = self._get_player_property(props, "Metadata")
            if isinstance(meta, dict):
                candidates.append((service, props, status, meta))

        selected = next((c for c in candidates if c[2] == "Playing"), candidates[0] if candidates else None)
        if selected is None:
            if not self.demo_mode:
                self.player_service = None
                self._player_interface = None
                self.player_status = "Stopped"
        else:
            service, props, status, meta = selected
            self.player_service = service
            self._player_interface = QDBusInterface(service, MPRIS_PATH, MPRIS_PLAYER_INTERFACE, self.bus)
            self.player_status = status or "Stopped"
            self.track_title = str(meta.get("xesam:title") or "Nothing playing")
            artists = meta.get("xesam:artist") or []
            if isinstance(artists, str):
                artists = [artists]
            self.track_artist = ", ".join(map(str, artists)) or service.removeprefix("org.mpris.MediaPlayer2.")
            self.track_length = max(0, int(meta.get("mpris:length") or 0))
            self.track_id = meta.get("mpris:trackid")
            self.track_position = max(0, int(self._get_player_property(props, "Position") or 0))

        self.update()

    def _control_player(self, method):
        if self._player_interface is not None and self._player_interface.isValid():
            self._player_interface.call(method)
            QTimer.singleShot(150, self._refresh_player)
        else:
            if method == "PlayPause":
                if self.player_status == "Playing" or self.demo_mode:
                    self.player_status = "Paused"
                    self.demo_mode = False
                else:
                    self.player_status = "Playing"
                    self.demo_mode = True
            elif method == "Next":
                self.track_title = "Blinding Lights"
                self.track_artist = "The Weeknd"
                self.track_position = 0
            elif method == "Previous":
                self.track_title = "Save Your Tears"
                self.track_artist = "The Weeknd"
                self.track_position = 0
            self.update()

    def _seek_player(self, progress):
        if self._player_interface is not None and self._player_interface.isValid() and self.track_length and self.track_id:
            self._player_interface.call(
                "SetPosition", QDBusObjectPath(str(self.track_id)), int(self.track_length * progress)
            )
        else:
            self.track_position = int(self.track_length * progress)
            self.update()

    def _request_weather(self, url, stage):
        fetch = WeatherFetch(url, stage)
        fetch.setAutoDelete(False)
        _WEATHER_FETCHES.add(fetch)
        fetch.signals.finished.connect(self._weather_reply_finished)
        self.weather_pool.start(fetch)

    def _refresh_weather(self):
        query = QUrlQuery()
        query.addQueryItem("name", WEATHER_LOCATION)
        query.addQueryItem("count", "1")
        query.addQueryItem("language", "en")
        query.addQueryItem("format", "json")
        url = QUrl("https://geocoding-api.open-meteo.com/v1/search")
        url.setQuery(query)
        self._request_weather(url.toString(), "geocoding")

    def _weather_reply_finished(self, fetch, stage, payload, error):
        _WEATHER_FETCHES.discard(fetch)
        if error:
            return
        try:
            data = json.loads(payload)
        except Exception:
            return
        if stage == "geocoding":
            results = data.get("results") or []
            if not results:
                return
            loc = results[0]
            query = QUrlQuery()
            query.addQueryItem("latitude", str(loc["latitude"]))
            query.addQueryItem("longitude", str(loc["longitude"]))
            query.addQueryItem("current", "temperature_2m,relative_humidity_2m,weather_code")
            query.addQueryItem("temperature_unit", "celsius")
            query.addQueryItem("timezone", "auto")
            url = QUrl("https://api.open-meteo.com/v1/forecast")
            url.setQuery(query)
            self._request_weather(url.toString(), "forecast")
        elif stage == "forecast":
            current = data.get("current") or {}
            temp = current.get("temperature_2m")
            if temp is not None:
                self.weather_text = f"{float(temp):.0f}°C"
                self.update()

    # ---------- per-frame update ----------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.05, max(0.001, now - self._last_tick))
        self._last_tick = now

        # Music simulated progress
        is_playing = (self.player_status == "Playing") or self.demo_mode
        if is_playing:
            self.track_position += int(dt * 1_000_000)
            if self.track_length and self.track_position >= self.track_length:
                self.track_position = 0

        # Timer countdown
        if self.timer_running:
            self.timer_remaining = max(0, int(self.timer_deadline - now + 0.999))
            if self.timer_remaining == 0:
                self.timer_running = False
                if self.state == self.TIMER:
                    self.set_state(self.COMPACT)

        # Charging auto popup auto-collapse (Diagram 1 Row 2)
        if self.state == self.CHARGING and now >= self.charge_notice_until:
            self.set_state(self.COMPACT)

        # Inactivity auto collapse: after 3 sec of no activity get back to default state (COMPACT)
        if self.state != self.COMPACT and not self.hidden:
            if now - self.last_activity >= 3.0:
                self.set_state(self.COMPACT)

        # Hidden reveal on hover at top screen edge (Diagram 2)
        if self.hidden:
            cursor = QCursor.pos()
            if not self._cursor_has_left:
                if cursor.y() > self.screen_top + 32 or abs(cursor.x() - self.center_x) > 100:
                    self._cursor_has_left = True
            else:
                if (
                    abs(cursor.x() - self.center_x) <= 55
                    and self.screen_top <= cursor.y() <= self.screen_top + 16
                ):
                    self._set_hidden(False)

        # Step all springs
        self.s_w.step(dt)
        self.s_h.step(dt)
        self.s_r.step(dt)
        self.s_y.step(dt)

        eff_scale = self.ui_scale * self.size_scale
        nw = int(self.s_w.value * eff_scale)
        nh = int(self.s_h.value * eff_scale)
        if (nw, nh) != (self.width(), self.height()):
            self.resize(nw, nh)

        self._place_window()

        animating = any(
            abs(s.value - s.target) >= 0.05 or abs(s.velocity) >= 0.05
            for s in (self.s_w, self.s_h, self.s_r, self.s_y)
        )
        needs_high_fps = animating or is_playing or self.timer_running
        target_interval = 16 if needs_high_fps else (60 if self.hidden else 500)
        if self.timer.interval() != target_interval:
            self.timer.setInterval(target_interval)

        self.update()

    # ---------- painting (Liquid Glass & Themes) ----------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        eff_scale = self.ui_scale * self.size_scale
        p.scale(eff_scale, eff_scale)

        w = self.width() / eff_scale
        h = self.height() / eff_scale
        radius = self.s_r.value
        t = self.theme
        accent = t["accent"]
        accent_alt = t["accent_alt"]
        white = QColor(255, 255, 255)
        gray = QColor(160, 160, 168)
        is_playing = (self.player_status == "Playing") or self.demo_mode

        # Diagram 2 Row 1: While Hidden (Screen Edge peek tab)
        if self.hidden:
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, -6, w, h + 6), radius, radius)
            self._paint_glass_background(p, path, w, h)
            # Dot is centered right in the peeking bottom sliver
            self._draw_status_dot(p, w / 2, h / 2 + 1, radius=3.2, color=accent)
            return

        # Diagram 2 Row 2: Background App Running (Detached Island / Dual Pill)
        if self.state == self.BG_APP:
            bubble_size = h
            pill_x = bubble_size + 10

            # Left detached circle
            path_left = QPainterPath()
            path_left.addRoundedRect(QRectF(0, 0, bubble_size, bubble_size), bubble_size / 2, bubble_size / 2)
            self._paint_glass_background(p, path_left, bubble_size, bubble_size)

            # Right main pill
            path_right = QPainterPath()
            path_right.addRoundedRect(QRectF(pill_x, 0, w - pill_x, h), h / 2, h / 2)
            self._paint_glass_background(p, path_right, w - pill_x, h, offset_x=pill_x)

            # Left circle logo
            p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(0, 0, bubble_size, bubble_size), Qt.AlignmentFlag.AlignCenter, self.bg_app_icon)

            # Right pill status dot
            self._draw_status_dot(p, w - 18, h / 2, radius=3.5, color=accent)
            return

        # Main Island Shape
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        self._paint_glass_background(p, path, w, h)

        # Diagram 1 & 2 & 3: Stage 1 Compact — minimal: camera dot + clock + status dot
        if self.state == self.COMPACT:
            # Camera lens dot (left)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(18, 18, 24, 200))
            p.drawEllipse(QRectF(14, h / 2 - 4.5, 9, 9))

            # Live clock (center)
            now_str = datetime.now().strftime("%H:%M")
            p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(30, 0, w - 52, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, now_str)

            # Glowing status dot (right)
            self._draw_status_dot(p, w - 14, h / 2, radius=3.0,
                                  color=accent if (is_playing or self.timer_running) else QColor(120, 120, 140))
            return

        # Diagram 1 Row 1: Stage 2 Music
        if self.state == self.MUSIC_S2:
            time_str = self._current_playback_or_clock_str()
            # Left: time
            p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(16, 0, 68, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, time_str)
            # Center: artist name (truncated)
            p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
            p.setPen(QColor(180, 180, 190))
            artist_rect = QRectF(88, 0, w - 130, h)
            p.drawText(artist_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                       p.fontMetrics().elidedText(self.track_artist, Qt.TextElideMode.ElideRight, int(w - 132)))
            # Right: equalizer bars
            self._draw_bars(p, w - 24, h / 2, color=accent, active=is_playing)
            return

        # Diagram 1 Row 1: Stage 3 Music (Expanded Player)
        if self.state == self.MUSIC_S3:
            time_str = self._current_playback_or_clock_str()
            # Top row: 00:00 on left, equalizer bars on right
            p.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(22, 10, 60, 22), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, time_str)
            self._draw_bars(p, w - 32, 21, color=accent, active=is_playing)

            # Middle row: logo on left, Song_title
            p.setPen(QPen(t["btn_border"], 1))
            p.setBrush(t["badge_bg"])
            p.drawRoundedRect(QRectF(22, 40, 32, 32), 8, 8)
            p.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
            p.setPen(accent)
            p.drawText(QRectF(22, 40, 32, 32), Qt.AlignmentFlag.AlignCenter, "♫")

            # Song title and artist
            p.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(
                QRectF(64, 38, w - 86, 18),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                p.fontMetrics().elidedText(self.track_title, Qt.TextElideMode.ElideRight, int(w - 90))
            )
            p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Normal))
            p.setPen(gray)
            p.drawText(
                QRectF(64, 57, w - 86, 15),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                p.fontMetrics().elidedText(self.track_artist, Qt.TextElideMode.ElideRight, int(w - 90))
            )

            # Media controls: |<<  ||  >>|
            cx = w / 2
            cy = 93
            p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(cx - 58, cy - 14, 28, 28), Qt.AlignmentFlag.AlignCenter, "◀◀")

            # Play / Pause circle button
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(white)
            p.drawEllipse(QRectF(cx - 15, cy - 15, 30, 30))
            p.setBrush(QColor(10, 10, 15))
            if is_playing:
                p.drawRoundedRect(QRectF(cx - 5, cy - 6, 3, 12), 1, 1)
                p.drawRoundedRect(QRectF(cx + 2, cy - 6, 3, 12), 1, 1)
            else:
                play = QPainterPath()
                play.moveTo(cx - 3, cy - 7)
                play.lineTo(cx + 6, cy)
                play.lineTo(cx - 3, cy + 7)
                play.closeSubpath()
                p.drawPath(play)

            p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(cx + 30, cy - 14, 28, 28), Qt.AlignmentFlag.AlignCenter, "▶▶")

            # Bottom scrubber row: o───────o
            x1, x2 = 24.0, w - 24.0
            scrub_y = 130.0
            p.setPen(QPen(QColor(70, 70, 80, 160), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(int(x1), int(scrub_y), int(x2), int(scrub_y))
            ratio = min(1.0, max(0.0, self.track_position / max(1, self.track_length)))
            prog_x = x1 + (x2 - x1) * ratio
            p.setPen(QPen(accent, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(int(x1), int(scrub_y), int(prog_x), int(scrub_y))

            # Endpoint dots
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(160, 160, 168))
            p.drawEllipse(QRectF(x1 - 2.5, scrub_y - 2.5, 5, 5))
            p.drawEllipse(QRectF(x2 - 2.5, scrub_y - 2.5, 5, 5))
            # Scrub thumb
            p.setBrush(white)
            p.drawEllipse(QRectF(prog_x - 4.5, scrub_y - 4.5, 9, 9))
            return

        # Diagram 1 Row 2: Stage 2 Charging (Auto pop up)
        if self.state == self.CHARGING:
            # Charging bolt icon (left)
            p.setFont(QFont(FONT_FAMILY, 15, QFont.Weight.Bold))
            p.setPen(accent)
            p.drawText(QRectF(16, 0, 26, h), Qt.AlignmentFlag.AlignCenter, "⚡")

            # "Charging" label
            p.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(46, 0, 82, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Charging")

            # Battery percentage with color coding
            lvl = self.battery_level if self.battery_level is not None else 0
            if lvl >= 80:
                bat_color = QColor(48, 209, 88)   # Green – healthy
            elif lvl >= 40:
                bat_color = QColor(255, 196, 0)   # Amber – mid
            else:
                bat_color = QColor(255, 80, 80)   # Red – low
            p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
            p.setPen(bat_color)
            p.drawText(QRectF(132, 0, 72, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f"{lvl}%")

            # Tap to dismiss hint
            p.setFont(QFont(FONT_FAMILY, 8, QFont.Weight.Normal))
            p.setPen(QColor(160, 160, 170, 180))
            p.drawText(QRectF(0, 0, w - 10, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "tap to dismiss")
            return

        # Diagram 1 Row 3: Stage 2 Timer
        if self.state == self.TIMER:
            # Top row: Timer label + countdown + ✕ close button
            p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.DemiBold))
            p.setPen(gray)
            p.drawText(QRectF(20, 10, 52, 28), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "Timer")

            m, s = divmod(self.timer_remaining, 60)
            p.setFont(QFont(FONT_FAMILY, 20, QFont.Weight.Bold))
            p.setPen(accent_alt)
            p.drawText(QRectF(72, 6, 140, 36), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f"{m:02d}:{s:02d}")

            # ✕ Close button — top right, circular
            close_cx = w - 22
            close_cy = 24
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(80, 80, 100, 140))
            p.drawEllipse(QRectF(close_cx - 12, close_cy - 12, 24, 24))
            p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
            p.setPen(QColor(220, 220, 230))
            p.drawText(QRectF(close_cx - 12, close_cy - 12, 24, 24), Qt.AlignmentFlag.AlignCenter, "✕")

            # Separator line
            p.setPen(QPen(QColor(80, 80, 100, 100), 0.8))
            p.drawLine(int(18), int(50), int(w - 18), int(50))

            # Bottom row buttons: evenly distributed
            btn_y = 60.0
            btn_h = 36.0
            avail_w = w - 44
            btn_w = avail_w / 4
            gap = 4.0
            btn_labels = ["Pause" if self.timer_running else "Start", "Reset", "+1m", "+5m"]

            for i, label in enumerate(btn_labels):
                bx = 22.0 + i * (btn_w + gap)
                p.setPen(QPen(t["btn_border"], 1))
                p.setBrush(t["btn_bg"])
                p.drawRoundedRect(QRectF(bx, btn_y, btn_w, btn_h), 14, 14)
                p.setPen(white)
                p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.DemiBold))
                p.drawText(QRectF(bx, btn_y, btn_w, btn_h), Qt.AlignmentFlag.AlignCenter, label)
            return

        # Diagram 3 Row 2: Stage 2 (All Together)
        if self.state == self.ALL_TOGETHER:
            time_str = self._current_playback_or_clock_str()

            # ── TOP ROW: playback/clock  |  ⚡ battery  |  equalizer bars ──
            p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(20, 8, 58, 22), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, time_str)

            # Battery — only if available
            if self.battery_level is not None:
                bat_icon = "⚡" if self.charging else "🔋"
                lvl = self.battery_level
                if lvl >= 80:
                    bat_col = accent
                elif lvl >= 40:
                    bat_col = QColor(255, 196, 0)
                else:
                    bat_col = QColor(255, 80, 80)
                p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
                p.setPen(bat_col)
                p.drawText(QRectF(82, 8, w - 160, 22), Qt.AlignmentFlag.AlignCenter, f"{bat_icon} {lvl}%")

            self._draw_bars(p, w - 28, 19, color=accent, active=is_playing)

            # ── DIVIDER ──
            p.setPen(QPen(QColor(80, 80, 100, 100), 0.8))
            p.drawLine(int(18), int(38), int(w - 18), int(38))

            # ── MIDDLE ROW: music track info (left) | timer (right) ──
            # Album art placeholder
            p.setPen(QPen(t["btn_border"], 1))
            p.setBrush(t["badge_bg"])
            p.drawRoundedRect(QRectF(20, 46, 28, 28), 7, 7)
            p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
            p.setPen(accent)
            p.drawText(QRectF(20, 46, 28, 28), Qt.AlignmentFlag.AlignCenter, "♫")

            # Track title
            p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(
                QRectF(54, 46, w - 160, 16),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                p.fontMetrics().elidedText(self.track_title, Qt.TextElideMode.ElideRight, int(w - 162))
            )
            # Track artist
            p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
            p.setPen(gray)
            p.drawText(
                QRectF(54, 63, w - 160, 14),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                p.fontMetrics().elidedText(self.track_artist, Qt.TextElideMode.ElideRight, int(w - 162))
            )

            # Timer countdown (right side)
            m, s = divmod(self.timer_remaining, 60)
            p.setFont(QFont(FONT_FAMILY, 15, QFont.Weight.Bold))
            p.setPen(accent_alt)
            p.drawText(QRectF(w - 105, 42, 88, 36), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, f"{m:02d}:{s:02d}")
            # Timer label
            p.setFont(QFont(FONT_FAMILY, 8, QFont.Weight.Normal))
            p.setPen(gray)
            p.drawText(QRectF(w - 105, 75, 88, 14), Qt.AlignmentFlag.AlignCenter, "timer")

            # ── DIVIDER ──
            p.setPen(QPen(QColor(80, 80, 100, 100), 0.8))
            p.drawLine(int(18), int(90), int(w - 18), int(90))

            # ── BOTTOM ROW: bg app info | status dot ──
            p.setPen(QPen(t["btn_border"], 1))
            p.setBrush(t["badge_bg"])
            p.drawRoundedRect(QRectF(20, 97, 26, 26), 7, 7)
            p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
            p.setPen(white)
            p.drawText(QRectF(20, 97, 26, 26), Qt.AlignmentFlag.AlignCenter, self.bg_app_icon)

            p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Medium))
            p.setPen(QColor(200, 200, 210))
            p.drawText(QRectF(52, 97, 150, 26), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.bg_app_name)

            # Weather (right of bottom row)
            if self.weather_text:
                p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.DemiBold))
                p.setPen(QColor(180, 220, 255))
                p.drawText(QRectF(w - 80, 97, 62, 26), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, f"☁ {self.weather_text}")

            self._draw_status_dot(p, w - 12, 110, radius=3.5, color=accent)

    def _paint_glass_background(self, p, path, w, h, offset_x=0.0):
        t = self.theme

        # 1. Outer ambient shadow
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(QRectF(offset_x + 1, 1.5, w - 2, h - 2), self.s_r.value, self.s_r.value)
        p.setPen(QPen(QColor(0, 0, 0, 80), 2.5))
        p.drawPath(shadow_path)

        # 2. Main Glass Body Gradient
        bg_grad = QLinearGradient(offset_x, 0, offset_x, h)
        bg_grad.setColorAt(0.0, t["bg_top"])
        bg_grad.setColorAt(0.5, t["bg_mid"])
        bg_grad.setColorAt(1.0, t["bg_bot"])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg_grad))
        p.drawPath(path)

        # 3. Liquid Glass Top Sheen (refraction layer)
        if t["sheen"]:
            sheen_path = QPainterPath()
            sheen_h = max(6.0, h * 0.44)
            sheen_path.addRoundedRect(QRectF(offset_x + 1, 1, w - 2, sheen_h), self.s_r.value - 1, self.s_r.value - 1)
            sheen_grad = QLinearGradient(offset_x, 1, offset_x, sheen_h)
            sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 32))
            sheen_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(sheen_grad))
            p.drawPath(sheen_path)

        # 4. Specular Highlight Rim (Glass border)
        rim_grad = QLinearGradient(offset_x, 0, offset_x, h)
        rim_grad.setColorAt(0.0, t["rim_top"])
        rim_grad.setColorAt(0.65, QColor(255, 255, 255, 20))
        rim_grad.setColorAt(1.0, t["rim_bot"])
        p.setPen(QPen(QBrush(rim_grad), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    def _current_playback_or_clock_str(self):
        if (self.player_status == "Playing" or self.demo_mode) and self.track_length:
            pos_sec = self.track_position // 1_000_000
            m, s = divmod(pos_sec, 60)
            return f"{m:02d}:{s:02d}"
        return datetime.now().strftime("%H:%M")

    def _draw_status_dot(self, p, cx, cy, radius=3.5, color=None):
        if color is None:
            color = self.theme["accent"]
        glow = QColor(color.red(), color.green(), color.blue(), 55)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QRectF(cx - radius - 2.5, cy - radius - 2.5, (radius + 2.5) * 2, (radius + 2.5) * 2))
        p.setBrush(color)
        p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

    def _draw_bars(self, p, cx, cy, color=None, n=4, gap=3.5, bw=2.8, active=True):
        if color is None:
            color = self.theme["accent"]
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        base_x = cx - (n * (bw + gap)) / 2 + gap / 2
        phase = time.monotonic() * 5
        for i in range(n):
            amp = 5 + 9 * abs(math.sin(phase + i * 0.95)) if active else 3
            x = base_x + i * (bw + gap)
            p.drawRoundedRect(QRectF(x, cy - amp / 2, bw, amp), bw / 2, bw / 2)


def main():
    if (
        sys.platform.startswith("linux")
        and os.environ.get("WAYLAND_DISPLAY")
        and os.environ.get("QT_QPA_PLATFORM") == "xcb"
    ):
        import ctypes.util

        required_packages = {
            "xcb-cursor": "libxcb-cursor0",
            "xkbcommon-x11": "libxkbcommon-x11-0",
            "xcb-icccm": "libxcb-icccm4",
            "xcb-image": "libxcb-image0",
            "xcb-keysyms": "libxcb-keysyms1",
            "xcb-render-util": "libxcb-render-util0",
            "xcb-xkb": "libxcb-xkb1",
        }
        missing = [
            package for library, package in required_packages.items()
            if ctypes.util.find_library(library) is None
        ]
        if missing:
            print(
                "Missing Qt XWayland libraries. Install them with: sudo apt install "
                + " ".join(missing),
                file=sys.stderr,
            )
            return 1

    app = QApplication(sys.argv)
    island = DynamicIsland()
    island.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())