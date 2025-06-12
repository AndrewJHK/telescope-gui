from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QMessageBox, QFileDialog, QScrollArea
)
import os
import json
from processing import CommandBuilder, tcp_client


class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.client = tcp_client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Przyciski do góry
        btn_layout = QHBoxLayout()

        self.send_btn = QPushButton("Wyślij konfigurację")
        self.send_btn.clicked.connect(self.send_config)
        btn_layout.addWidget(self.send_btn)

        self.save_btn = QPushButton("Zapisz do JSON")
        self.save_btn.clicked.connect(self.save_to_json)
        btn_layout.addWidget(self.save_btn)

        self.load_btn = QPushButton("Wczytaj z JSON")
        self.load_btn.clicked.connect(self.load_from_json)
        btn_layout.addWidget(self.load_btn)

        layout.addLayout(btn_layout)

        # Presety z folderu ./presets
        self.preset_container = QVBoxLayout()
        layout.addWidget(QLabel("Dostępne presety:"))
        self.load_presets()
        layout.addLayout(self.preset_container)

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

        layout.addWidget(QLabel("Prędkość maksymalna [°/s]"))
        self.max_speed_x = QLineEdit()
        self.max_speed_y = QLineEdit()
        max_speed_layout = QHBoxLayout()
        max_speed_layout.addWidget(QLabel("X:"))
        max_speed_layout.addWidget(self.max_speed_x)
        max_speed_layout.addWidget(QLabel("Y:"))
        max_speed_layout.addWidget(self.max_speed_y)
        layout.addLayout(max_speed_layout)

        layout.addWidget(QLabel("Dokładność (tolerancja pozycji) [°]"))
        self.tolerance_x = QLineEdit()
        self.tolerance_y = QLineEdit()
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("X:"))
        tolerance_layout.addWidget(self.tolerance_x)
        tolerance_layout.addWidget(QLabel("Y:"))
        tolerance_layout.addWidget(self.tolerance_y)
        layout.addLayout(tolerance_layout)

        self.setLayout(layout)

    def load_presets(self):
        self.clear_layout(self.preset_container)
        presets_dir = "presets"
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
        for fname in os.listdir(presets_dir):
            if fname.endswith(".json"):
                btn = QPushButton(fname)
                btn.clicked.connect(lambda _, f=fname: self.load_preset_file(os.path.join(presets_dir, f)))
                self.preset_container.addWidget(btn)

    def load_preset_file(self, filepath):
        try:
            with open(filepath, "r") as f:
                config = json.load(f)
                self.p_x.setText(config.get("p_x", ""))
                self.i_x.setText(config.get("i_x", ""))
                self.d_x.setText(config.get("d_x", ""))
                self.p_y.setText(config.get("p_y", ""))
                self.i_y.setText(config.get("i_y", ""))
                self.d_y.setText(config.get("d_y", ""))
                self.max_speed_x.setText(config.get("max_speed_x", ""))
                self.max_speed_y.setText(config.get("max_speed_y", ""))
                self.tolerance_x.setText(config.get("tolerance_x", ""))
                self.tolerance_y.setText(config.get("tolerance_y", ""))
            QMessageBox.information(self, "Preset wczytany", f"Wczytano preset z {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać presetu: {e}")

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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

    def save_to_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Zapisz konfigurację", "config.json", "JSON Files (*.json)")
        if not file_path:
            return
        config = {
            "p_x": self.p_x.text(), "i_x": self.i_x.text(), "d_x": self.d_x.text(),
            "p_y": self.p_y.text(), "i_y": self.i_y.text(), "d_y": self.d_y.text(),
            "max_speed_x": self.max_speed_x.text(), "max_speed_y": self.max_speed_y.text(),
            "tolerance_x": self.tolerance_x.text(), "tolerance_y": self.tolerance_y.text()
        }
        try:
            with open(file_path, "w") as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self, "Sukces", f"Zapisano konfigurację do {file_path}")
            self.load_presets()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać: {e}")

    def load_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Wczytaj konfigurację", "", "JSON Files (*.json)")
        if not file_path:
            return
        self.load_preset_file(file_path)
