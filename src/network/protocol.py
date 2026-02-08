from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import json
import time


class CommandAction(str, Enum):
    """Типы команд от сервера"""
    WAKEUP = "wakeup"
    SHUTDOWN = "shutdown"
    REBOOT = "reboot"
    STATUS = "status"
    HEARTBEAT = "heartbeat"


@dataclass
class ServerCommand:
    """Структура команды от сервера"""
    action: CommandAction
    target: str = "self"  # "self" или конкретный MAC
    delay: int = 0  # задержка в секундах
    auth_token: Optional[str] = None
    timestamp: float = 0.0
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["ServerCommand"]:
        """Парсинг JSON в команду"""
        try:
            return cls(
                action=CommandAction(data.get("action", "status")),
                target=data.get("target", "self"),
                delay=int(data.get("delay", 0)),
                auth_token=data.get("auth_token"),
                timestamp=data.get("timestamp", time.time())
            )
        except (ValueError, KeyError):
            return None
    
    def to_json(self) -> str:
        """Сериализация команды в JSON"""
        return json.dumps({
            "action": self.action.value,
            "target": self.target,
            "delay": self.delay,
            "timestamp": self.timestamp
        })


@dataclass
class ClientStatus:
    """Статус клиента для отправки на сервер"""
    device_id: str
    hostname: str
    mac_address: str
    local_ip: str
    status: str  # "online", "offline", "sleeping"
    last_heartbeat: float
    
    def to_json(self) -> str:
        """Сериализация статуса в JSON"""
        return json.dumps({
            "device_id": self.device_id,
            "hostname": self.hostname,
            "mac_address": self.mac_address,
            "local_ip": self.local_ip,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat
        })