import struct
import socket
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class CommandBuilder:
    @staticmethod
    def build_goto_command(x: float, y: float) -> bytes:
        return struct.pack('Bff', 2, x, y)

    @staticmethod
    def build_manual_command(direction_code: int) -> bytes:
        return struct.pack('Bi', 3, direction_code)

    @staticmethod
    def build_analog_manual_command(x: float, y: float) -> bytes:
        return struct.pack('Bff', 4, x, y)

    @staticmethod
    def build_stop_command() -> bytes:
        return struct.pack('B', 1)

    @staticmethod
    def build_config_packet(px, ix, dx, py, iy, dy, max_x, max_y, tol_x, tol_y) -> bytes:
        return struct.pack('B10f', 6, px, ix, dx, py, iy, dy, max_x, max_y, tol_x, tol_y)

    @staticmethod
    def build_trajectory_command(coeffs_x, coeffs_y):
        if len(coeffs_x) != 5 or len(coeffs_y) != 5:
            raise ValueError("Wymagane dokładnie 5 współczynników dla każdej osi")

        return struct.pack('B10f', 5, *(coeffs_x + coeffs_y))


class TCPClient(QObject):
    data_received = pyqtSignal(bytes)

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
        buffer = b""
        try:
            while self.running:
                data = self.socket.recv(1024)
                if data:
                    buffer += data
                    while len(buffer) >= 8:
                        chunk = buffer[:8]
                        buffer = buffer[8:]
                        self.data_received.emit(chunk)
        finally:
            self.socket.close()

    def send(self, message: bytes):
        if self.socket:
            self.socket.sendall(message)

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()


tcp_client = TCPClient("127.0.0.1", 2137)
tcp_client.start()
