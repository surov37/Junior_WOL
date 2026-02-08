import asyncio
import json
import uuid
import time
from typing import Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from .protocol import ServerCommand, CommandAction


class ServerStub(QObject):
    """
    Элегантная заглушка сервера для разработки.
    Симулирует облачное подключение через асинхронные команды.
    """
    
    # Сигналы для общения с UI
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    command_received = pyqtSignal(object)  # ServerCommand
    heartbeat = pyqtSignal(float)  # timestamp
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_id = str(uuid.uuid4())
        self._is_connected = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._command_task: Optional[asyncio.Task] = None
        self._command_handler: Optional[Callable] = None
    
    async def connect(self):
        """Симуляция подключения к серверу"""
        await asyncio.sleep(0.8)  # имитация задержки сети
        
        self._is_connected = True
        self.connected.emit()
        
        # Запуск фоновых задач
        self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
        self._command_task = asyncio.create_task(self._simulate_commands())
    
    async def disconnect(self):
        """Отключение от сервера"""
        self._is_connected = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        if self._command_task:
            self._command_task.cancel()
            self._command_task = None
        
        self.disconnected.emit()
    
    def is_connected(self) -> bool:
        """Проверка статуса подключения"""
        return self._is_connected
    
    def set_command_handler(self, handler: Callable):
        """Установка обработчика команд"""
        self._command_handler = handler
    
    async def _send_heartbeats(self):
        """Периодическая отправка heartbeat"""
        while self._is_connected:
            await asyncio.sleep(5.0)
            if self._is_connected:
                self.heartbeat.emit(time.time())
    
    async def _simulate_commands(self):
        """Симуляция получения команд от сервера"""
        # Демонстрационный сценарий: пробуждение → выключение через 30 сек
        await asyncio.sleep(8)
        if not self._is_connected:
            return
        
        # Команда пробуждения (для демонстрации)
        wakeup_cmd = ServerCommand(
            action=CommandAction.WAKEUP,
            target="self",
            auth_token="stub_token_wakeup"
        )
        self.command_received.emit(wakeup_cmd)
        if self._command_handler:
            self._command_handler(wakeup_cmd)
        
        await asyncio.sleep(15)
        if not self._is_connected:
            return
        
        # Команда выключения
        shutdown_cmd = ServerCommand(
            action=CommandAction.SHUTDOWN,
            target="self",
            delay=5,
            auth_token="stub_token_shutdown"
        )
        self.command_received.emit(shutdown_cmd)
        if self._command_handler:
            self._command_handler(shutdown_cmd)
    
    async def send_status(self, status_data: dict):
        """Симуляция отправки статуса на сервер"""
        await asyncio.sleep(0.1)  # имитация задержки
        print(f"[STUB] Status sent: {status_data.get('status')}")