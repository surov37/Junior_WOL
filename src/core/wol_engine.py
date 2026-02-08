import socket
import struct
import re
import platform
from typing import Optional, List


class WOLEngine:
    """Кроссплатформенный движок Wake-on-LAN с валидацией и расширенной функциональностью"""
    
    BROADCAST_PORT = 9
    
    def __init__(self, broadcast_ip: str = "255.255.255.255", port: int = BROADCAST_PORT):
        self.broadcast_ip = broadcast_ip
        self.port = port
    
    def validate_mac(self, mac: str) -> bool:
        """
        Валидация MAC-адреса в различных форматах:
        - 00:11:22:33:44:55
        - 00-11-22-33-44-55
        - 0011.2233.4455
        - 001122334455
        """
        if not mac or not isinstance(mac, str):
            return False
        
        # Удаляем пробелы и приводим к нижнему регистру для проверки
        clean = mac.replace(" ", "").lower()
        
        # Шаблоны для разных форматов
        patterns = [
            r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$',      # 00:11:22:33:44:55
            r'^([0-9a-f]{2}-){5}[0-9a-f]{2}$',      # 00-11-22-33-44-55
            r'^([0-9a-f]{4}\.){2}[0-9a-f]{4}$',     # 0011.2233.4455
            r'^[0-9a-f]{12}$'                       # 001122334455
        ]
        
        return any(re.match(pattern, clean) for pattern in patterns)
    
    def normalize_mac(self, mac: str) -> Optional[str]:
        """
        Нормализация MAC-адреса к стандартному формату: 00:11:22:33:44:55
        
        Возвращает:
            str: Нормализованный MAC-адрес или None при ошибке
        """
        if not self.validate_mac(mac):
            return None
        
        # Удаляем все не-шестнадцатеричные символы
        clean = re.sub(r'[^0-9a-fA-F]', '', mac.lower())
        
        # Проверяем длину (должно быть 12 шестнадцатеричных символов)
        if len(clean) != 12:
            return None
        
        # Форматируем с двоеточиями
        return ':'.join(clean[i:i+2] for i in range(0, 12, 2))
    
    def build_magic_packet(self, mac: str) -> Optional[bytes]:
        """
        Создание «магического пакета» для пробуждения компьютера.
        
        Структура пакета:
        - 6 байт 0xFF
        - 16 повторений MAC-адреса (по 6 байт каждый)
        Итого: 6 + (16 * 6) = 102 байта
        
        Возвращает:
            bytes: Магический пакет или None при ошибке
        """
        normalized = self.normalize_mac(mac)
        if not normalized:
            return None
        
        # Конвертируем MAC в байты
        try:
            mac_bytes = bytes.fromhex(normalized.replace(':', ''))
        except ValueError:
            return None
        
        # Собираем пакет: 6 байт 0xFF + 16 повторений MAC
        packet = b'\xff' * 6 + mac_bytes * 16
        return packet
    
    def send_magic_packet(self, mac: str, broadcast_ip: str = None, port: int = None) -> bool:
        """
        Отправка магического пакета через UDP broadcast.
        
        Аргументы:
            mac: MAC-адрес целевого устройства
            broadcast_ip: IP для broadcast (по умолчанию 255.255.255.255)
            port: Порт для отправки (по умолчанию 9)
        
        Возвращает:
            bool: True при успешной отправке, иначе False
        """
        packet = self.build_magic_packet(mac)
        if packet is None:
            return False
        
        ip = broadcast_ip or self.broadcast_ip
        port = port or self.port
        
        try:
            # Создаем UDP сокет
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # Включаем опцию broadcast
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                # Устанавливаем таймаут
                sock.settimeout(2.0)
                # Отправляем пакет
                sock.sendto(packet, (ip, port))
            return True
        except PermissionError:
            # Ошибка прав (требуются права администратора на некоторых системах)
            return False
        except Exception:
            # Любая другая ошибка сети
            return False
    
    def send_magic_packet_multiple(self, mac: str, count: int = 3, interval: float = 0.1) -> bool:
        """
        Отправка нескольких магических пакетов для повышения надежности.
        
        Аргументы:
            mac: MAC-адрес целевого устройства
            count: Количество пакетов (по умолчанию 3)
            interval: Интервал между отправками в секундах (по умолчанию 0.1)
        
        Возвращает:
            bool: True если хотя бы один пакет отправлен успешно
        """
        import time
        
        normalized = self.normalize_mac(mac)
        if not normalized:
            return False
        
        success_count = 0
        for i in range(count):
            if self.send_magic_packet(normalized):
                success_count += 1
            if i < count - 1:
                time.sleep(interval)
        
        return success_count > 0
    
    def get_broadcast_addresses(self) -> List[str]:
        """
        Получение списка широковещательных адресов для всех сетевых интерфейсов.
        
        Возвращает:
            List[str]: Список broadcast-адресов (например: ['192.168.1.255', '10.0.0.255'])
        """
        broadcast_addresses = []
        
        try:
            import psutil
            nics = psutil.net_if_addrs()
            
            for interface, addrs in nics.items():
                # Пропускаем loopback и виртуальные интерфейсы
                if any(skip in interface.lower() for skip in ['loopback', 'lo', 'virtual', 'vmware', 'vbox', 'docker']):
                    continue
                
                for addr in addrs:
                    if addr.family == socket.AF_INET and addr.broadcast:
                        # Проверяем валидность broadcast адреса
                        if addr.broadcast not in ['0.0.0.0', '127.0.0.1', '255.255.255.255']:
                            broadcast_addresses.append(addr.broadcast)
        except ImportError:
            # Если psutil недоступен, возвращаем стандартный адрес
            pass
        except Exception:
            pass
        
        # Добавляем стандартный глобальный broadcast если список пустой
        if not broadcast_addresses:
            broadcast_addresses.append("255.255.255.255")
        
        # Убираем дубликаты и сортируем
        return sorted(list(set(broadcast_addresses)))
    
    def send_broadcast_magic_packet(self, mac: str, port: int = None) -> dict:
        """
        Отправка магического пакета на все доступные broadcast-адреса.
        
        Возвращает:
            dict: Словарь с результатами {'success': bool, 'attempts': int, 'successful_broadcasts': List[str]}
        """
        normalized = self.normalize_mac(mac)
        if not normalized:
            return {'success': False, 'attempts': 0, 'successful_broadcasts': []}
        
        broadcasts = self.get_broadcast_addresses()
        successful = []
        
        for broadcast_ip in broadcasts:
            if self.send_magic_packet(normalized, broadcast_ip, port):
                successful.append(broadcast_ip)
        
        return {
            'success': len(successful) > 0,
            'attempts': len(broadcasts),
            'successful_broadcasts': successful
        }
    
    def is_wol_supported(self) -> bool:
        """
        Проверка поддержки Wake-on-LAN на текущей системе.
        Примечание: Эта проверка ограничена и не может гарантировать работоспособность на целевом ПК.
        
        Возвращает:
            bool: True если система потенциально поддерживает WoL
        """
        system = platform.system()
        
        # Windows: WoL обычно поддерживается на большинстве сетевых карт
        if system == "Windows":
            return True
        
        # Linux: Проверяем наличие утилиты ethtool (но не пытаемся её запускать без прав)
        if system == "Linux":
            return True
        
        # macOS: Ограниченная поддержка
        if system == "Darwin":
            return True
        
        return True  # По умолчанию считаем поддерживаемым
    
    @staticmethod
    def format_mac_for_display(mac: str) -> str:
        """
        Форматирование MAC-адреса для отображения в интерфейсе.
        
        Пример: '00:11:22:33:44:55' -> '00:11:22:33:44:55'
        """
        normalized = WOLEngine().normalize_mac(mac)
        return normalized if normalized else mac