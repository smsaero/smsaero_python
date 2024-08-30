from typing import Union, List

import logging
import time
import os

import smsaero

SMSAERO_EMAIL = os.getenv("SMSAERO_EMAIL")
SMSAERO_API_KEY = os.getenv("SMSAERO_API_KEY")
PHONE_NUMBER = os.getenv("PHONE_NUMBER") and int(os.getenv("PHONE_NUMBER"))
PHONE_NUMBERS = os.getenv("PHONE_NUMBERS")
TEXT_MESSAGE = os.getenv("TEXT_MESSAGE", "Hello, World!")
TEST_MODE = bool(int(os.getenv("TEST_MODE", "0")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
GROUP_NAME = "test_group"


log_level = logging.DEBUG if LOG_LEVEL == "DEBUG" else logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
logger.addHandler(logging.StreamHandler())

smsaero_logger = logging.getLogger("smsaero")
smsaero_logger.setLevel(log_level)
smsaero_logger.addHandler(logging.StreamHandler())


class Base:
    def __init__(self, api):
        self.api = api

    def get_groups_list(self):
        group_list_response = self.api.group_list()
        return {
            group["id"]: group["name"]
            for group in group_list_response.values()
            if isinstance(group, dict) and "name" in group
        }

    def get_blacklist(self):
        blacklist_response = self.api.blacklist_list()
        return {
            item["id"]: item["number"]
            for item in blacklist_response.values()
            if isinstance(item, dict) and "number" in item
        }

    def get_contacts(self):
        contacts_response = self.api.contact_list()
        return {
            item["id"]: str(item["number"])
            for item in contacts_response.values()
            if isinstance(item, dict) and "number" in item
        }


class Basic(Base):
    def run(self):
        logger.info(">> СМС <<")

        if PHONE_NUMBERS:
            logger.info("> Режим множественный <")
            self._run([int(number.strip()) for number in PHONE_NUMBERS.split(",")])
        else:
            logger.info("> Режим одиночный <")
            self._run(PHONE_NUMBER)

    def _run(self, number: Union[int, List[int]]):
        numbers_list = number if isinstance(number, list) else [number]

        logger.info("Проверка авторизации")
        if not self.api.is_authorized():
            raise Exception("Authorization failed")

        logger.info("Проверка баланса")
        balance_response = self.api.balance()
        if balance_response["balance"] <= 10:
            raise Exception("Balance is not positive")
        else:
            logger.info("баланс: " + str(balance_response["balance"]))

        logger.info("Получение оператора для проверки цены")
        operator_response = self.api.number_operator(number)
        if isinstance(operator_response, dict):
            assert operator_response["extendOperator"] == "BEELINE"
        else:
            for op in operator_response:
                assert op["extendOperator"] == "BEELINE"

        logger.info("Получение тарифа для номера")
        tariff_response = self.api.tariffs()

        logger.info("Проверка, что тариф доступен")
        if "BEELINE" not in tariff_response["FREE SIGN"]:
            raise Exception("Tariff is not available")

        for phone in numbers_list:
            logger.info(f"Проверка, что номер {phone} не в черном списке")
            if str(PHONE_NUMBER) in list(self.get_blacklist().values()):
                raise Exception("Number is in the blacklist")

            logger.info(f"Проверка, что номер {phone} не в контактах")
            if str(PHONE_NUMBER) in list(self.get_contacts().values()):
                raise Exception("Number is in the contacts")

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
            logger.info(f"Добавление номера {phone} в контакты")
            self.api.contact_add(phone)

            logger.info(f"Проверка, что номер {phone} добавился")
            if str(phone) not in list(self.get_contacts().values()):
                raise Exception("Number was not added to contacts")

            logger.info(f"Удаление номера {phone} из контактов")
            self.api.contact_delete(list(self.get_contacts().keys())[0])

        logger.info("Отправка сообщения " + repr(number))
        message_response = self.api.send_sms(number, TEXT_MESSAGE)

        logger.info("Ожидание, что сообщение доставлено")
        if isinstance(message_response, dict):
            while message_response["extendStatus"] != "delivery":
                time.sleep(5)
                message_response = self.api.sms_status(message_response["id"])
        else:
            for res in message_response:
                while res["extendStatus"] != "delivery":
                    time.sleep(5)
                    res = self.api.sms_status(res["id"])

        logger.info("Проверка, что сообщение есть в списке ЛК")
        messages_response = self.api.sms_list(page=1)
        messages_list = [data for data in messages_response.values() if isinstance(data, dict) and "number" in data]
        message_list_ids = [message["id"] for message in messages_list]
        if isinstance(message_response, dict):
            if message_response["id"] not in message_list_ids:
                raise Exception("Message is not in the list")
        else:
            for res in message_response:
                if res["id"] not in message_list_ids:
                    raise Exception("Message is not in the list")


#####


class Group(Base):
    def run(self):
        logger.info(">> ГРУППЫ <<")

        logger.info("Проверка наличия группы")
        if GROUP_NAME in list(self.get_groups_list().values()):
            raise Exception("Group already exists")

        logger.info("Добавление группы")
        self.api.group_add(GROUP_NAME)

        logger.info("Проверка, что группа добавилась")
        if GROUP_NAME not in list(self.get_groups_list().values()):
            raise Exception("Group was not added")

        logger.info("Удаление группы")
        assert self.api.group_delete(list(self.get_groups_list().keys())[0])

        logger.info("Проверка, что группа удалена")
        if GROUP_NAME in list(self.get_groups_list().values()):
            raise Exception("Group was not deleted")


class BlackList(Base):
    def run(self):
        logger.info(">> ЧЕРНЫЙ СПИСОК <<")

        logger.info("Проверка наличия номера в черном списке")
        if str(PHONE_NUMBER) in list(self.get_blacklist().values()):
            raise Exception("Number is already in the blacklist")

        logger.info("Добавление номера в черный список")
        self.api.blacklist_add(PHONE_NUMBER)

        logger.info("Проверка, что номер добавился в черный список")
        if str(PHONE_NUMBER) not in list(self.get_blacklist().values()):
            raise Exception("Number was not added to the blacklist")

        logger.info("Удаление номера из черного списка")
        assert self.api.blacklist_delete(list(self.get_blacklist().keys())[0])

        logger.info("Проверка, что номер удален из черного списка")
        if str(PHONE_NUMBER) in list(self.get_blacklist().values()):
            raise Exception("Number was not removed from the blacklist")


class Contact(Base):
    def run(self):
        logger.info(">> КОНТАКТЫ <<")

        logger.info("Проверка наличия номера в контактах")
        if str(PHONE_NUMBER) in list(self.get_contacts().values()):
            raise Exception("Number is already in the contacts")

        logger.info("Добавление номера в контакты")
        self.api.contact_add(PHONE_NUMBER)

        logger.info("Проверка, что номер добавился в контакты")
        if str(PHONE_NUMBER) not in list(self.get_contacts().values()):
            raise Exception("Number was not added to the contacts")

        logger.info("Удаление номера из контактов")
        assert self.api.contact_delete(list(self.get_contacts().keys())[0])

        logger.info("Проверка, что номер удален из контактов")
        if str(PHONE_NUMBER) in list(self.get_contacts().values()):
            raise Exception("Number was not removed from the contacts")


def run():
    # Создаем экземпляр класса SmsAero
    api = smsaero.SmsAero(email=SMSAERO_EMAIL, api_key=SMSAERO_API_KEY)
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
