import os
import signal
import sys

import paho.mqtt.client as mqtt
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from src.mqtt_client import create_mqtt_client
from src.wayland_layer import LayerShellQt


class OverlayWindow(QWidget):
    sig_update = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self.sig_update.connect(self._on_update)

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setGeometry(10, 10, 200, 80)

    def _setup_ui(self) -> None:
        self.label_cpu = QLabel("CPU: 0%", self)
        self.label_ram = QLabel("RAM: 0%", self)
        for lbl in (self.label_cpu, self.label_ram):
            lbl.setStyleSheet(
                "color: #00ff00; font-size: 18px; font-weight: bold;"
                "padding: 2px 8px;"
                "background: rgba(0, 0, 0, 120);"
                "border-radius: 4px;"
            )

        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.label_cpu)
        layout.addWidget(self.label_ram)
        self.setLayout(layout)

    def _on_update(self, topic: str, value: str) -> None:
        if "cpu" in topic:
            self.label_cpu.setText(f"CPU: {value}%")
        elif "ram" in topic:
            self.label_ram.setText(f"RAM: {value}%")


def main() -> None:
    app = QApplication(sys.argv)

    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    signal.signal(signal.SIGTERM, lambda sig, frame: app.quit())

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(200)

    window = OverlayWindow()

    if os.environ.get("WAYLAND_DISPLAY"):
        _ = window.winId()
        layer = LayerShellQt()
        if layer.available():
            ok = layer.setup(window)
            print(f"Layer-shell: {'ativado' if ok else 'falhou, usando fallback'}")

    window.show()

    client = create_mqtt_client("overlay-pc")
    client.on_message = _build_on_message(window)
    client.subscribe("sistema/pc/#", qos=1)
    client.loop_start()

    app.aboutToQuit.connect(lambda: _cleanup(client))
    sys.exit(app.exec())


def _build_on_message(window: OverlayWindow):
    def on_message(_client: mqtt.Client, _userdata, msg: mqtt.MQTTMessage) -> None:
        window.sig_update.emit(msg.topic, msg.payload.decode())
    return on_message


def _cleanup(client: mqtt.Client) -> None:
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
