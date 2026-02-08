import platform
import subprocess
import sys
from typing import Optional


class PowerManager:
    """Управление питанием операционной системы"""
    
    @staticmethod
    def shutdown(delay_sec: int = 0) -> bool:
        """Выключение системы"""
        try:
            system = platform.system()
            if system == "Windows":
                cmd = f"shutdown /s /t {delay_sec}"
            elif system == "Linux":
                if delay_sec == 0:
                    cmd = "systemctl poweroff"
                else:
                    minutes = max(1, delay_sec // 60)
                    cmd = f"shutdown -h +{minutes}"
            elif system == "Darwin":
                if delay_sec == 0:
                    cmd = 'osascript -e \'tell app "System Events" to shut down\''
                else:
                    return False  # macOS не поддерживает отложенное выключение через скрипт
            else:
                return False
            
            subprocess.run(cmd, shell=True, check=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def reboot(delay_sec: int = 0) -> bool:
        """Перезагрузка системы"""
        try:
            system = platform.system()
            if system == "Windows":
                cmd = f"shutdown /r /t {delay_sec}"
            elif system == "Linux":
                if delay_sec == 0:
                    cmd = "systemctl reboot"
                else:
                    minutes = max(1, delay_sec // 60)
                    cmd = f"shutdown -r +{minutes}"
            elif system == "Darwin":
                if delay_sec == 0:
                    cmd = 'osascript -e \'tell app "System Events" to restart\''
                else:
                    return False
            else:
                return False
            
            subprocess.run(cmd, shell=True, check=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_os_name() -> str:
        """Получение человекочитаемого названия ОС"""
        system = platform.system()
        if system == "Windows":
            return f"Windows {platform.release()}"
        elif system == "Linux":
            return "Linux"
        elif system == "Darwin":
            return "macOS"
        return system