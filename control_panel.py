import struct
import csv
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QHBoxLayout,
    QRadioButton, QButtonGroup, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGridLayout, QStackedLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg
from math import sqrt
from processing import CommandBuilder, tcp_client


class JoystickWidget(QGraphicsView):
    def __init__(self, on_move_callback):
        super().__init__()
        self.setFixedSize(300, 300)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.on_move = on_move_callback

        self.bounds = 250
        self.radius = 15
        self.center = self.width() / 2

        self.scene.addEllipse(
            self.center - self.bounds / 2,
            self.center - self.bounds / 2,
            self.bounds,
            self.bounds
        )

        self.joystick = QGraphicsEllipseItem(0, 0, self.radius * 2, self.radius * 2)
        self.joystick.setBrush(Qt.GlobalColor.blue)
        self.scene.addItem(self.joystick)

        self.setMouseTracking(True)
        self.mouse_pressed = False
        self.reset_position()

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
        dist = sqrt(dx ** 2 + dy ** 2)
        if dist > max_dist:
            scale = max_dist / dist
            dx *= scale
            dy *= scale

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
        self.x_setpoint = []
        self.y_setpoint = []

        self.direction_map = {"UP": 0, "DOWN": 1, "LEFT": 2, "RIGHT": 3}

        self.init_ui()

        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)

    def init_ui(self):
        layout = QVBoxLayout()

        self.graph_x = pg.PlotWidget(title="Pozycja X")
        self.curve_x = self.graph_x.plot(pen='b')
        self.curve_x_setpoint = self.graph_x.plot(pen='r', symbol='x')
        layout.addWidget(self.graph_x, stretch=2)

        self.graph_y = pg.PlotWidget(title="Pozycja Y")
        self.curve_y = self.graph_y.plot(pen='b')
        self.curve_y_setpoint = self.graph_y.plot(pen='r', symbol='x')
        layout.addWidget(self.graph_y, stretch=2)

        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.left_btn = QPushButton("←")
        self.right_btn = QPushButton("→")

        for btn in [self.up_btn, self.down_btn, self.left_btn, self.right_btn]:
            btn.setFixedSize(80, 80)

        nav_grid = QGridLayout()
        nav_grid.addWidget(self.up_btn, 0, 1)
        nav_grid.addWidget(self.left_btn, 1, 0)
        nav_grid.addWidget(self.right_btn, 1, 2)
        nav_grid.addWidget(self.down_btn, 2, 1)

        self.nav_widget = QWidget()
        self.nav_widget.setLayout(nav_grid)

        joystick_and_buttons = QWidget()
        joystick_layout = QHBoxLayout()
        self.joystick = JoystickWidget(self.handle_joystick_move)
        joystick_layout.addWidget(self.joystick)
        joystick_layout.addWidget(self.nav_widget)
        joystick_and_buttons.setLayout(joystick_layout)

        self.placeholder_widget = QWidget()
        self.placeholder_widget.setFixedSize(300, 300)

        # trajektoria widget
        self.coeff_inputs_x = [QLineEdit() for _ in range(5)]
        self.coeff_inputs_y = [QLineEdit() for _ in range(5)]
        self.send_traj_button = QPushButton("Zadaj trajektorię")
        self.send_traj_button.clicked.connect(self.send_trajectory)

        traj_layout = QVBoxLayout()
        traj_layout.addWidget(QLabel("X(t) = a₀ + a₁·t + a₂·t² + a₃·t³ + a₄·t⁴"))
        traj_x = QVBoxLayout()
        labels_x = QHBoxLayout()
        inputs_x = QHBoxLayout()
        for i, edit in enumerate(self.coeff_inputs_x):
            labels_x.addWidget(QLabel(f"a{i}"))
            inputs_x.addWidget(edit)
        traj_x.addLayout(labels_x)
        traj_x.addLayout(inputs_x)
        traj_layout.addLayout(traj_x)

        traj_layout.addWidget(QLabel("Y(t) = b₀ + b₁·t + b₂·t² + b₃·t³ + b₄·t⁴"))
        traj_y = QVBoxLayout()
        labels_y = QHBoxLayout()
        inputs_y = QHBoxLayout()
        for i, edit in enumerate(self.coeff_inputs_y):
            labels_y.addWidget(QLabel(f"b{i}"))
            inputs_y.addWidget(edit)
        traj_y.addLayout(labels_y)
        traj_y.addLayout(inputs_y)
        traj_layout.addLayout(traj_y)

        traj_layout.addWidget(self.send_traj_button)

        self.traj_widget = QWidget()
        self.traj_widget.setLayout(traj_layout)

        self.left_stack = QStackedLayout()
        self.left_stack.addWidget(joystick_and_buttons)
        self.left_stack.addWidget(self.placeholder_widget)
        self.left_stack.addWidget(self.traj_widget)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_stack)

        control_box = QVBoxLayout()

        self.reset_button = QPushButton("Resetuj wykres")
        self.reset_button.clicked.connect(self.reset_plot)
        control_box.addWidget(self.reset_button)

        self.home_button = QPushButton("Powrót do pozycji początkowej")
        self.home_button.clicked.connect(self.go_home_position)
        control_box.addWidget(self.home_button)

        self.save_button = QPushButton("Zapisz dane do CSV")
        self.save_button.clicked.connect(self.save_to_csv)
        control_box.addWidget(self.save_button)

        self.mode_group = QButtonGroup(self)
        self.angle_mode = QRadioButton("Sterowanie GOTO")
        self.dir_mode = QRadioButton("Sterowanie kierunkowe")
        self.traj_mode = QRadioButton("Sterowanie trajektorią")
        self.angle_mode.setChecked(True)
        for btn in [self.angle_mode, self.dir_mode, self.traj_mode]:
            self.mode_group.addButton(btn)
            control_box.addWidget(btn)
            btn.toggled.connect(self.update_nav_buttons_state)

        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        self.send_button = QPushButton("Zadaj punkt")
        self.send_button.clicked.connect(self.send_angles)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("X:"))
        input_layout.addWidget(self.x_input)
        input_layout.addWidget(QLabel("Y:"))
        input_layout.addWidget(self.y_input)
        input_layout.addWidget(self.send_button)

        self.goto_inputs_widget = QWidget()
        self.goto_inputs_widget.setLayout(input_layout)
        control_box.addWidget(self.goto_inputs_widget)

        control_box.addStretch()

        control_container = QWidget()
        control_container.setLayout(control_box)
        control_container.setMinimumWidth(960)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.left_widget)
        bottom_layout.addWidget(control_container)

        layout.addLayout(bottom_layout)
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
        is_dir = self.dir_mode.isChecked()
        is_goto = self.angle_mode.isChecked()
        is_traj = self.traj_mode.isChecked()

        if is_dir:
            self.left_stack.setCurrentIndex(0)
        elif is_goto:
            self.left_stack.setCurrentIndex(1)
        else:
            self.left_stack.setCurrentIndex(2)

        for btn in [self.up_btn, self.down_btn, self.left_btn, self.right_btn]:
            btn.setEnabled(is_dir)
        self.send_button.setEnabled(is_goto)
        self.goto_inputs_widget.setVisible(is_goto)
        self.send_traj_button.setEnabled(is_traj)

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
        self.curve_x_setpoint.setData(self.x_setpoint)
        self.curve_y_setpoint.setData(self.y_setpoint)

    def reset_plot(self):
        self.x_data.clear()
        self.y_data.clear()
        self.x_setpoint.clear()
        self.y_setpoint.clear()

    def send_angles(self):
        if self.angle_mode.isChecked():
            try:
                x = float(self.x_input.text())
                y = float(self.y_input.text())
                cmd = CommandBuilder.build_goto_command(x, y)
                self.client.send(cmd)
                self.x_setpoint.append(x)
                self.y_setpoint.append(y)
            except ValueError:
                pass

    def go_home_position(self):
        cmd = CommandBuilder.build_goto_command(0.0, 0.0)
        self.client.send(cmd)

    def save_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Zapisz dane do CSV", "dane.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["czas (s)", "index", "x", "y"])
                start_time = time.time()
                for i, (x, y) in enumerate(zip(self.x_data, self.y_data)):
                    t = round(time.time() - start_time, 3)
                    writer.writerow([t, i, x, y])
            print(f"Dane zapisane do {file_path}")
        except Exception as e:
            print(f"Błąd zapisu CSV: {e}")

    def send_trajectory(self):
        try:
            coeffs_x = [float(e.text()) for e in self.coeff_inputs_x]
            coeffs_y = [float(e.text()) for e in self.coeff_inputs_y]
            cmd = CommandBuilder.build_trajectory_command(coeffs_x, coeffs_y)
            self.client.send(cmd)
            x_final = sum(c * (1.0 ** i) for i, c in enumerate(coeffs_x))
            y_final = sum(c * (1.0 ** i) for i, c in enumerate(coeffs_y))
            self.x_setpoint.append(x_final)
            self.y_setpoint.append(y_final)
            print("Trajektoria wysłana")
        except ValueError:
            print("Błędne współczynniki!")

    def handle_joystick_move(self, norm_x, norm_y):
        if self.dir_mode.isChecked():
            pass

    def closeEvent(self, event):
        self.client.stop()
        super().closeEvent(event)
