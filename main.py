import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QStackedWidget
from control_panel import ControlPanel
from settings_panel import SettingsPanel

"""

Okrągły joystick, przełączalne tryby sterowania (znikanie tych nie używanych)
Graficzne ułożenie
Wielomiany
zapis do csvki
punkt zadany na wykresie dobrze by było też trajektorie
informacja o zakończonym ruchu (pop up) 
******* presety do PIDa i innych takich (DŻEJSON NAJLEPIEJ) ********
Model musi być dokładny i obszerny (wykresy o trajektorii, GOTO itd.)
Opis ramek danych do raportu

"""


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Goniometr - GUI")
        self.resize(900, 600)

        self.stack = QStackedWidget()
        self.control_panel = ControlPanel()
        self.settings_panel = SettingsPanel()

        self.stack.addWidget(self.control_panel)
        self.stack.addWidget(self.settings_panel)

        self.control_btn = QPushButton("Sterowanie")
        self.settings_btn = QPushButton("Ustawienia")

        self.control_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.control_panel))
        self.settings_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_panel))

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.control_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.stack)

        self.setLayout(main_layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
