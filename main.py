import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QStackedWidget
from control_panel import ControlPanel
from settings_panel import SettingsPanel


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Goniometr - GUI")

        self.stack = QStackedWidget()
        self.control_panel = ControlPanel()
        self.settings_panel = SettingsPanel()

        self.stack.addWidget(self.control_panel)
        self.stack.addWidget(self.settings_panel)

        self.control_btn = QPushButton("Sterowanie")
        self.settings_btn = QPushButton("Ustawienia")

        self.control_btn.setCheckable(True)
        self.settings_btn.setCheckable(True)
        self.control_btn.setChecked(True)

        self.control_btn.clicked.connect(self.show_control_panel)
        self.settings_btn.clicked.connect(self.show_settings_panel)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.control_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.stack)

        self.setLayout(main_layout)

    def show_control_panel(self):
        self.stack.setCurrentWidget(self.control_panel)
        self.control_btn.setChecked(True)
        self.settings_btn.setChecked(False)

    def show_settings_panel(self):
        self.stack.setCurrentWidget(self.settings_panel)
        self.settings_btn.setChecked(True)
        self.control_btn.setChecked(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
