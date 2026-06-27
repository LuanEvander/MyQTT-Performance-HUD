import ctypes
import logging

logger = logging.getLogger(__name__)

# --- Enums ---
ANCHOR_NONE = 0
ANCHOR_TOP = 1
ANCHOR_BOTTOM = 2
ANCHOR_LEFT = 4
ANCHOR_RIGHT = 8

LAYER_BACKGROUND = 0
LAYER_BOTTOM = 1
LAYER_TOP = 2
LAYER_OVERLAY = 3

KEYBOARD_INTERACTIVITY_NONE = 0
KEYBOARD_INTERACTIVITY_EXCLUSIVE = 1
KEYBOARD_INTERACTIVITY_ON_DEMAND = 2


class QMargins(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_int),
        ("top", ctypes.c_int),
        ("right", ctypes.c_int),
        ("bottom", ctypes.c_int),
    ]


class LayerShellQt:
    """ctypes wrapper around libLayerShellQtInterface.so.6"""

    def __init__(self):
        self._lib = None
        self._load_library()

    def _load_library(self):
        try:
            self._lib = ctypes.CDLL("libLayerShellQtInterface.so.6")
        except OSError as e:
            logger.warning("Could not load libLayerShellQtInterface.so.6: %s", e)
            return

        self._window_get = self._lib._ZN12LayerShellQt6Window3getEP7QWindow
        self._window_get.argtypes = [ctypes.c_void_p]
        self._window_get.restype = ctypes.c_void_p

        self._set_anchors = self._lib._ZN12LayerShellQt6Window10setAnchorsE6QFlagsINS0_6AnchorEE
        self._set_anchors.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._set_anchors.restype = None

        self._set_layer = self._lib._ZN12LayerShellQt6Window8setLayerENS0_5LayerE
        self._set_layer.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._set_layer.restype = None

        self._set_keyboard_interactivity = self._lib._ZN12LayerShellQt6Window24setKeyboardInteractivityENS0_21KeyboardInteractivityE
        self._set_keyboard_interactivity.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._set_keyboard_interactivity.restype = None

        self._set_exclusive_zone = self._lib._ZN12LayerShellQt6Window16setExclusiveZoneEi
        self._set_exclusive_zone.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._set_exclusive_zone.restype = None

        self._set_margins = self._lib._ZN12LayerShellQt6Window10setMarginsERK8QMargins
        self._set_margins.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self._set_margins.restype = None

    def available(self) -> bool:
        return self._lib is not None

    def setup(self, qwidget, x=10, y=10, width=200, height=80) -> bool:
        if not self._lib:
            return False

        try:
            from shiboken6 import Shiboken

            qwindow = qwidget.windowHandle()
            if qwindow is None:
                logger.error("No QWindow available")
                return False

            ptr = Shiboken.getCppPointer(qwindow)
            if not ptr or not ptr[0]:
                logger.error("Failed to get QWindow pointer")
                return False

            layer_win = self._window_get(ctypes.c_void_p(ptr[0]))
            if not layer_win:
                logger.error("LayerShellQt::Window::get returned null")
                return False

            lw = ctypes.c_void_p(layer_win)

            self._set_layer(lw, ctypes.c_int(LAYER_OVERLAY))
            self._set_anchors(lw, ctypes.c_int(ANCHOR_TOP | ANCHOR_LEFT))
            self._set_keyboard_interactivity(lw, ctypes.c_int(KEYBOARD_INTERACTIVITY_NONE))
            self._set_exclusive_zone(lw, ctypes.c_int(-1))

            margins = QMargins(x, y, 0, 0)
            self._set_margins(lw, ctypes.pointer(margins))

            return True

        except Exception as e:
            logger.error("Layer-shell setup failed: %s", e)
            return False
