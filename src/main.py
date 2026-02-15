import sys
import sqlite3
import hashlib
import os
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QStackedWidget,
    QListWidget, QDialog, QDialogButtonBox, QFormLayout, QListWidgetItem,
    QInputDialog
)
from PyQt6.QtCore import Qt


def init_db():
    conn = sqlite3.connect("computers.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS computers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            ip TEXT NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def is_valid_ip(ip):
    pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    if re.match(pattern, ip):
        return all(0 <= int(part) <= 255 for part in re.findall(r"\d+", ip))
    return False


class ComputerWindow(QWidget):
    def __init__(self, room_id, room_name):
        super().__init__()
        self.room_id = room_id
        self.room_name = room_name
        self.setWindowTitle(f"Кабинет: {room_name}")
        self.resize(400, 300)

        layout = QVBoxLayout()

        title = QLabel(f"Компьютеры в кабинете «{room_name}»")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.computer_list = QListWidget()
        layout.addWidget(self.computer_list)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить компьютер")
        self.add_btn.clicked.connect(self.add_computer)
        self.back_btn = QPushButton("⬅ Назад")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.back_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_computers()

    def load_computers(self):
        self.computer_list.clear()
        conn = sqlite3.connect("computers.db")
        cur = conn.cursor()
        cur.execute("SELECT id, name, ip FROM computers WHERE room_id = ?", (self.room_id,))
        for comp_id, name, ip in cur.fetchall():
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            label = QLabel(f"{name} ({ip})")
            on_btn = QPushButton("Вкл")
            off_btn = QPushButton("Выкл")

            on_btn.clicked.connect(lambda _, ip=ip: self.send_power_command(ip, True))
            off_btn.clicked.connect(lambda _, ip=ip: self.send_power_command(ip, False))

            item_layout.addWidget(label)
            item_layout.addWidget(on_btn)
            item_layout.addWidget(off_btn)
            item_widget.setLayout(item_layout)

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.computer_list.addItem(item)
            self.computer_list.setItemWidget(item, item_widget)

            item.setData(Qt.ItemDataRole.UserRole, comp_id)

        conn.close()

    def add_computer(self):
        dialog = ComputerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, ip = dialog.get_data()
            conn = sqlite3.connect("computers.db")
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO computers (room_id, name, ip) VALUES (?, ?, ?)",
                    (self.room_id, name, ip)
                )
                conn.commit()
                self.load_computers()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Ошибка", "Компьютер с таким IP уже существует в этом кабинете!")
            finally:
                conn.close()

    def send_power_command(self, ip, turn_on):
        action = "включение" if turn_on else "выключение"
        print(f"[ЗАГЛУШКА] Отправка команды: {action} компьютера {ip}")
        QMessageBox.information(self, "Команда отправлена", f"Команда '{action}' отправлена на {ip}")


class ComputerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить компьютер")
        self.setFixedSize(300, 150)

        self.name_edit = QLineEdit()
        self.ip_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("Название:", self.name_edit)
        form.addRow("IP-адрес:", self.ip_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def accept(self):
        name = self.name_edit.text().strip()
        ip = self.ip_edit.text().strip()
        if not name or not ip:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        if not is_valid_ip(ip):
            QMessageBox.warning(self, "Ошибка", "Некорректный IP-адрес!")
            return
        super().accept()

    def get_data(self):
        return self.name_edit.text().strip(), self.ip_edit.text().strip()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление кабинетами")
        self.resize(400, 350)

        layout = QVBoxLayout()

        title = QLabel("Список кабинетов")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.room_list = QListWidget()
        self.room_list.itemClicked.connect(self.open_room)
        layout.addWidget(self.room_list)

        btn_layout = QHBoxLayout()
        self.add_room_btn = QPushButton("➕ Добавить кабинет")
        self.add_room_btn.clicked.connect(self.add_room)
        btn_layout.addWidget(self.add_room_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_rooms()

    def load_rooms(self):
        self.room_list.clear()
        conn = sqlite3.connect("computers.db")
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM rooms")
        for room_id, name in cur.fetchall():
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, room_id)
            self.room_list.addItem(item)
        conn.close()

    def add_room(self):
        name, ok = QInputDialog.getText(self, "Новый кабинет", "Название кабинета:")
        if ok and name.strip():
            name = name.strip()
            conn = sqlite3.connect("computers.db")
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO rooms (name) VALUES (?)", (name,))
                conn.commit()
                self.load_rooms()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Ошибка", "Кабинет с таким названием уже существует!")
            finally:
                conn.close()

    def open_room(self, item):
        room_id = item.data(Qt.ItemDataRole.UserRole)
        room_name = item.text()
        self.room_window = ComputerWindow(room_id, room_name)
        self.room_window.show()


class AuthApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.db_path = "users.db"
        self.init_user_db()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(320, 220)

        self.login_widget = self.create_login_form()
        self.register_widget = self.create_register_form()

        self.addWidget(self.login_widget)
        self.addWidget(self.register_widget)

    def init_user_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt BLOB NOT NULL,
                password_hash BLOB NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def create_login_form(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.login_username = QLineEdit()
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_username)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.login_password)

        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)

        switch_btn = QPushButton("Нет аккаунта? Зарегистрироваться")
        switch_btn.clicked.connect(lambda: self.setCurrentIndex(1))
        layout.addWidget(switch_btn)

        widget.setLayout(layout)
        return widget

    def create_register_form(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.reg_username = QLineEdit()
        self.reg_password = QLineEdit()
        self.reg_password_repeat = QLineEdit()

        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password_repeat.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.reg_username)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.reg_password)
        layout.addWidget(QLabel("Повторите пароль:"))
        layout.addWidget(self.reg_password_repeat)

        register_btn = QPushButton("Зарегистрироваться")
        register_btn.clicked.connect(self.register)
        layout.addWidget(register_btn)

        back_btn = QPushButton("Уже есть аккаунт? Войти")
        back_btn.clicked.connect(lambda: self.setCurrentIndex(0))
        layout.addWidget(back_btn)

        widget.setLayout(layout)
        return widget

    def hash_password(self, password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        if salt is None:
            salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return salt, pwd_hash

    def verify_password(self, stored_salt: bytes, stored_hash: bytes, password: str) -> bool:
        _, new_hash = self.hash_password(password, stored_salt)
        return new_hash == stored_hash

    def login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT salt, password_hash FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            salt, stored_hash = result
            if self.verify_password(salt, stored_hash, password):
                self.main_window = MainWindow()
                self.main_window.show()
                self.hide()
                return

        QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль!")

    def register(self):
        username = self.reg_username.text().strip()
        password = self.reg_password.text()
        password_repeat = self.reg_password_repeat.text()

        if not username or not password or not password_repeat:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        if password != password_repeat:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов!")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Ошибка", "Пользователь уже существует!")
                return

            salt, pwd_hash = self.hash_password(password)
            cursor.execute("INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                           (username, salt, pwd_hash))
            conn.commit()
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
            self.setCurrentIndex(0)
            self.reg_username.clear()
            self.reg_password.clear()
            self.reg_password_repeat.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка регистрации: {str(e)}")
        finally:
            conn.close()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = AuthApp()
    window.show()
    sys.exit(app.exec())