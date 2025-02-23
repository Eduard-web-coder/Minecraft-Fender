from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QCheckBox, QListWidget, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
import sys
import socket
import threading
import os
from mcstatus import JavaServer

class MinecraftServerFinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Server Finder")
        self.setGeometry(100, 100, 600, 600)
        self.setWindowIcon(QIcon('f44bc6a9bb0214239dba6cb2fa2c4db7.png'))
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.stop_scanning)

    def init_ui(self):
        layout = QVBoxLayout()

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
                color: #333;
                font-family: 'Segoe UI';
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #005f73;
                margin-bottom: 10px;
            }
            QLineEdit, QComboBox, QListWidget {
                background: #ffffff;
                border: 1px solid #007f6d;
                border-radius: 8px;
                padding: 10px;
                color: #333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007f6d;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005f73;
            }
            QCheckBox {
                padding: 5px;
                color: #333;
            }
            QWidget > QVBoxLayout > QLabel:first-child {
                margin-top: 20px;
            }
            QVBoxLayout > QLabel, QVBoxLayout > QLineEdit, QVBoxLayout > QCheckBox, QVBoxLayout > QPushButton, QVBoxLayout > QListWidget {
                margin-bottom: 15px;
            }
        """)

        self.label = QLabel("Поиск серверов Minecraft...")
        layout.addWidget(self.label)

        self.port_label = QLabel("Введите порт сервера (по умолчанию 25565):")
        layout.addWidget(self.port_label)

        self.port_entry = QLineEdit("25565")
        layout.addWidget(self.port_entry)

        self.use_ip_file_checkbutton = QCheckBox("Использовать IP-адреса из IP.ini")
        layout.addWidget(self.use_ip_file_checkbutton)

        self.internet_scan_checkbutton = QCheckBox("Сканировать интернет")
        self.internet_scan_checkbutton.stateChanged.connect(self.toggle_ip_range_entries)
        layout.addWidget(self.internet_scan_checkbutton)

        self.ip_range_label = QLabel("Введите диапазон IP-адресов (например, 192.168.1.1-192.168.1.255):")
        layout.addWidget(self.ip_range_label)

        self.ip_range_entry = QLineEdit()
        layout.addWidget(self.ip_range_entry)

        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.search_servers)
        layout.addWidget(self.search_button)

        # Кнопка для получения IP
        self.ip_button = QPushButton("Узнать свой IP в подробностях скнирование 5 сек")
        self.ip_button.clicked.connect(self.show_ip_dialog)
        layout.addWidget(self.ip_button)

        self.server_listbox = QListWidget()
        layout.addWidget(self.server_listbox)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def show_ip_dialog(self):
        # Создание .bat файла
        bat_content = '''@echo on
color 02
cls
ipconfig /renew
cls
cls
ipconfig /all
pause
'''
        bat_file = 'get_ip.bat'
        with open(bat_file, 'w') as file:
            file.write(bat_content)

        # Выполнение .bat файла
        os.system(f'start {bat_file}')

    def toggle_ip_range_entries(self):
        state = self.internet_scan_checkbutton.isChecked()
        self.ip_range_label.setEnabled(state)
        self.ip_range_entry.setEnabled(state)

    def search_servers(self):
        self.server_listbox.clear()
        self.label.setText("Поиск...")
        self.port = self.port_entry.text()
        self.servers_found = []
        self.timer.start(5000)  # Установка таймера на 5 секунд

        if self.use_ip_file_checkbutton.isChecked():
            self.scan_ip_file()
        elif self.internet_scan_checkbutton.isChecked():
            self.scan_internet_range()
        else:
            self.local_ip = self.get_local_ip()
            self.base_ip = ".".join(self.local_ip.split(".")[:-1]) + "."
            self.scan_network()

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def scan_network(self):
        threads = []
        for i in range(1, 255):
            ip = self.base_ip + str(i)
            thread = threading.Thread(target=self.ping_server, args=(ip,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        self.display_results()

    def scan_ip_file(self):
        if os.path.exists("IP.ini"):
            with open("IP.ini", "r") as file:
                ips = [ip.strip() for ip in file.readlines() if ip.strip()]
            threads = []
            for ip in ips:
                thread = threading.Thread(target=self.ping_server, args=(ip,))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
            self.display_results()
        else:
            QMessageBox.critical(self, "Ошибка", "Файл IP.ini не найден.")

    def scan_internet_range(self):
        ip_range = self.ip_range_entry.text()
        if '-' in ip_range:
            ips = self.generate_ip_range(ip_range)
            threads = []
            for ip in ips:
                thread = threading.Thread(target=self.ping_server, args=(ip,))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
            self.display_results()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный формат диапазона IP-адресов. Используйте формат: start_ip-end_ip")

    def generate_ip_range(self, ip_range):
        start_ip, end_ip = ip_range.split('-')
        start_ip_parts = list(map(int, start_ip.split('.')))
        end_ip_parts = list(map(int, end_ip.split('.')))
        ips = []
        current_ip_parts = start_ip_parts
        while current_ip_parts != end_ip_parts:
            ips.append('.'.join(map(str, current_ip_parts)))
            for i in range(3, -1, -1):
                current_ip_parts[i] += 1
                if current_ip_parts[i] < 256:
                    break
                else:
                    current_ip_parts[i] = 0
        ips.append('.'.join(map(str, end_ip_parts)))
        return ips

    def ping_server(self, ip):
        try:
            server = JavaServer.lookup(f"{ip}:{self.port}")
            status = server.status()
            server_info = f"IP: {ip}, Игроки: {status.players.online}/{status.players.max}, Версия: {status.version.name}"
            self.servers_found.append(server_info)
            players = [player.name for player in status.players.sample] if status.players.sample else []
            self.write_to_file(ip, players)
        except Exception as e:
            print(f"Не удалось подключиться к {ip}:{self.port}: {e}")

    def write_to_file(self, ip, players):
        filename = "server_players.txt"
        with open(filename, "a") as file:
            file.write(f"IP сервера: {ip}:{self.port}\n")
            file.write("Игроки:\n")
            for player in players:
                file.write(f" - {player}\n")
            file.write("\n")

    def display_results(self):
        self.label.setText("Поиск завершен. Найденные серверы:")
        if not self.servers_found:
            self.server_listbox.addItem("Серверы не найдены.")
        else:
            for server in self.servers_found:
                self.server_listbox.addItem(server)

    def stop_scanning(self):
        self.label.setText("Поиск остановлен.")
        self.timer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinecraftServerFinder()
    window.show()
    sys.exit(app.exec_())