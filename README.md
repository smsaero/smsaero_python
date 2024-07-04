# SmsAero API client

[![PyPI version](https://badge.fury.io/py/smsaero-api.svg)](https://badge.fury.io/py/smsaero-api)
[![Python Versions](https://img.shields.io/pypi/pyversions/smsaero-api.svg)](https://pypi.org/project/smsaero-api/)
[![Downloads](https://pepy.tech/badge/smsaero-api)](https://pepy.tech/project/smsaero-api)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](MIT-LICENSE)

## Installation (from PyPI):

```bash
pip install -U smsaero-api
```

## Usage example:

Get credentials from account settings page: https://smsaero.ru/cabinet/settings/apikey/

```python
from pprint import pprint
from smsaero import SmsAero, SmsAeroException


SMSAERO_EMAIL = 'your email'
SMSAERO_API_KEY = 'your api key'


def send_sms(phone: int, message: str) -> dict:
    """
    Sends an SMS message

    Parameters:
    phone (int): The phone number to which the SMS message will be sent.
    message (str): The content of the SMS message to be sent.

    Returns:
    dict: A dictionary containing the response from the SmsAero API.
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

#### Exceptions:

* `SmsAeroException` - base exception class for all exceptions raised by the library.
* `SmsAeroConnectionException` - exception raised when there is a connection error.
* `SmsAeroNoMoneyException` - exception raised when there is not enough money in the account.


## Command line usage:

```bash
SMSAERO_EMAIL="your email"
SMSAERO_API_KEY="your api key"

smsaero_send --email "$SMSAERO_EMAIL" --api_key "$SMSAERO_API_KEY" --phone 79038805678 --message 'Hello, World!'
```

## Run on Docker:

```bash
docker pull 'smsaero/smsaero_python:latest'
docker run -it --rm 'smsaero/smsaero_python:latest' smsaero_send --email "your email" --api_key "your api key" --phone 79038805678 --message 'Hello, World!'
```

## Compatibility:

* Currently version of library is compatible with Python 3.6+.
* Previous versions of Python supported by versions 2.2.0 and below.


## License:

```
MIT License
```
