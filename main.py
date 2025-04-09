import sys
import socket
import threading
import struct
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QRadioButton, QButtonGroup, QLineEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, QTimer
import pyqtgraph as pg


class CommandBuilder:
    @staticmethod
    def build_goto_command(x: float, y: float) -> bytes:
        return struct.pack('Bff', 2, x, y)

    @staticmethod
    def build_manual_command(direction_code: int) -> bytes:
        return struct.pack('Bi', 3, direction_code)

    @staticmethod
    def build_stop_command() -> bytes:
        return struct.pack('B', 1)


class TCPClient(QObject):
    data_received = pyqtSignal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = False
        self.socket = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.thread.start()

    def listen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        try:
            while self.running:
                data = self.socket.recv(1024)
                if data:
                    self.data_received.emit(data.decode(errors='ignore'))
        finally:
            self.socket.close()

    def send(self, message: bytes):
        if self.socket:
            self.socket.sendall(message)

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()


class GoniometerControl(QWidget):
    def __init__(self):
        super().__init__()
        self.client = TCPClient("127.0.0.1", 9000)
        self.client.data_received.connect(self.handle_data)
        self.client.start()

        self.x_data = []
        self.y_data = []
        self.ptr = 0
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)

        self.direction_map = {
            "UP": 0,
            "DOWN": 1,
            "LEFT": 2,
            "RIGHT": 3
        }

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Sterowanie Goniometrem")

        layout = QVBoxLayout()

        self.graph_x = pg.PlotWidget(title="Pozycja X")
        self.curve_x = self.graph_x.plot()
        layout.addWidget(self.graph_x)

        self.graph_y = pg.PlotWidget(title="Pozycja Y")
        self.curve_y = self.graph_y.plot()
        layout.addWidget(self.graph_y)

        self.reset_button = QPushButton("Resetuj wykres")
        self.reset_button.clicked.connect(self.reset_plot)
        layout.addWidget(self.reset_button)

        self.mode_group = QButtonGroup(self)
        self.angle_mode = QRadioButton("Sterowanie kątem")
        self.dir_mode = QRadioButton("Sterowanie kierunkowe")
        self.angle_mode.setChecked(True)
        self.mode_group.addButton(self.angle_mode)
        self.mode_group.addButton(self.dir_mode)
        self.dir_mode.toggled.connect(self.update_nav_buttons_state)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.angle_mode)
        mode_layout.addWidget(self.dir_mode)
        layout.addLayout(mode_layout)

        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        send_button = QPushButton("Wyślij kąty")
        send_button.clicked.connect(self.send_angles)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("X:"))
        input_layout.addWidget(self.x_input)
        input_layout.addWidget(QLabel("Y:"))
        input_layout.addWidget(self.y_input)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)

        self.up_btn = QPushButton("Góra")
        self.down_btn = QPushButton("Dół")
        self.left_btn = QPushButton("Lewo")
        self.right_btn = QPushButton("Prawo")

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.left_btn)
        nav_layout.addWidget(self.right_btn)
        nav_layout.addWidget(self.up_btn)
        nav_layout.addWidget(self.down_btn)
        layout.addLayout(nav_layout)

        self.setLayout(layout)

        self.setup_navigation_buttons()
        self.update_nav_buttons_state()

    def setup_navigation_buttons(self):
        def make_move_handler(direction):
            direction_code = self.direction_map[direction]
            return lambda: self.client.send(
                CommandBuilder.build_manual_command(direction_code)) if self.dir_mode.isChecked() else None

        def stop_move():
            if self.dir_mode.isChecked():
                self.client.send(CommandBuilder.build_stop_command())

        for btn, cmd in zip(
                [self.up_btn, self.down_btn, self.left_btn, self.right_btn],
                ["UP", "DOWN", "LEFT", "RIGHT"]
        ):
            btn.pressed.connect(make_move_handler(cmd))
            btn.released.connect(stop_move)

    def update_nav_buttons_state(self):
        enabled = self.dir_mode.isChecked()
        for btn in [self.up_btn, self.down_btn, self.left_btn, self.right_btn]:
            btn.setEnabled(enabled)

    def handle_data(self, data):
        try:
            x_str, y_str = data.strip().split(',')
            self.x_data.append(float(x_str))
            self.y_data.append(float(y_str))
        except ValueError:
            pass

    def update_plot(self):
        self.curve_x.setData(self.x_data)
        self.curve_y.setData(self.y_data)

    def reset_plot(self):
        self.x_data.clear()
        self.y_data.clear()

    def send_angles(self):
        if self.angle_mode.isChecked():
            try:
                x = float(self.x_input.text())
                y = float(self.y_input.text())
                cmd = CommandBuilder.build_goto_command(x, y)
                self.client.send(cmd)
            except ValueError:
                pass

    def closeEvent(self, event):
        self.client.stop()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GoniometerControl()
    window.show()
    sys.exit(app.exec())
