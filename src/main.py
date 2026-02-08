import sys
import asyncio
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from ui.main_window import MainWindow
from ui.tray import TrayIcon
from network.client_stub import ServerStub


class AsyncioThread(QThread):
    """Поток для запуска asyncio event loop"""
    
    def __init__(self, stub: ServerStub):
        super().__init__()
        self.stub = stub
        self.loop = None
    
    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Запуск подключения
        self.loop.run_until_complete(self.stub.connect())
        
        # Запуск основного цикла
        self.loop.run_forever()
    
    def stop(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.wait(2000)


class Application:
    """Основной класс приложения"""
    
    def __init__(self):
        # Настройка Qt
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar)
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Aether Wake")
        self.app.setApplicationVersion("1.0.0")
        self.app.setQuitOnLastWindowClosed(False)
        
        # Инициализация компонентов
        self.stub = ServerStub()
        self.tray_icon = TrayIcon()
        self.stub.tray_icon = self.tray_icon  # для доступа к showMessage
        
        # Создание окна
        self.window = MainWindow(self.stub)
        self.stub.tray_icon = self.tray_icon
        
        # Подключение сигналов
        self.stub.connected.connect(self.window.on_server_connected)
        self.stub.disconnected.connect(self.window.on_server_disconnected)
        self.stub.command_received.connect(self.window.on_command_received)
        
        # Меню трея
        self.tray_icon.open_action.triggered.connect(self._restore_window)
        self.tray_icon.quit_action.triggered.connect(self._quit_app)
        
        # Показ иконки трея
        self.tray_icon.show()
        
        # Запуск асинхронного потока
        self.async_thread = AsyncioThread(self.stub)
        self.async_thread.start()
        
        # Обработка SIGINT для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _restore_window(self):
        """Восстановление окна из трея"""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
    
    def _quit_app(self):
        """Корректное завершение приложения"""
        self.tray_icon.hide()
        self.async_thread.stop()
        self.app.quit()
    
    def _signal_handler(self, sig, frame):
        """Обработчик сигналов ОС"""
        print("\nShutdown signal received...")
        self._quit_app()
    
    def run(self):
        """Запуск основного цикла приложения"""
        # Показ окна с небольшой задержкой для плавного появления
        QTimer.singleShot(300, self.window.show)
        
        # Запуск цикла событий Qt
        exit_code = self.app.exec()
        
        # Очистка ресурсов
        self.async_thread.stop()
        sys.exit(exit_code)


if __name__ == "__main__":
    # Исправление для Windows (multiprocessing)
    import multiprocessing
    multiprocessing.freeze_support()
    
    app = Application()
    app.run()