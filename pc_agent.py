import os
import time
import uuid
import socket
import platform
import subprocess
import json
import logging
from threading import Thread

import requests
import psutil


SERVER_URL = "https://your-server.com/api"
CHECK_INTERVAL = 10
AGENT_ID = str(uuid.uuid4())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pc_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        return ip
    except Exception as e:
        logger.error(f"Не удалось получить IP: {e}")
        return "127.0.0.1"

def get_mac_address():
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:  # MAC-адрес
                    mac = addr.address
                    if mac and mac != "00:00:00:00:00:00":
                        return mac.replace("-", ":").upper()
    except Exception as e:
        logger.error(f"Ошибка получения MAC: {e}")
    return "UNKNOWN"

def shutdown_system():
    logger.info("Выполняется выключение системы...")
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
        else:
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
    except Exception as e:
        logger.error(f"Ошибка выключения: {e}")

def reboot_system():
    logger.info("Выполняется перезагрузка системы...")
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
        else:
            subprocess.run(["sudo", "reboot"], check=True)
    except Exception as e:
        logger.error(f"Ошибка перезагрузки: {e}")

def get_agent_info():
    return {
        "agent_id": AGENT_ID,
        "hostname": socket.gethostname(),
        "ip": get_local_ip(),
        "mac": get_mac_address(),
        "os": platform.system(),
        "platform": platform.platform()
    }

def register_with_server():
    info = get_agent_info()
    try:
        response = requests.post(f"{SERVER_URL}/register", json=info, timeout=10)
        if response.status_code == 200:
            logger.info("Успешно зарегистрирован на сервере")
        else:
            logger.warning(f"Ошибка регистрации: {response.status_code}")
    except Exception as e:
        logger.error(f"Не удалось зарегистрироваться: {e}")

def check_for_commands():
    try:
        response = requests.post(
            f"{SERVER_URL}/check",
            json={"agent_id": AGENT_ID},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            command = data.get("command")
            if command == "shutdown":
                shutdown_system()
            elif command == "reboot":
                reboot_system()
            elif command == "ping":
                logger.info("Получена команда ping — ПК активен")
        elif response.status_code == 404:
            logger.debug("Команд нет")
        else:
            logger.warning(f"Неожиданный ответ сервера: {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка проверки команд: {e}")

def background_worker():
    register_with_server()
    while True:
        check_for_commands()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logger.info("Запуск PC Agent...")
    logger.info(f"Agent ID: {AGENT_ID}")
    logger.info(f"IP: {get_local_ip()}, MAC: {get_mac_address()}")

    worker = Thread(target=background_worker, daemon=True)
    worker.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Агент остановлен пользователем")