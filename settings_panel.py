from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QMessageBox
)
from processing import CommandBuilder, tcp_client


class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.client = tcp_client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # PID dla osi X
        layout.addWidget(QLabel("PID - Oś X"))
        self.p_x = QLineEdit()
        self.i_x = QLineEdit()
        self.d_x = QLineEdit()
        pid_x_layout = QHBoxLayout()
        pid_x_layout.addWidget(QLabel("P:"))
        pid_x_layout.addWidget(self.p_x)
        pid_x_layout.addWidget(QLabel("I:"))
        pid_x_layout.addWidget(self.i_x)
        pid_x_layout.addWidget(QLabel("D:"))
        pid_x_layout.addWidget(self.d_x)
        layout.addLayout(pid_x_layout)

        # PID dla osi Y
        layout.addWidget(QLabel("PID - Oś Y"))
        self.p_y = QLineEdit()
        self.i_y = QLineEdit()
        self.d_y = QLineEdit()
        pid_y_layout = QHBoxLayout()
        pid_y_layout.addWidget(QLabel("P:"))
        pid_y_layout.addWidget(self.p_y)
        pid_y_layout.addWidget(QLabel("I:"))
        pid_y_layout.addWidget(self.i_y)
        pid_y_layout.addWidget(QLabel("D:"))
        pid_y_layout.addWidget(self.d_y)
        layout.addLayout(pid_y_layout)

        # Prędkość maksymalna
        layout.addWidget(QLabel("Prędkość maksymalna [°/s]"))
        self.max_speed_x = QLineEdit()
        self.max_speed_y = QLineEdit()
        max_speed_layout = QHBoxLayout()
        max_speed_layout.addWidget(QLabel("X:"))
        max_speed_layout.addWidget(self.max_speed_x)
        max_speed_layout.addWidget(QLabel("Y:"))
        max_speed_layout.addWidget(self.max_speed_y)
        layout.addLayout(max_speed_layout)

        # Dokładność (tolerancja)
        layout.addWidget(QLabel("Dokładność (tolerancja pozycji) [°]"))
        self.tolerance_x = QLineEdit()
        self.tolerance_y = QLineEdit()
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("X:"))
        tolerance_layout.addWidget(self.tolerance_x)
        tolerance_layout.addWidget(QLabel("Y:"))
        tolerance_layout.addWidget(self.tolerance_y)
        layout.addLayout(tolerance_layout)

        # Przycisk wyślij
        self.send_btn = QPushButton("Wyślij konfigurację")
        self.send_btn.clicked.connect(self.send_config)
        layout.addWidget(self.send_btn)

        self.setLayout(layout)

    def send_config(self):
        try:
            values = [
                float(self.p_x.text()), float(self.i_x.text()), float(self.d_x.text()),
                float(self.p_y.text()), float(self.i_y.text()), float(self.d_y.text()),
                float(self.max_speed_x.text()), float(self.max_speed_y.text()),
                float(self.tolerance_x.text()), float(self.tolerance_y.text())
            ]
            packet = CommandBuilder.build_config_packet(*values)
            self.client.send(packet)
            QMessageBox.information(self, "Sukces", "Konfiguracja została wysłana")
        except ValueError:
            QMessageBox.critical(self, "Błąd", "Wprowadź poprawne wartości liczbowe")
