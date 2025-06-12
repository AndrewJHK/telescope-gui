import struct
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QHBoxLayout,
    QRadioButton, QButtonGroup, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg
from processing import CommandBuilder, tcp_client


class JoystickWidget(QGraphicsView):
    def __init__(self, on_move_callback):
        super().__init__()
        self.setFixedSize(150, 150)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.on_move = on_move_callback

        self.bounds = 100
        self.radius = 10
        self.joystick = QGraphicsEllipseItem(0, 0, self.radius * 2, self.radius * 2)
        self.joystick.setBrush(Qt.GlobalColor.blue)
        self.scene.addEllipse(0, 0, self.bounds, self.bounds)
        self.scene.addItem(self.joystick)
        self.setMouseTracking(True)
        self.center = self.bounds / 2
        self.reset_position()
        self.mouse_pressed = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = True

    def mouseMoveEvent(self, event):
        if not self.mouse_pressed:
            return
        pos = self.mapToScene(event.pos())
        dx = pos.x() - self.center
        dy = pos.y() - self.center
        max_dist = self.bounds / 2 - self.radius
        dx = max(-max_dist, min(max_dist, dx))
        dy = max(-max_dist, min(max_dist, dy))
        self.joystick.setPos(self.center + dx - self.radius, self.center + dy - self.radius)
        self.on_move(dx / max_dist, dy / max_dist)

    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False
        self.reset_position()
        self.on_move(0, 0)

    def reset_position(self):
        self.joystick.setPos(self.center - self.radius, self.center - self.radius)


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.client = tcp_client
        self.client.data_received.connect(self.handle_data)

        self.x_data = []
        self.y_data = []

        self.direction_map = {"UP": 0, "DOWN": 1, "LEFT": 2, "RIGHT": 3}

        self.init_ui()

        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)

    def init_ui(self):
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

        self.home_button = QPushButton("Pozycja początkowa")
        self.home_button.clicked.connect(self.go_home_position)
        layout.addWidget(self.home_button)

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
        self.send_button = QPushButton("Wyślij kąty")
        self.send_button.clicked.connect(self.send_angles)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("X:"))
        input_layout.addWidget(self.x_input)
        input_layout.addWidget(QLabel("Y:"))
        input_layout.addWidget(self.y_input)
        input_layout.addWidget(self.send_button)
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

        self.joystick = JoystickWidget(self.handle_joystick_move)
        layout.addWidget(QLabel("Joystick sterowania"))
        layout.addWidget(self.joystick)

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
                ["UP", "DOWN", "LEFT", "RIGHT"]):
            btn.pressed.connect(make_move_handler(cmd))
            btn.released.connect(stop_move)

    def update_nav_buttons_state(self):
        enabled = self.dir_mode.isChecked()
        for btn in [self.up_btn, self.down_btn, self.left_btn, self.right_btn]:
            btn.setEnabled(enabled)
        self.send_button.setEnabled(not enabled)

    def handle_data(self, data: bytes):
        try:
            x, y = struct.unpack('II', data)
            self.x_data.append(x)
            self.y_data.append(y)
        except struct.error:
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

    def go_home_position(self):
        cmd = CommandBuilder.build_goto_command(0.0, 0.0)
        self.client.send(cmd)

    def handle_joystick_move(self, norm_x, norm_y):
        if self.dir_mode.isChecked():
            pass

    def closeEvent(self, event):
        self.client.stop()
        super().closeEvent(event)
