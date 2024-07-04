# SmsAero клиент

[![PyPI version](https://badge.fury.io/py/smsaero-api.svg)](https://badge.fury.io/py/smsaero-api)
[![Python Versions](https://img.shields.io/pypi/pyversions/smsaero-api.svg)](https://pypi.org/project/smsaero-api/)
[![Downloads](https://pepy.tech/badge/smsaero-api)](https://pepy.tech/project/smsaero-api)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](MIT-LICENSE)

## Установка с использованием пакетного менеджера pip:

    $ pip install -U smsaero-api

## Пример использования в коде:

API-ключ вы можете получить в настройках аккаунта: https://smsaero.ru/cabinet/settings/apikey/

```python
from pprint import pprint
from smsaero import SmsAero, SmsAeroException


SMSAERO_EMAIL = 'ваш email'
SMSAERO_API_KEY = 'ваш api key'


def send_sms(phone: int, message: str) -> dict:
    """
    Отправка SMS сообщения

    Параметры:
    phone (int): Номер телефона.
    message (str): Содержание SMS сообщения.

    Возвращает:
    dict: Словарь, содержащий ответ от API SmsAero.
    """
    api = SmsAero(SMSAERO_EMAIL, SMSAERO_API_KEY)
    return api.send_sms(phone, message)


if __name__ == '__main__':
    try:
        result = send_sms(79038805678, 'Hello, World!')
        pprint(result)
    except SmsAeroException as e:
        print(f"An error occurred: {e}")
```

#### Исключения, возникающие в библиотеке:

* `SmsAeroException` - базовый класс для всех исключений, возникающих в библиотеке.
* `SmsAeroConnectionException` - исключение, возникающее при сетевых ошибках.
* `SmsAeroNoMoneyException` - исключение, возникающее при недостаточном количестве средств на счете.

## Использование в командной строке (полезно для автоматизации):

```bash
SMSAERO_EMAIL="ваш email"
SMSAERO_API_KEY="ваш api key"

smsaero_send --email "$SMSAERO_EMAIL" --api_key "$SMSAERO_API_KEY" --phone 79038805678 --message 'Hello, World!'
```

## Запуск в Docker (demo):

```bash
docker pull 'smsaero/smsaero_python:latest'
docker run -it --rm 'smsaero/smsaero_python:latest' smsaero_send --email "ваш email" --api_key "ваш api key" --phone 79038805678 --message 'Привет, Мир!'
```

## Совместимость с версиями Python:

* Текущая версия библиотеки совместима с Python 3.6+.
* Предыдущие версии Python поддерживаются версиями 2.2.0 и ниже.

## Лицензия библиотеки:

```
MIT License
```
