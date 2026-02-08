from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, 
    QPushButton, QTextEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtProperty, QRectF, QEasingCurve, QPropertyAnimation, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QFont, QFontMetrics


class PulseStatusWidget(QWidget):
    """Анимированный индикатор статуса с пульсацией"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "offline"
        self._pulse_radius = 0.0
        self._opacity = 1.0
        
        # Анимация пульсации
        self._pulse_anim = QPropertyAnimation(self, b"pulseRadius")
        self._pulse_anim.setDuration(1500)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(15.0)
        
        # Анимация подключения
        self._connect_anim = QPropertyAnimation(self, b"opacity")
        self._connect_anim.setDuration(800)
        self._connect_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 16, 8)
        layout.setSpacing(10)
        
        # Иконка статуса
        self.icon = QWidget()
        self.icon.setFixedSize(16, 16)
        
        # Текст статуса
        self.label = QLabel("Offline")
        self.label.setStyleSheet("font-weight: 500; color: #a0a0c0;")
        
        layout.addWidget(self.icon)
        layout.addWidget(self.label)
        layout.addStretch()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Фон плашки
        if self._state == "online":
            bg_color = QColor(138, 43, 226, 30)  # Фиолетовый 30%
            border_color = QColor(138, 43, 226, 60)
        elif self._state == "connecting":
            bg_color = QColor(65, 105, 225, 30)  # Синий 30%
            border_color = QColor(65, 105, 225, 60)
        else:
            bg_color = QColor(255, 23, 68, 30)  # Красный 30%
            border_color = QColor(255, 23, 68, 60)
        
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        
        # Пульсирующий круг (только для connecting)
        if self._state == "connecting" and self._pulse_radius > 0:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(65, 105, 225, 100), 2))
            center = self.icon.geometry().center()
            painter.drawEllipse(center, self._pulse_radius, self._pulse_radius)
            painter.setPen(QPen(QColor(65, 105, 225, 180), 2))
            painter.drawEllipse(center, self._pulse_radius * 0.6, self._pulse_radius * 0.6)
    
    def set_state(self, state: str):
        """Установка состояния: online, offline, connecting"""
        self._state = state
        
        if state == "online":
            self.label.setText("Online")
            self.label.setStyleSheet("color: #00C853; font-weight: 500;")
            self._pulse_anim.stop()
            self.icon.update()
            
        elif state == "offline":
            self.label.setText("Offline")
            self.label.setStyleSheet("color: #FF1744; font-weight: 500;")
            self._pulse_anim.stop()
            self.icon.update()
            
        elif state == "connecting":
            self.label.setText("Connecting...")
            self.label.setStyleSheet("color: #2979FF; font-weight: 500;")
            self._pulse_anim.start()
            self.icon.update()
        
        self.update()
    
    def paintEventIcon(self, painter: QPainter, rect: QRectF):
        """Отрисовка иконки статуса внутри круга"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Цвет иконки
        if self._state == "online":
            color = QColor("#00C853")
        elif self._state == "connecting":
            color = QColor("#2979FF")
        else:
            color = QColor("#FF1744")
        
        # Круг фона
        painter.setBrush(QColor(20, 15, 45))
        painter.setPen(QPen(QColor(48, 43, 99), 1))
        painter.drawEllipse(rect)
        
        # Точка статуса
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.center(), 4, 4)
    
    def get_pulse_radius(self):
        return self._pulse_radius
    
    def set_pulse_radius(self, value):
        self._pulse_radius = value
        self.icon.update()
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    pulseRadius = pyqtProperty(float, get_pulse_radius, set_pulse_radius)
    opacity = pyqtProperty(float, get_opacity, set_opacity)


class LogWidget(QTextEdit):
    """Виджет лога событий с автопрокруткой"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFixedHeight(150)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #15122a;
                border: 1px solid #302b63;
                border-radius: 8px;
                padding: 8px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self._max_lines = 100
    
    def append_log(self, message: str, level: str = "info"):
        """Добавление записи в лог с цветовой подсветкой"""
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        
        colors = {
            "info": "#a0a0c0",
            "success": "#00C853",
            "warning": "#FFAB00",
            "error": "#FF1744",
            "command": "#8A2BE2"
        }
        
        color = colors.get(level, colors["info"])
        formatted = f'<span style="color:#606080">[{timestamp}]</span> ' \
                   f'<span style="color:{color};">{message}</span>'
        
        self.append(formatted)
        
        # Ограничение количества строк
        while self.document().blockCount() > self._max_lines:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        
        # Автопрокрутка вниз
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class GradientLabel(QLabel):
    """Текст с градиентной заливкой"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._gradient_pos = 0.0
        self.setStyleSheet("font-size: 24px; font-weight: 600;")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Динамический градиент
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0 + self._gradient_pos, QColor("#8A2BE2"))
        gradient.setColorAt(0.5 + self._gradient_pos, QColor("#4169E1"))
        gradient.setColorAt(1.0 + self._gradient_pos, QColor("#8A2BE2"))
        
        painter.setPen(gradient)
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
    
    def animate(self):
        """Запуск анимации градиента"""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_gradient)
        self._timer.start(50)
    
    def _update_gradient(self):
        self._gradient_pos = (self._gradient_pos + 0.01) % 1.0
        self.update()