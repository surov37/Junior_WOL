# Aether Wake — Элегантное управление питанием ПК

Минималистичное десктопное приложение для удалённого включения/выключения компьютера через Wake-on-LAN с облачной интеграцией.

## Установка

```bash
git clone https://github.com/yourname/aether-wake.git
cd aether-wake
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
python src/main.py