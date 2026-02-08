from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QColor
from PyQt6.QtCore import Qt


class TrayIcon(QSystemTrayIcon):
    """Системный трей с динамическими иконками"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "offline"
        self._create_icons()
        self.setIcon(self._icons["offline"])
        
        # Меню трея
        self.menu = QMenu(parent)
        
        self.status_action = self.menu.addAction("Status: Offline")
        self.status_action.setEnabled(False)
        
        self.menu.addSeparator()
        
        self.open_action = self.menu.addAction("Open Dashboard")
        self.quit_action = self.menu.addAction("Quit")
        
        self.setContextMenu(self.menu)
        self.setToolTip("Aether Wake — Power Management")
    
    def _create_icons(self):
        """Генерация иконок программно через QPainter"""
        self._icons = {}
        
        for state in ["online", "offline", "connecting"]:
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Фон круга
            painter.setBrush(QColor(30, 25, 60))
            painter.setPen(QColor(65, 55, 120))
            painter.drawEllipse(2, 2, 20, 20)
            
            # Цвет точки в зависимости от состояния
            if state == "online":
                color = QColor("#00C853")
            elif state == "connecting":
                color = QColor("#2979FF")
            else:
                color = QColor("#FF1744")
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(9, 9, 6, 6)
            
            painter.end()
            
            self._icons[state] = QIcon(pixmap)
    
    def set_state(self, state: str):
        """Обновление иконки и статуса в зависимости от состояния"""
        if state not in ["online", "offline", "connecting"]:
            state = "offline"
        
        self._state = state
        self.setIcon(self._icons[state])
        
        status_text = {
            "online": "Status: Online",
            "offline": "Status: Offline",
            "connecting": "Status: Connecting..."
        }
        
        self.status_action.setText(status_text[state])
        self.setToolTip(f"Aether Wake — {status_text[state][8:]}")
    
    def is_online(self) -> bool:
        return self._state == "online"