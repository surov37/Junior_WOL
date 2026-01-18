# FapuFap — PC Agent
import os
import time
import uuid
import socket
import platform
import subprocess
import json
import logging
import hashlib
import shlex
import signal
from threading import Thread, Lock
from datetime import datetime, timedelta
from pathlib import Path

import requests
import psutil
import schedule
from wakeonlan import send_magic_packet

CONFIG_PATH = Path("agent_config.json")
SERVER_CONFIG = {
    "base_url": "https://your-server.com/api",  # ← УБРАЛ ПРОБЕЛЫ!
    "endpoints": {
        "register": "/register",
        "heartbeat": "/heartbeat",
        "commands": "/commands",
        "metrics": "/metrics",
        "update": "/update"
    },
    "retry_attempts": 3,
    "timeout": 15
}

AGENT_CONFIG = {
    "agent_id": str(uuid.uuid4()),
    "version": "1.1.7",
    "check_interval": 60,
    "heartbeat_interval": 300,
    "max_log_size_mb": 10,
    "log_level": "INFO",
    "allowed_commands": ["dir", "ls", "ipconfig", "ifconfig", "whoami", "wake"],
    "security": {
        "command_whitelist": True,
        "hash_check": True,
        "max_command_length": 100
    },
    "metrics": {
        "enabled": True,
        "disk_partitions": ["/", "C:\\"]
    },
    "wol_interface": None
}

# Инициализация планировщика ОДИН РАЗ
schedule.every().day.at("02:00").do(lambda: send_scheduled_metrics())

def send_scheduled_metrics():
    """Функция для отправки метрик по расписанию"""
    try:
        server = ServerCommunicator()
        server.send_metrics()
    except Exception as e:
        logging.error(f"Ошибка отправки метрик по расписанию: {e}")

def load_config():
    global AGENT_CONFIG, SERVER_CONFIG
    
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                AGENT_CONFIG.update(config.get("agent", {}))
                SERVER_CONFIG.update(config.get("server", {}))
            logging.info("Конфигурация загружена из файла")
        except Exception as e:
            logging.error(f"Ошибка загрузки конфигурации: {e}. Используются настройки по умолчанию.")
    
    # Гарантируем наличие agent_id
    if "agent_id" not in AGENT_CONFIG or not AGENT_CONFIG["agent_id"]:
        AGENT_CONFIG["agent_id"] = str(uuid.uuid4())
        logging.info("Создан новый agent_id")

    save_config()
    return AGENT_CONFIG, SERVER_CONFIG

def save_config():
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump({
                "agent": AGENT_CONFIG,
                "server": SERVER_CONFIG
            }, f, indent=2)
        logging.debug("Конфигурация сохранена")
    except Exception as e:
        logging.error(f"Ошибка сохранения конфигурации: {e}")

def get_hardware_id():
    try:
        mac = get_mac_address().replace(":", "").replace("-", "").upper()
        hostname = socket.gethostname()
        return hashlib.sha256(f"{mac}{hostname}".encode()).hexdigest()[:16]
    except Exception as e:
        logging.error(f"Ошибка генерации Hardware ID: {e}")
        return "hw_unknown"

def get_system_metrics():
    metrics = {
        "cpu": {
            "percent": psutil.cpu_percent(interval=1),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True)
        },
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
            "percent_used": psutil.virtual_memory().percent
        },
        "disk": {},
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "uptime": str(timedelta(seconds=time.time() - psutil.boot_time())).split(".")[0]
    }
    
    for partition in AGENT_CONFIG["metrics"]["disk_partitions"]:
        try:
            if os.name == 'nt':
                if not partition.endswith(':\\'):
                    continue
            usage = psutil.disk_usage(partition)
            metrics["disk"][partition] = {
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "percent_used": usage.percent
            }
        except Exception as e:
            logging.debug(f"Ошибка сбора метрик для {partition}: {e}")
    
    return metrics

def get_network_info():
    return {
        "local_ip": get_local_ip(),
        "public_ip": get_public_ip(),
        "mac_address": get_mac_address(),
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn()
    }

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text.strip()
    except Exception as e:
        logging.debug(f"Не удалось определить публичный IP: {e}")
        return "unknown"

def validate_and_translate_command(cmd: str):
    if not cmd.strip():
        return None

    if len(cmd) > AGENT_CONFIG["security"]["max_command_length"]:
        logging.warning(f"Команда превышает максимальную длину: {len(cmd)}")
        return None

    # Разделение на аргументы безопасно
    try:
        parts = shlex.split(cmd)
    except ValueError as e:
        logging.warning(f"Неверный синтаксис команды: {e}")
        return None

    if not parts:
        return None

    base = parts[0].lower()

    # ОС-специфичная подмена
    cmd_mapping = {
        'windows': {'ls': 'dir', 'ifconfig': 'ipconfig'},
        'linux': {'dir': 'ls', 'ipconfig': 'ifconfig'},
        'darwin': {'dir': 'ls', 'ipconfig': 'ifconfig'}
    }

    current_os = platform.system().lower()
    os_family = 'windows' if current_os == 'windows' else 'linux'

    if os_family in cmd_mapping and base in cmd_mapping[os_family]:
        parts[0] = cmd_mapping[os_family][base]

    base = parts[0].lower()

    if AGENT_CONFIG["security"]["command_whitelist"]:
        allowed = [c.lower() for c in AGENT_CONFIG["allowed_commands"]]
        if base not in allowed:
            logging.warning(f"Заблокирована неавторизованная команда: {base}")
            return None

    return parts

def verify_update_package(file_path, expected_hash):
    if not AGENT_CONFIG["security"]["hash_check"]:
        return True
        
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return file_hash == expected_hash
    except Exception as e:
        logging.error(f"Проверка обновления не пройдена: {e}")
        return False

class ServerCommunicator:
    def __init__(self):
        self.base_url = SERVER_CONFIG["base_url"].rstrip('/')  # Защита от лишних слэшей
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"PC-Agent/{AGENT_CONFIG['version']}",
            "Content-Type": "application/json"
        })
        self.lock = Lock()

    def _make_request(self, endpoint, payload=None, method="POST"):
        url = self.base_url + endpoint
        for attempt in range(SERVER_CONFIG["retry_attempts"]):
            try:
                with self.lock:
                    response = self.session.request(
                        method,
                        url,
                        json=payload,
                        timeout=SERVER_CONFIG["timeout"]
                    )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt
                logging.warning(f"Запрос не удался (попытка {attempt+1}/{SERVER_CONFIG['retry_attempts']}): {str(e)}")
                time.sleep(wait_time)
        logging.error(f"Все попытки для {endpoint} исчерпаны")
        return None

    def register_agent(self):
        payload = {
            "agent_id": AGENT_CONFIG["agent_id"],
            "hardware_id": get_hardware_id(),
            "version": AGENT_CONFIG["version"],
            "system_info": {
                "os": platform.system(),
                "platform": platform.platform(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "python_version": platform.python_version()
            },
            "network": get_network_info(),
            "first_seen": datetime.now().isoformat()
        }
        return self._make_request(SERVER_CONFIG["endpoints"]["register"], payload)

    def send_heartbeat(self):
        payload = {
            "agent_id": AGENT_CONFIG["agent_id"],
            "timestamp": datetime.now().isoformat(),
            "status": "active",
            "metrics": get_system_metrics() if AGENT_CONFIG["metrics"]["enabled"] else None,
            "network": get_network_info()
        }
        return self._make_request(SERVER_CONFIG["endpoints"]["heartbeat"], payload)

    def check_commands(self):
        payload = {"agent_id": AGENT_CONFIG["agent_id"]}
        return self._make_request(SERVER_CONFIG["endpoints"]["commands"], payload)

    def send_metrics(self):
        if not AGENT_CONFIG["metrics"]["enabled"]:
            return None
            
        payload = {
            "agent_id": AGENT_CONFIG["agent_id"],
            "timestamp": datetime.now().isoformat(),
            "metrics": get_system_metrics()
        }
        return self._make_request(SERVER_CONFIG["endpoints"]["metrics"], payload)

    def download_update(self, package_url, expected_hash):
        try:
            response = requests.get(package_url, stream=True, timeout=30)
            response.raise_for_status()
            
            temp_path = Path(f"update_{AGENT_CONFIG['version']}.tmp")
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if verify_update_package(temp_path, expected_hash):
                logging.info("Пакет обновления успешно проверен")
                return temp_path
            else:
                logging.error("Проверка пакета обновления не пройдена!")
                temp_path.unlink(missing_ok=True)
                return None
        except Exception as e:
            logging.error(f"Ошибка загрузки обновления: {e}")
            return None

def execute_shell_command(command):
    parts = validate_and_translate_command(command)
    if parts is None:
        return "Команда заблокирована политиками безопасности или недопустима"

    try:
        # Безопасное выполнение БЕЗ shell=True
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout or result.stderr
        return output[:1000] + "..." if len(output) > 1000 else output
    except subprocess.TimeoutExpired:
        return "Команда превысила лимит времени (30 секунд)"
    except FileNotFoundError:
        return f"Команда не найдена: {parts[0]}"
    except Exception as e:
        return f"Ошибка выполнения: {str(e)}"

def wake_on_lan(target_mac):
    try:
        clean_mac = target_mac.replace(":", "").replace("-", "").lower()
        if len(clean_mac) != 12:
            return f"Неверный формат MAC-адреса: {target_mac}"
        
        formatted_mac = ":".join([clean_mac[i:i+2] for i in range(0, 12, 2)])
        
        interface = AGENT_CONFIG.get("wol_interface")
        send_magic_packet(formatted_mac, interface=interface)
        
        logging.info(f"Wake-on-LAN пакет отправлен на {formatted_mac} через {interface or 'все интерфейсы'}")
        return f"Компьютер с MAC {formatted_mac} будет включен"
    except Exception as e:
        error_msg = f"Ошибка Wake-on-LAN: {str(e)}"
        logging.error(error_msg)
        return error_msg

def apply_update(package_path):
    try:
        logging.info("Применение обновления агента...")
        new_version = "2.0.0"  # В реальности — из метаданных
        AGENT_CONFIG["version"] = new_version
        save_config()
        
        package_path.unlink(missing_ok=True)
        logging.info(f"Агент обновлен до версии {new_version}")
        return True
    except Exception as e:
        logging.error(f"Обновление не удалось: {e}")
        return False

class PC_Agent:
    def __init__(self):
        self.config = AGENT_CONFIG
        self.server = ServerCommunicator()
        self.running = True
        self.last_heartbeat = datetime.min
        
    def handle_command(self, command_data):
        cmd_type = command_data.get("type")
        cmd_value = command_data.get("value", "")
        
        logging.info(f"Выполнение команды: {cmd_type} {str(cmd_value)[:20]}...")
        
        if cmd_type == "shutdown":
            self.running = False
            shutdown_system()
            return "Инициировано выключение системы"
            
        elif cmd_type == "reboot":
            self.running = False
            reboot_system()
            return "Инициирована перезагрузка системы"
            
        elif cmd_type == "execute":
            return execute_shell_command(cmd_value)
            
        elif cmd_type == "wake":
            return wake_on_lan(cmd_value)
            
        elif cmd_type == "update":
            package_path = self.server.download_update(
                cmd_value.get("url"),
                cmd_value.get("hash")
            )
            if package_path and apply_update(package_path):
                return "Обновление успешно применено"
            return "Ошибка обновления"
            
        elif cmd_type == "config_update":
            self.config.update(cmd_value)
            save_config()
            return "Конфигурация обновлена"
            
        elif cmd_type == "ping":
            return f"Агент активен - Версия: {self.config['version']}"
        
        return "Неизвестная команда"

    def periodic_tasks(self):
        while self.running:
            try:
                if (datetime.now() - self.last_heartbeat).total_seconds() > self.config["heartbeat_interval"]:
                    self.server.send_heartbeat()
                    self.last_heartbeat = datetime.now()
                
                # Запуск отложенных задач (например, 02:00)
                schedule.run_pending()
                
                time.sleep(self.config["check_interval"])
            except Exception as e:
                logging.error(f"Ошибка периодической задачи: {e}")
                time.sleep(60)

    def command_monitor(self):
        while self.running:
            try:
                response = self.server.check_commands()
                if response and "commands" in response:
                    for cmd in response["commands"]:
                        result = self.handle_command(cmd)
                        logging.info(f"Результат команды: {result[:50]}...")
                time.sleep(self.config["check_interval"])
            except Exception as e:
                logging.error(f"Ошибка мониторинга команд: {e}")
                time.sleep(30)

    def start(self):
        logging.info(f"Запуск PC Agent v{self.config['version']}")
        logging.info(f"ID Агента: {self.config['agent_id']}")
        logging.info(f"Hardware ID: {get_hardware_id()}")
        
        self.server.register_agent()
        
        Thread(target=self.periodic_tasks, daemon=True).start()
        Thread(target=self.command_monitor, daemon=True).start()
        
        while self.running:
            time.sleep(1)

def setup_logging():
    log_path = Path("pc_agent.log")
    
    if log_path.exists() and log_path.stat().st_size > AGENT_CONFIG["max_log_size_mb"] * 1024 * 1024:
        archive_path = Path(f"pc_agent_{int(time.time())}.log")
        log_path.rename(archive_path)
        logging.info(f"Старый лог архивирован: {archive_path}")
    
    logging.basicConfig(
        level=getattr(logging, AGENT_CONFIG.get("log_level", "INFO").upper()),
        format="%(asctime)s [%(levelname)-8s] %(filename)s:%(lineno)d - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"

def get_mac_address():
    """Надёжное получение MAC через psutil"""
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            if "Loopback" in iface or "lo" in iface:
                continue
            for addr in addrs:
                if addr.family == psutil.AF_LINK and addr.address and addr.address != "00:00:00:00:00:00":
                    return addr.address.upper()
    except Exception as e:
        logging.error(f"Ошибка определения MAC: {e}")
    return "00:00:00:00:00:00"

def shutdown_system():
    logging.info("Инициирование выключения системы...")
    try:
        if os.name == 'nt':
            os.system("shutdown /s /t 10 /c \"Удаленное выключение инициировано PC Agent\"")
        else:
            os.system("sudo shutdown -h +1 \"Удаленное выключение инициировано PC Agent\"")
    except Exception as e:
        logging.error(f"Выключение не удалось: {e}")

def reboot_system():
    logging.info("Инициирование перезагрузки системы...")
    try:
        if os.name == 'nt':
            os.system("shutdown /r /t 10 /c \"Удаленная перезагрузка инициирована PC Agent\"")
        else:
            os.system("sudo reboot")
    except Exception as e:
        logging.error(f"Перезагрузка не удалась: {e}")

def signal_handler(signum, frame):
    logging.info(f"Получен сигнал {signum}. Завершение работы...")
    global agent_instance
    if agent_instance:
        agent_instance.running = False

if __name__ == "__main__":
    agent_instance = None
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    load_config()
    setup_logging()
    
    agent_instance = PC_Agent()
    
    try:
        agent_instance.start()
    except KeyboardInterrupt:
        logging.info("Агент остановлен пользователем")
    except Exception as e:
        logging.critical(f"Агент аварийно завершил работу: {e}", exc_info=True)
    finally:
        if agent_instance:
            agent_instance.running = False
        logging.info("PC Agent завершил работу")
