from PyQt6.QtGui import QColor, QLinearGradient, QGradient
from PyQt6.QtCore import Qt


class Theme:
    """Цветовая палитра и градиенты темы"""
    
    # Основные цвета
    BG_DARK = "#0f0c29"
    BG_DARKER = "#0a081a"
    BG_DARKEST = "#05040d"
    
    ACCENT_PRIMARY = "#8A2BE2"   # Фиолетовый
    ACCENT_SECONDARY = "#4169E1" # Синий
    ACCENT_SUCCESS = "#00C853"
    ACCENT_WARNING = "#FFAB00"
    ACCENT_ERROR = "#FF1744"
    
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0c0"
    TEXT_DISABLED = "#606080"
    
    PANEL_BG = "#1a173a"
    PANEL_BORDER = "#302b63"
    
    @staticmethod
    def gradient_header() -> QLinearGradient:
        """Градиент для заголовка"""
        gradient = QLinearGradient(0, 0, 400, 80)
        gradient.setColorAt(0.0, QColor("#8A2BE2"))
        gradient.setColorAt(1.0, QColor("#4169E1"))
        gradient.setCoordinateMode(QGradient.CoordinateMode.ObjectMode)
        return gradient
    
    @staticmethod
    def gradient_status_online() -> QLinearGradient:
        """Градиент для онлайн статуса"""
        gradient = QLinearGradient(0, 0, 200, 40)
        gradient.setColorAt(0.0, QColor("#00C853"))
        gradient.setColorAt(1.0, QColor("#00E676"))
        return gradient
    
    @staticmethod
    def gradient_status_connecting() -> QLinearGradient:
        """Пульсирующий градиент для подключения"""
        gradient = QLinearGradient(0, 0, 200, 40)
        gradient.setColorAt(0.0, QColor("#2979FF"))
        gradient.setColorAt(1.0, QColor("#448AFF"))
        return gradient
    
    @staticmethod
    def gradient_button_normal() -> str:
        """Градиент для обычной кнопки"""
        return """
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #302b63,
                stop:1 #24243e
            );
            border: 1px solid #403a70;
        """
    
    @staticmethod
    def gradient_button_hover() -> str:
        """Градиент для кнопки при наведении"""
        return """
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #4169E1,
                stop:1 #8A2BE2
            );
            border: 1px solid #5a4fcf;
        """
    
    @staticmethod
    def gradient_button_pressed() -> str:
        """Градиент для кнопки при нажатии"""
        return """
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #2a1b9a,
                stop:1 #5a189a
            );
            border: 1px solid #4a148c;
        """


STYLESHEET = """
/* Глобальные стили */
QWidget {
    background-color: #0f0c29;
    color: #ffffff;
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #0f0c29;
    border: none;
}

/* Панели */
QGroupBox {
    background-color: #1a173a;
    border: 1px solid #302b63;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 5px;
    color: #a0a0c0;
    font-size: 13px;
    font-weight: bold;
}

/* Кнопки */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #302b63, stop:1 #24243e);
    border: 1px solid #403a70;
    border-radius: 8px;
    padding: 10px 20px;
    color: white;
    font-weight: 500;
    min-width: 100px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4169E1, stop:1 #8A2BE2);
    border: 1px solid #5a4fcf;
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2a1b9a, stop:1 #5a189a);
    border: 1px solid #4a148c;
}

QPushButton:disabled {
    background: #15122a;
    border: 1px solid #2a254a;
    color: #606080;
}

/* Текстовые поля */
QLineEdit, QTextEdit {
    background-color: #15122a;
    border: 1px solid #302b63;
    border-radius: 6px;
    padding: 8px 12px;
    color: white;
    selection-background-color: #4169E1;
    selection-color: white;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #8A2BE2;
}

/* Скроллбары */
QScrollBar:vertical {
    border: none;
    background: #15122a;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #302b63;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #4169E1;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Статус-бар */
QStatusBar {
    background-color: #15122a;
    color: #a0a0c0;
    padding: 4px 8px;
    border-top: 1px solid #302b63;
}

/* Меню */
QMenu {
    background-color: #1a173a;
    border: 1px solid #302b63;
    padding: 5px;
}

QMenu::item {
    padding: 8px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #302b63;
}

QMenu::separator {
    height: 1px;
    background: #302b63;
    margin: 4px 0;
}
"""