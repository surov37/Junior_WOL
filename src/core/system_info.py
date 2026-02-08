import platform
import socket
import uuid
import psutil
from typing import Optional, List, Tuple


class SystemInfo:
    """Сбор системной информации: MAC, IP, hostname"""
    
    @staticmethod
    def get_hostname() -> str:
        """Получение имени хоста"""
        return socket.gethostname()
    
    @staticmethod
    def get_local_ip() -> str:
        """Получение локального IP-адреса"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    @staticmethod
    def get_primary_mac() -> Optional[str]:
        """Получение MAC-адреса основного сетевого интерфейса"""
        try:
            # Способ 1: через UUID (работает на всех платформах)
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                          for elements in range(0, 2 * 6, 2)][::-1])
            if mac != "00:00:00:00:00:00":
                return mac
            
            # Способ 2: через psutil (более надёжно)
            nics = psutil.net_if_addrs()
            for interface, addrs in nics.items():
                # Пропускаем виртуальные и loopback интерфейсы
                if any(skip in interface.lower() for skip in ['loopback', 'virtual', 'vmware', 'vbox']):
                    continue
                
                for addr in addrs:
                    if addr.family == psutil.AF_LINK and addr.address != "00:00:00:00:00:00":
                        return addr.address
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_network_interfaces() -> List[Tuple[str, str, str]]:
        """Получение списка сетевых интерфейсов с IP и MAC"""
        interfaces = []
        nics = psutil.net_if_addrs()
        
        for name, addrs in nics.items():
            ip = None
            mac = None
            
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    ip = addr.address
                elif addr.family == psutil.AF_LINK:
                    mac = addr.address
            
            if ip and mac and mac != "00:00:00:00:00:00":
                interfaces.append((name, ip, mac))
        
        return interfaces
    
    @staticmethod
    def get_system_info() -> dict:
        """Полная системная информация для отправки на сервер"""
        return {
            "hostname": SystemInfo.get_hostname(),
            "os": SystemInfo.get_os_name(),
            "local_ip": SystemInfo.get_local_ip(),
            "mac_address": SystemInfo.get_primary_mac(),
            "platform": platform.platform(),
            "python_version": platform.python_version()
        }