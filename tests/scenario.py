"""Модуль тестовых сценариев для тестирования API SMSAero."""

import logging
import os
import time
from typing import Union, List

import smsaero

SMS_AERO_EMAIL = os.getenv("SMSAERO_EMAIL")
SMS_AERO_API_KEY = os.getenv("SMSAERO_API_KEY")
PHONE_NUMBER = os.getenv("PHONE_NUMBER") and int(os.getenv("PHONE_NUMBER"))
PHONE_NUMBERS = os.getenv("PHONE_NUMBERS")
TEXT_MESSAGE = os.getenv("TEXT_MESSAGE", "Hello, World!")
TEST_MODE = bool(int(os.getenv("TEST_MODE", "0")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
GROUP_NAME = "test_group"


LOG_LEVEL = logging.DEBUG if LOG_LEVEL == "DEBUG" else logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(logging.StreamHandler())

smsaero_logger = logging.getLogger("smsaero")
smsaero_logger.setLevel(LOG_LEVEL)
smsaero_logger.addHandler(logging.StreamHandler())


class SMSAeroError(Exception):
    """Базовый класс для исключений в модуле."""

class GroupError(SMSAeroError):
    """Исключение при работе с группами."""

class BlackListError(SMSAeroError):
    """Исключение при работе с черным списком."""

class ContactError(SMSAeroError):
    """Исключение при работе с контактами."""

class AuthorizationError(SMSAeroError):
    """Исключение при ошибке авторизации."""

class BalanceError(SMSAeroError):
    """Исключение при недостаточном балансе."""

class MessageError(SMSAeroError):
    """Исключение при работе с сообщениями."""


class Base:
    """Базовый класс для всех тестовых сценариев."""

    def __init__(self, api):
        """Инициализация базового класса.

        Args:
            api: Экземпляр класса SmsAero API
        """
        self.api = api

    def get_groups_list(self) -> dict:
        """Получение списка групп.

        Returns:
            dict: Словарь групп {id: name}
        """
        group_list_response = self.api.group_list()
        return {
            group["id"]: group["name"]
            for group in group_list_response.values()
            if isinstance(group, dict) and "name" in group
        }

    def get_blacklist(self) -> dict:
        """Получение черного списка.

        Returns:
            dict: Словарь номеров {id: number}
        """
        blacklist_response = self.api.blacklist_list()
        return {
            item["id"]: item["number"]
            for item in blacklist_response.values()
            if isinstance(item, dict) and "number" in item
        }

    def get_contacts(self) -> dict:
        """Получение списка контактов.

        Returns:
            dict: Словарь контактов {id: number}
        """
        contacts_response = self.api.contact_list()
        return {
            item["id"]: str(item["number"])
            for item in contacts_response.values()
            if isinstance(item, dict) and "number" in item
        }


class Basic(Base):
    """Класс для выполнения базового тестового сценария."""

    def run(self):
        """Запуск базового тестового сценария."""
        logger.info(">> СМС <<")

        if PHONE_NUMBERS:
            logger.info("> Режим множественный <")
            self._run([int(number.strip()) for number in PHONE_NUMBERS.split(",")])
        else:
            logger.info("> Режим одиночный <")
            self._run(PHONE_NUMBER)

    def _validate_operator(self, operator_response):
        """Проверка ответа оператора."""
        if isinstance(operator_response, dict):
            if operator_response["extendOperator"] != "BEELINE":
                raise SMSAeroError("Неверный оператор")
        else:
            for op in operator_response:
                if op["extendOperator"] != "BEELINE":
                    raise SMSAeroError("Неверный оператор")

    def _check_tariff(self, tariff_response):
        """Проверка тарифа."""
        logger.info("Проверка, что тариф доступен")
        if "BEELINE" not in tariff_response["FREE SIGN"]:
            raise SMSAeroError("Тариф недоступен")

    def _check_number_in_lists(self, phone):
        """Проверка номера в списках."""
        logger.info("Проверка, что номер %s не в черном списке", phone)
        if str(PHONE_NUMBER) in list(self.get_blacklist().values()):
            raise BlackListError("Номер находится в черном списке")

        logger.info("Проверка, что номер %s не в контактах", phone)
        if str(PHONE_NUMBER) in list(self.get_contacts().values()):
            raise ContactError("Номер уже есть в контактах")

    def _handle_contacts(self, phone):
        """Обработка контактов."""
        logger.info("Добавление номера %s в контакты", phone)
        self.api.contact_add(phone)

        logger.info("Проверка, что номер %s добавился", phone)
        if str(phone) not in list(self.get_contacts().values()):
            raise ContactError("Номер не был добавлен в контакты")

        logger.info("Удаление номера %s из контактов", phone)
        self.api.contact_delete(list(self.get_contacts().keys())[0])

    def _wait_for_delivery(self, message_response, i=0):
        """Ожидание доставки сообщения."""
        logger.info("Ожидание доставки сообщения")
        if isinstance(message_response, dict):
            while message_response["extendStatus"] not in ["delivery", "undelivered"]:
                time.sleep(5)
                message_response = self.api.sms_status(message_response["id"])

                if i >= 120:
                    raise MessageError("Истекло время ожидания!")
        else:
            for res in message_response:
                while res["extendStatus"] not in ["delivery", "undelivered"]:
                    time.sleep(5)
                    res = self.api.sms_status(res["id"])

                    if i >= 120:
                        raise MessageError("Истекло время ожидания!")

    def _check_authorization(self):
        """Проверка авторизации."""
        logger.info("Проверка авторизации")
        if not self.api.is_authorized():
            raise AuthorizationError("Ошибка авторизации")

    def _check_balance(self):
        """Проверка баланса."""
        logger.info("Проверка баланса")
        balance_response = self.api.balance()
        if balance_response["balance"] <= 10:
            raise BalanceError("Недостаточно средств на балансе")
        logger.info("баланс: %s", balance_response["balance"])

    def _check_operator(self, number):
        """Проверка оператора."""
        logger.info("Получение оператора для проверки цены")
        operator_response = self.api.number_operator(number)
        self._validate_operator(operator_response)

    def _run(self, number: Union[int, List[int]]):
        """Запуск основного сценария тестирования."""
        numbers_list = number if isinstance(number, list) else [number]

        self._check_authorization()
        self._check_balance()
        self._check_operator(number)

        logger.info("Получение тарифа для номера")
        tariff_response = self.api.tariffs()

        self._check_tariff(tariff_response)

        for phone in numbers_list:
            self._check_number_in_lists(phone)

        if not self.api.is_test_mode_active():
            logger.info("Проверка доступности номера через HLR")
            hlr_response = self.api.hlr_check(number)

            logger.info("Ожидание, что номер доступен")
            if isinstance(hlr_response, dict):
                while hlr_response["extendHlrStatus"] != "available":
                    time.sleep(5)
                    hlr_response = self.api.hlr_status(hlr_response["id"])
            else:
                for res in hlr_response:
                    while res["extendHlrStatus"] != "available":
                        time.sleep(5)
                        res = self.api.hlr_status(res["id"])

        for phone in numbers_list:
            self._handle_contacts(phone)

        logger.info("Отправка сообщения %s", repr(number))
        message_response = self.api.send_sms(number, TEXT_MESSAGE)

        self._wait_for_delivery(message_response)

        logger.info("Проверка, что сообщение есть в списке ЛК")
        messages_response = self.api.sms_list(page=1)
        messages_list = [data for data in messages_response.values() if isinstance(data, dict) and "number" in data]
        message_list_ids = [message["id"] for message in messages_list]
        if isinstance(message_response, dict):
            if message_response["id"] not in message_list_ids:
                raise MessageError("Сообщение отсутствует в списке")
        else:
            for res in message_response:
                if res["id"] not in message_list_ids:
                    raise MessageError("Сообщение отсутствует в списке")


#####


class Group(Base):
    """Класс для тестирования функционала групп."""

    def run(self):
        """Запуск сценария тестирования групп."""
        logger.info(">> ГРУППЫ <<")

        logger.info("Проверка наличия группы")
        if GROUP_NAME in list(self.get_groups_list().values()):
            raise GroupError("Группа уже существует")

        logger.info("Добавление группы")
        self.api.group_add(GROUP_NAME)

        logger.info("Проверка, что группа добавилась")
        if GROUP_NAME not in list(self.get_groups_list().values()):
            raise GroupError("Группа не была добавлена")

        logger.info("Удаление группы")
        assert self.api.group_delete(list(self.get_groups_list().keys())[0])

        logger.info("Проверка, что группа удалена")
        if GROUP_NAME in list(self.get_groups_list().values()):
            raise GroupError("Группа не была удалена")


class BlackList(Base):
    """Класс для тестирования функционала черного списка."""

    def run(self):
        """Запуск сценария тестирования черного списка."""
        logger.info(">> ЧЕРНЫЙ СПИСОК <<")

        logger.info("Проверка наличия номера в черном списке")
        if str(PHONE_NUMBER) in list(self.get_blacklist().values()):
            raise BlackListError("Номер уже находится в черном списке")

        logger.info("Добавление номера в черный список")
        self.api.blacklist_add(PHONE_NUMBER)

        logger.info("Проверка, что номер добавился в черный список")
        if str(PHONE_NUMBER) not in list(self.get_blacklist().values()):
            raise BlackListError("Номер не был добавлен в черный список")

        logger.info("Удаление номера из черного списка")
        assert self.api.blacklist_delete(list(self.get_blacklist().keys())[0])

        logger.info("Проверка, что номер удален из черного списка")
        if str(PHONE_NUMBER) in list(self.get_blacklist().values()):
            raise BlackListError("Номер не был удален из черного списка")


class Contact(Base):
    """Класс для тестирования функционала контактов."""

    def run(self):
        """Запуск сценария тестирования контактов."""
        logger.info(">> КОНТАКТЫ <<")

        logger.info("Проверка наличия номера в контактах")
        if str(PHONE_NUMBER) in list(self.get_contacts().values()):
            raise ContactError("Номер уже существует в контактах")

        logger.info("Добавление номера в контакты")
        self.api.contact_add(PHONE_NUMBER)

        logger.info("Проверка, что номер добавился в контакты")
        if str(PHONE_NUMBER) not in list(self.get_contacts().values()):
            raise ContactError("Номер не был добавлен в контакты")

        logger.info("Удаление номера из контактов")
        assert self.api.contact_delete(list(self.get_contacts().keys())[0])

        logger.info("Проверка, что номер удален из контактов")
        if str(PHONE_NUMBER) in list(self.get_contacts().values()):
            raise ContactError("Номер не был удален из контактов")


def run():
    """Основная функция запуска всех тестовых сценариев."""

    api = smsaero.SmsAero(email=SMS_AERO_EMAIL, api_key=SMS_AERO_API_KEY)
    if TEST_MODE:
        logger.info(">>> Включен тестовый режим <<<")
        api.enable_test_mode()
    else:
        logger.info(">>> Выключен продакшен режим <<<")

    # Базовы сценарий
    Basic(api).run()

    # Если множественный режим, то не запускаем остальные сценарии
    if PHONE_NUMBER:
        # Группы
        Group(api).run()
        # Черный список
        BlackList(api).run()
        # Контакты
        Contact(api).run()

    # Выводим сообщение об успешном завершении сценария
    print(">>> Сценарий успешно завершен <<<")


if __name__ == "__main__":
    run()
