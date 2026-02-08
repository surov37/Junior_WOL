from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from .widgets import PulseStatusWidget, LogWidget, GradientLabel
from .styles import Theme
from core.system_info import SystemInfo
from core.wol_engine import WOLEngine


class MainWindow(QMainWindow):
    """Главное окно приложения с элегантным интерфейсом"""
    
    def __init__(self, network_stub, parent=None):
        super().__init__(parent)
        self.network_stub = network_stub
        self.wol_engine = WOLEngine()
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._setup_timer()
        
        # Инициализация состояния
        self.status_widget.set_state("offline")
        self._update_system_info()
        self.log_widget.append_log("Application started", "info")
    
    def _setup_window(self):
        self.setWindowTitle("Aether Wake")
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29,
                    stop:1 #24243e
                );
                border-radius: 16px;
            }
        """)
        
        # Центрирование окна
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(
            (screen.width() - self.minimumWidth()) // 2,
            (screen.height() - self.minimumHeight()) // 2,
            self.minimumWidth(),
            self.minimumHeight()
        )
    
    def _create_widgets(self):
        # Заголовок с градиентом
        self.title_label = GradientLabel("Aether Wake")
        self.title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            margin: 15px 0 5px 0;
        """)
        self.title_label.animate()
        
        # Статус подключения
        self.status_widget = PulseStatusWidget()
        
        # Системная информация
        self.sys_info_group = QGroupBox("System Overview")
        self.sys_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #a0a0c0;
                padding: 10px;
            }
        """)
        
        self.hostname_label = QLabel()
        self.ip_label = QLabel()
        self.mac_label = QLabel()
        self.os_label = QLabel()
        
        for label in [self.hostname_label, self.ip_label, self.mac_label, self.os_label]:
            label.setStyleSheet("color: #ffffff; padding: 3px 0;")
        
        # Панель управления
        self.control_group = QGroupBox("Power Control")
        self.control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #a0a0c0;
                padding: 10px;
            }
        """)
        
        self.wakeup_btn = QPushButton("Wake Up")
        self.shutdown_btn = QPushButton("Shut Down")
        self.reboot_btn = QPushButton("Reboot")
        
        # Настройка кнопок
        for btn in [self.wakeup_btn, self.shutdown_btn, self.reboot_btn]:
            btn.setMinimumHeight(40)
            btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        
        self.wakeup_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C853, stop:1 #00E676);
                border: 1px solid #00C853;
                border-radius: 8px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00B349, stop:1 #00CC66);
                border: 1px solid #00AA55;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #009940, stop:1 #00B359);
            }
        """)
        
        self.shutdown_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF1744, stop:1 #FF5252);
                border: 1px solid #FF1744;
                border-radius: 8px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E6153D, stop:1 #FF4040);
                border: 1px solid #D9143A;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #CC1337, stop:1 #E63939);
            }
        """)
        
        # Лог событий
        self.log_widget = LogWidget()
    
    def _setup_layout(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Заголовок
        main_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Статус
        main_layout.addWidget(self.status_widget)
        
        # Системная информация
        sys_layout = QVBoxLayout(self.sys_info_group)
        sys_layout.addWidget(self.hostname_label)
        sys_layout.addWidget(self.ip_label)
        sys_layout.addWidget(self.mac_label)
        sys_layout.addWidget(self.os_label)
        main_layout.addWidget(self.sys_info_group)
        
        # Панель управления
        control_layout = QHBoxLayout(self.control_group)
        control_layout.setSpacing(12)
        control_layout.addWidget(self.wakeup_btn)
        control_layout.addWidget(self.shutdown_btn)
        control_layout.addWidget(self.reboot_btn)
        main_layout.addWidget(self.control_group)
        
        # Лог событий
        log_group = QGroupBox("Event Log")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #a0a0c0;
                padding: 10px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_widget)
        main_layout.addWidget(log_group)
        
        # Кнопка сворачивания в трей
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.tray_btn = QPushButton("Minimize to Tray")
        self.tray_btn.setMinimumWidth(160)
        self.tray_btn.setMinimumHeight(36)
        bottom_layout.addWidget(self.tray_btn)
        main_layout.addLayout(bottom_layout)
        
        self.setCentralWidget(central_widget)
    
    def _connect_signals(self):
        # Кнопки управления
        self.wakeup_btn.clicked.connect(self._handle_wakeup)
        self.shutdown_btn.clicked.connect(self._handle_shutdown)
        self.reboot_btn.clicked.connect(self._handle_reboot)
        self.tray_btn.clicked.connect(self.close)
    
    def _setup_timer(self):
        """Таймер для периодического обновления статуса"""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_status)
        self._timer.start(3000)  # каждые 3 секунды
    
    def _update_system_info(self):
        """Обновление системной информации"""
        info = SystemInfo.get_system_info()
        self.hostname_label.setText(f"• Hostname: {info['hostname']}")
        self.ip_label.setText(f"• Local IP: {info['local_ip']}")
        self.mac_label.setText(f"• MAC Address: {info['mac_address'] or 'Not detected'}")
        self.os_label.setText(f"• OS: {info['os']}")
    
    def _update_status(self):
        """Обновление статуса подключения"""
        if self.network_stub.is_connected():
            self.status_widget.set_state("online")
        else:
            self.status_widget.set_state("offline")
    
    def _handle_wakeup(self):
        """Обработка команды пробуждения"""
        mac = SystemInfo.get_primary_mac()
        if not mac:
            self.log_widget.append_log("MAC address not detected", "error")
            return
        
        if self.wol_engine.send_magic_packet(mac):
            self.log_widget.append_log(f"Magic packet sent to {mac}", "success")
            self.log_widget.append_log("Computer should wake up shortly", "info")
        else:
            self.log_widget.append_log("Failed to send magic packet", "error")
    
    def _handle_shutdown(self):
        """Обработка команды выключения"""
        self.log_widget.append_log("Shutdown initiated (delay: 3s)", "warning")
        QTimer.singleShot(3000, lambda: self._execute_shutdown(0))
    
    def _handle_reboot(self):
        """Обработка команды перезагрузки"""
        self.log_widget.append_log("Reboot initiated (delay: 3s)", "warning")
        QTimer.singleShot(3000, lambda: self._execute_reboot(0))
    
    def _execute_shutdown(self, delay: int):
        from core.power_manager import PowerManager
        if PowerManager.shutdown(delay):
            self.log_widget.append_log("Shutdown command executed", "command")
        else:
            self.log_widget.append_log("Shutdown failed", "error")
    
    def _execute_reboot(self, delay: int):
        from core.power_manager import PowerManager
        if PowerManager.reboot(delay):
            self.log_widget.append_log("Reboot command executed", "command")
        else:
            self.log_widget.append_log("Reboot failed", "error")
    
    def on_server_connected(self):
        """Обработчик подключения к серверу"""
        self.status_widget.set_state("online")
        self.log_widget.append_log("Connected to cloud stub", "success")
    
    def on_server_disconnected(self):
        """Обработчик отключения от сервера"""
        self.status_widget.set_state("offline")
        self.log_widget.append_log("Disconnected from server", "warning")
    
    def on_command_received(self, command):
        """Обработчик команды от сервера"""
        from network.protocol import CommandAction
        
        self.log_widget.append_log(
            f"Command received: {command.action.value} (delay: {command.delay}s)",
            "command"
        )
        
        if command.action == CommandAction.WAKEUP:
            QTimer.singleShot(command.delay * 1000, self._handle_wakeup)
        
        elif command.action == CommandAction.SHUTDOWN:
            QTimer.singleShot(command.delay * 1000, lambda: self._execute_shutdown(0))
        
        elif command.action == CommandAction.REBOOT:
            QTimer.singleShot(command.delay * 1000, lambda: self._execute_reboot(0))
    
    def closeEvent(self, event):
        """Сворачивание в трей вместо закрытия"""
        event.ignore()
        self.hide()
        self.network_stub.tray_icon.showMessage(
            "Aether Wake",
            "Application minimized to system tray\nRight-click the icon to restore",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )