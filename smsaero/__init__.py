"""
This module provides the SmsAero class for interacting with the SMS Aero API.

The SmsAero class provides methods for sending SMS messages, checking the status of sent messages,
managing contacts, managing groups, managing the blacklist, and more.

Example:
    smsaero = SmsAero(email="your_email", api_key="your_api_key")
    smsaero.send_sms(number=70000000000, text="Hello, World!")

This module also provides several exception classes for handling errors that may occur when interacting with the API.

Classes:
    SmsAero: Provides methods for interacting with the SMS Aero API.
    SmsAeroException: The base class for all exceptions raised by this module.
    SmsAeroConnectionException: Raised when a connection error occurs.
    SmsAeroNoMoneyException: Raised when there is not enough money on the account to perform an operation.
"""

from typing import Union, List, Dict, Optional

import datetime
import logging
import time

from urllib.parse import urljoin, quote_plus, urlparse


from email_validator import validate_email, EmailNotValidError
from requests.models import Response
from requests import exceptions

import phonenumbers
import requests


__all__ = [
    "SmsAero",
    "SmsAeroException",
    "SmsAeroConnectionException",
    "SmsAeroNoMoneyException",
]


class SmsAeroException(Exception):
    """Super class of all SmsAero Errors."""


class SmsAeroConnectionException(SmsAeroException):
    """A Connection error occurred."""


class SmsAeroNoMoneyException(SmsAeroException):
    """No money on the account."""


logger = logging.getLogger(__name__)


class SmsAero:
    """
    The SmsAero class provides methods for interacting with the SmsAero API.

    This class provides methods for sending SMS messages, checking the status of sent messages,
    managing contacts, managing groups, managing the blacklist, and more.
    """

    # List of available gateway URLs
    GATE_URLS = [
        "@gate.smsaero.ru/v2/",
        "@gate.smsaero.org/v2/",
        "@gate.smsaero.net/v2/",
    ]
    # Default signature for the messages
    SIGNATURE = "SMS Aero"

    def __init__(
        self,
        email: str,
        api_key: str,
        signature: str = SIGNATURE,
        timeout: int = 15,
        allow_phone_validation: bool = True,
        url_gate: Optional[str] = None,
        test_mode: bool = False,
    ):
        """
        Initializes the SmsAero class.

        Parameters:
        email (str): The user's email.
        api_key (str): The user's API key. Should be 32 characters.
        signature (str, optional): The signature for the messages.
        timeout (int, optional): The timeout for the requests.
        allow_phone_validation (bool, optional): Whether to allow phone number validation.
        url_gate (str, optional): The gateway URL. For example, '@local.host/v2/'.
        test_mode (bool, optional): Whether to enable test mode.
        """
        self.__user = email
        self.__akey = api_key
        self.__gate = url_gate
        self.__sign = signature
        self.__sess = requests.session()
        self.__sess.headers.update({"User-Agent": "SAPythonClient/3.1.0"})
        self.__time = timeout
        self.__pnum = allow_phone_validation
        self.__resp: Optional[Response] = None
        self.__test = test_mode

        self.init_validate(
            email,
            api_key,
            signature,
            timeout,
            allow_phone_validation,
            url_gate,
            test_mode,
        )

        self.check_and_format_user_gate()

    def check_and_format_user_gate(self):
        """
        This method checks and formats the `self.__gate` attribute to ensure it starts with '@' and ends with '/v2/'.
        If `self.__gate` does not start with '@', it prepends '@' to it.
        If `self.__gate` does not end with '/v2/', it appends '/v2/' to it.
        The method does not return any value but modifies the `self.__gate` attribute in-place.
        """

        if not self.__gate:
            return

        parsed_url = urlparse(self.__gate)

        if not parsed_url.path.startswith("@"):
            parsed_url = parsed_url._replace(path="@" + parsed_url.path)
        if parsed_url.path.endswith("/v2"):
            parsed_url = parsed_url._replace(path=parsed_url.path + "/")
        elif not parsed_url.path.endswith("/v2/"):
            parsed_url = parsed_url._replace(path=parsed_url.path + "/v2/")

        self.__gate = parsed_url.geturl()

    def get_gate(self):
        """
        Returns the gateway URL.
        """
        return self.__gate

    def get_gate_urls(self) -> List[str]:
        """
        Returns a list of gateway URLs for sending requests.
        If a gateway URL was specified during initialization, it returns a list with only that URL.
        Otherwise, it returns a list of all available gateway URLs.
        """
        return [self.__gate] if self.__gate else self.GATE_URLS

    @staticmethod
    def fill_nums(number: Union[int, List[int]]) -> Dict:
        """
        Takes a number or a list of numbers as input.
        Returns:
        Dict: with the key as 'numbers' if input is a list, or 'number' if input is a single number.
        """
        if not number:
            raise ValueError("Number cannot be empty")
        return {"numbers" if isinstance(number, list) else "number": number}

    @staticmethod
    def check_response(response: Response) -> Dict:
        """
        Checks the response from the server.

        If the response contains an error message, it raises an appropriate exception.
        If the response is successful, it returns the data from the response.

        Parameters:
        response (Response): The response from the server.

        Returns:
        Dict: The data from the response if the request was successful.
        """
        try:
            content = response.json()
        except ValueError as e:
            raise SmsAeroException("Unexpected format is received") from e

        if content.get("result") == "no credits":
            raise SmsAeroNoMoneyException(content["result"])
        if content.get("result") == "reject":
            raise SmsAeroException(content["reason"])
        if not content.get("success"):
            raise SmsAeroException(content.get("message") or "Unknown error")

        return content.get("data")

    def build_url(self, proto: str, selector: str, gate: str, page: Optional[int] = None) -> str:
        """
        Builds a URL for the request.

        Parameters:
        proto (str): The protocol for the URL (e.g., 'http' or 'https').
        selector (str): The selector for the URL.
        gate (str): The gateway for the URL.
        page (Optional[int], optional): The page number for the URL.

        Returns:
        str: The built URL.
        """
        url = urljoin(f"{proto}://{quote_plus(self.__user)}:{self.__akey}{gate}", selector)
        if page:
            url = urljoin(url, f"?page={int(page)}")
        return url

    def get_response(self) -> Dict:
        """
        Retrieves the response from the server.

        Returns:
        Dict: The server's response in JSON format.
        """
        if not self.__resp:
            raise SmsAeroException("No response received")
        return self.__resp.json()

    def request(
        self,
        selector: str,
        data: Optional[Dict] = None,
        page: Optional[int] = None,
        proto: str = "https",
    ) -> Dict:
        """
        Sends a request to the server.

        Parameters:
        selector (str): The selector for the URL.
        data (Dict[str, Any], optional): The data to be sent in the request. If not specified, no data will be sent.
        page (int, optional): The page number for the URL. If not specified, no page number will be added to the URL.
        proto (str, optional): The protocol for the URL (e.g., 'http' or 'https'). Default is 'https'.

        Returns:
        Dict: The data from the response if the request was successful.
        """
        for gate in self.get_gate_urls():
            try:
                url = self.build_url(proto, selector, gate, page)
                logger.debug("Sending request to %s with data %s", url, data)
                self.__resp = self.__sess.post(url, json=data or {}, timeout=self.__time)
                logger.debug("Received response: %s", self.__resp.json())
                return self.check_response(self.__resp)
            except exceptions.SSLError:
                # switch to http when got ssl error
                proto = "http"
                continue
            except requests.RequestException:
                # next gate
                continue
        raise SmsAeroConnectionException

    def enable_test_mode(self):
        """
        Enables test mode.
        """
        self.__test = True

    def disable_test_mode(self):
        """
        Disables test mode.
        """
        self.__test = False

    def is_test_mode_active(self) -> bool:
        """
        Checks if test mode is active.

        Returns:
        bool: True if test mode is active, False otherwise.
        """
        return self.__test

    def is_authorized(self) -> bool:
        """
        Checks if the user is authorized.

        This method sends a request to the server to check if the user is authorized.
        It does not require any parameters.

        Returns:
        bool: True if the user is authorized or SmsAeroException if the user is not authorized.
        """
        return self.request("auth") is None

    def send_sms(
        self,
        number: Union[int, List[int]],
        text: str,
        sign: Optional[str] = None,
        date_to_send: Optional[datetime.datetime] = None,
        callback_url: Optional[str] = None,
    ) -> Dict:
        """
        Sends a message to the specified number or numbers.

        Parameters:
        number (Union[int, List[int]]): The recipient's phone number or a list of phone numbers.
        text (str): The text of the message.
        sign (str, optional): The signature for the message.
        date_to_send (datetime, optional): The date and time when the message should be sent.
        callback_url (str, optional): The URL to which the server will send a request when the message status changes.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "from": "SMS Aero",
            "number": "79031234567",
            "text": "Hello, World!",
            "status": 0,
            "extendStatus": "queue",
            "channel": "FREE SIGN",
            "cost": 5.49,
            "dateCreate": 1719119523,
            "dateSend": 1719119523
        }
        """
        self.send_sms_validate(number, text, sign, date_to_send, callback_url)
        data: Dict = {"text": text, "sign": sign or self.__sign, "callbackUrl": callback_url}
        data.update(**self.fill_nums(number))
        if date_to_send:
            data.update({"dateSend": int(time.mktime(date_to_send.timetuple()))})
        return self.request("sms/testsend" if self.__test else "sms/send", data)

    def sms_status(self, sms_id: int) -> Dict:
        """
        Retrieves the status of a specific SMS.

        Parameters:
        sms_id (int): The ID of the SMS.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "from": "SMS Aero",
            "number": "79031234567",
            "text": "Hello, World!",
            "status": 1,
            "extendStatus": "delivery",
            "channel": "FREE SIGN",
            "cost": "5.49",
            "dateCreate": 1719115820,
            "dateSend": 1719115820,
            "dateAnswer": 1719115825
        }
        """
        return self.request("sms/teststatus" if self.__test else "sms/status", {"id": int(sms_id)})

    def sms_list(
        self,
        number: Optional[Union[int, List[int]]] = None,
        text: Optional[str] = None,
        page: Optional[int] = None,
    ) -> Dict:
        """
        Retrieves a list of SMS messages.

        Parameters:
        number (Union[int, List[int]], optional): The recipient's phone number or a list of phone numbers.
        text (str, optional): The text of the message.
        page (int, optional): The page number for the URL.

        Returns:
        Dict: The server's response in JSON format.


        Example response:
        {
            "0": {
                "id": 12345,
                "from": "SMS Aero",
                "number": "79031234567",
                "text": "Hello, World!",
                "status": 1,
                "extendStatus": "delivery",
                "channel": "FREE SIGN",
                "cost": "5.49",
                "dateCreate": 1697533302,
                "dateSend": 1697533302,
                "dateAnswer": 1697533306
            },
            "1": {
            ...
            },
            ...
            "links": {
                "self": "/v2/sms/list?page=1",
                "first": "/v2/sms/list?page=1",
                "last": "/v2/sms/list?page=3",
                "next": "/v2/sms/list?page=2"
            },
            "totalCount": "138"
        }
        """
        self.sms_list_validate(number, text, page)
        data: Dict = {}
        if number:
            data.update(self.fill_nums(number))
        if text:
            data.update({"text": text})
        return self.request("sms/testlist" if self.__test else "sms/list", data, page)

    def balance(self) -> Dict:
        """
        Retrieves the balance of the user's account.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "balance": 337.03
        }
        """
        return self.request("balance")

    def balance_add(self, amount: float, card_id: int) -> Dict:
        """
        Adds a specified amount to the balance using a specified card.

        Parameters:
        amount (float): The amount to be added to the balance.
        card_id (int): The ID of the card to be used for the transaction.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "sum": 100
        }
        """
        return self.request("balance/add", {"sum": float(amount), "cardId": int(card_id)})

    def cards(self) -> Dict:
        """
        Retrieves the cards associated with the user's account.

        This method sends a request to the server to retrieve the cards associated with the user's account.
        It does not require any parameters.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "0": {
                "id": 12345,
                "number": Visa*****1234
            },
            "1": {
                "id": 12346,
                "number": MasterCard*****4321
            }
        }
        """
        return self.request("cards")

    def tariffs(self) -> Dict:
        """
        Retrieves the tariffs for the user's account.

        This method sends a request to the server to retrieve the tariffs for the user's account.
        It does not require any parameters.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "FREE SIGN": {
                "MEGAFON": "8.99",
                "MTS": "4.99",
                "BEELINE": "5.49",
                "TELE2": "4.79",
                "OTHER": "5.19"
            },
            ...
        }
        """
        return self.request("tariffs")

    def sign_list(self, page: Optional[int] = None) -> Dict:
        """
        Retrieves a list of signatures for the user's account.

        This method sends a request to the server to retrieve a list of signatures for the user's account.
        It accepts an optional parameter for pagination.

        Parameters:
        page (int, optional): The page number for the URL.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "totalCount": "1",
            "0": {
                "id": 12345,
                "name": "TestSign",
                "status": 1,
                "extendStatus": "approve",
                "statusOperators": {
                    "1": {
                        "operator": 1,
                        "extendOperator": "MEGAFON",
                        "status": 1,
                        "extendStatus": "approve"
                    },
                    "4": {
                        "operator": 4,
                        "extendOperator": "MTS",
                        "status": 1,
                        "extendStatus": "approve"
                    },
                    "5": {
                        "operator": 5,
                        "extendOperator": "BEELINE",
                        "status": 1,
                        "extendStatus": "approve"
                    },
                    "6": {
                        "operator": 6,
                        "extendOperator": "TELE2",
                        "status": 1,
                        "extendStatus": "approve"
                    }
                }
            }
        }
        """
        return self.request("sign/list", page=page)

    def group_add(self, name: str) -> Dict:
        """
        Adds a new group to the SmsAero service.

        Parameters:
        name (str): The name of the group to be added.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "name": "TestGroup",
            "count": 0
        }
        """
        return self.request("group/add", {"name": name})

    def group_delete(self, group_id: int) -> bool:
        """
        Deletes a group from the SmsAero service.

        Parameters:
        group_id (int): The ID of the group to be deleted.

        Returns:
        bool: True if deletion was successful, SmsAeroException if deletion was unsuccessful.
        """
        return self.request("group/delete", {"id": int(group_id)}) is None

    def group_delete_all(self) -> bool:
        """
        Deletes all group from the SmsAero service.

        Returns:
        bool: True if deletion was successful, SmsAeroException if deletion was unsuccessful.
        """
        return self.request("group/delete-all") is None

    def group_list(self, page: Optional[int] = None) -> Dict:
        """
        Retrieves a list of groups from the SmsAero service.

        Parameters:
        page (Optional[int], optional): The page number for the URL.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "0": {
                "id": "12345",
                "name": "test_group",
                "countContacts": "0"
            },
            ...,
            "links": {
                "self": "/v2/group/list?page=1",
                "first": "/v2/group/list?page=1",
                "last": "/v2/group/list?page=1"
            },
            "totalCount": "4"
        }
        """
        return self.request("group/list", page=page)

    def contact_add(
        self,
        number: Union[int, List[int]],
        group_id: Optional[int] = None,
        birthday: Optional[str] = None,
        sex: Optional[str] = None,
        last_name: Optional[str] = None,
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        param1: Optional[str] = None,
        param2: Optional[str] = None,
        param3: Optional[str] = None,
    ) -> Dict:
        """
        Adds a contact or a list of contacts to the user's account.

        Parameters:
        number (Union[int, List[int]]): The phone number or a list of phone numbers of the contacts.
        group_id (int, optional): The ID of the group to which the contacts belong.
        birthday (str, optional): The birthday of the contact.
        sex (str, optional): The sex of the contact.
        last_name (str, optional): The last name of the contact.
        first_name (str, optional): The first name of the contact.
        surname (str, optional): The surname of the contact.
        param1 (str, optional): The first custom parameter for the contact.
        param2 (str, optional): The second custom parameter for the contact.
        param3 (str, optional): The third custom parameter for the contact.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "number": "79031234567",
            "sex": "male",
            "lname": "Doe",
            "fname": "John",
            "sname": "Smith",
            "param1": "custom1",
            "param2": "custom2",
            "param3": "custom3",
            "operator": 5,
            "extendOperator": "BEELINE"
        }
        """

        self.contact_add_validate(
            number, group_id, birthday, sex, last_name, first_name, surname, param1, param2, param3
        )
        return self.request(
            "contact/add",
            {
                "number": number,
                "groupId": group_id and int(group_id),
                "birthday": birthday,
                "sex": sex,
                "lname": last_name,
                "fname": first_name,
                "sname": surname,
                "param1": param1,
                "param2": param2,
                "param3": param3,
            },
        )

    def contact_delete(self, contact_id: int) -> bool:
        """
        Deletes a contact from the user's account.

        Parameters:
        contact_id (int): The ID of the contact to be deleted.

        Returns:
        bool: True if deletion was successful, SmsAeroException if deletion was unsuccessful.
        """
        return self.request("contact/delete", {"id": int(contact_id)}) is None

    def contact_delete_all(self) -> bool:
        """
        Deletes all contacts from the user's account.

        Returns:
        bool: True if deletion was successful, SmsAeroException if deletion was unsuccessful.
        """
        return self.request("contact/delete-all") is None

    def contact_list(
        self,
        number: Optional[Union[int, List[int]]] = None,
        group_id: Optional[int] = None,
        birthday: Optional[str] = None,
        sex: Optional[str] = None,
        operator: Optional[str] = None,
        last_name: Optional[str] = None,
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        page: Optional[int] = None,
    ) -> Dict:
        """
        Retrieves a list of contacts from the user's account.

        Parameters:
        number (Optional[Union[int, List[int]]], optional): The phone number or a list of phone numbers of the contacts.
        group_id (int, optional): The ID of the group to which the contacts belong.
        birthday (str, optional): The birthday of the contact.
        sex (str, optional): The sex of the contact.
        operator (str, optional): The operator of the contact.
        last_name (str, optional): The last name of the contact.
        first_name (str, optional): The first name of the contact.
        surname (str, optional): The surname of the contact.
        page (int, optional): The page number for the URL.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "0": {
                "id": 12345,
                "number": 79031234567,
                "sex": "male",
                "lname": "Doe",
                "fname": "John",
                "sname": "Smith",
                "param1": "",
                "param2": "",
                "param3": "",
                "operator": 5,
                "extendOperator": "BEELINE",
                "groups": [
                    {
                        "id": 12345,
                        "name": "test_group"
                    }
                ],
                "hlrStatus": 1,
                "extendHlrStatus": "available"
            },
            ...,
            "links": {
                "self": "/v2/contact/list?page=1",
                "first": "/v2/contact/list?page=1",
                "last": "/v2/contact/list?page=1"
            },
            "totalCount": "5"
        }
        """

        self.contact_list_validate(number, group_id, birthday, sex, operator, last_name, first_name, surname, page)
        return self.request(
            "contact/list",
            {
                "number": number,
                "groupId": group_id and int(group_id),
                "birthday": birthday,
                "sex": sex,
                "operator": operator,
                "lname": last_name,
                "fname": first_name,
                "sname": surname,
            },
            page,
        )

    def blacklist_add(self, number: Union[int, List[int]]) -> Dict:
        """
        Adds a number or a list of numbers to the blacklist.

        Parameters:
        number (Union[int, List[int]]): The number or a list of numbers to be added to the blacklist.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "number": "79031234567",
            "sex": "male",
            "lname": "Doe",
            "fname": "John",
            "sname": "Smith",
            "bday": null,
            "param": null,
            "param2": null,
            "param3": null
        }
        """
        return self.request("blacklist/add", self.fill_nums(number))

    def blacklist_list(self, number: Optional[Union[int, List[int]]] = None, page: Optional[int] = None) -> Dict:
        """
        Retrieves a list of numbers from the blacklist.

        Parameters:
        number (Optional[Union[int, List[int]]], optional): The number or a list of numbers to be retrieved.
        page (Optional[int], optional): The page number for the URL.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "0": {
                "id": "12345",
                "number": "79031234567",
                "sex": "male",
                "lname": "Doe",
                "fname": "John",
                "sname": "Smith",
                "bday": null,
                "param": null,
                "param2": null,
                "param3": null
            },
            "links": {
                "self": "/v2/blacklist/list?page=1",
                "first": "/v2/blacklist/list?page=1",
                "last": "/v2/blacklist/list?page=1"
            },
            "totalCount": "1"
        }
        """
        return self.request("blacklist/list", self.fill_nums(number) if number else None, page)

    def blacklist_delete(self, blacklist_id: int) -> bool:
        """
        Deletes a number from the blacklist.

        Parameters:
        blacklist_id (int): The ID of the number to be deleted from the blacklist.

        Returns:
        bool: True if deletion was successful, SmsAeroException if deletion was unsuccessful.
        """
        return self.request("blacklist/delete", {"id": int(blacklist_id)}) is None

    def hlr_check(self, number: Union[int, List[int]]) -> Dict:
        """
        Checks the Home Location Register (HLR) for a number or a list of numbers.

        Parameters:
        number (Union[int, List[int]]): The number or a list of numbers to be checked.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "number": "79031234567",
            "hlrStatus": 4,
            "extendHlrStatus": "in work"
        }
        """
        return self.request("hlr/check", self.fill_nums(number))

    def hlr_status(self, hlr_id: int) -> Dict:
        """
        Retrieves the status of a specific HLR check.

        Parameters:
        hlr_id (int): The ID of the HLR check.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "number": "79031234567",
            "hlrStatus": 1,
            "extendHlrStatus": "available"
        }
        """
        return self.request("hlr/status", {"id": int(hlr_id)})

    def number_operator(self, number: Union[int, List[int]]) -> Dict:
        """
        Retrieves the operator of a number or a list of numbers.

        Parameters:
        number (Union[int, List[int]]): The number or a list of numbers.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "number": "79031234567",
            "operator": 5,
            "extendOperator": "BEELINE"
        }
        """
        return self.request("number/operator", self.fill_nums(number))

    def viber_send(
        self,
        sign: str,
        channel: str,
        text: str,
        number: Optional[Union[int, List[int]]] = None,
        group_id: Optional[int] = None,
        image_source: Optional[str] = None,
        text_button: Optional[str] = None,
        link_button: Optional[str] = None,
        date_send: Optional[str] = None,
        sign_sms: Optional[str] = None,
        channel_sms: Optional[str] = None,
        text_sms: Optional[str] = None,
        price_sms: Optional[int] = None,
    ) -> Dict:
        """
        Sends a Viber message.

        Parameters:
        sign (str): The signature of the message.
        channel (str): The channel of the message.
        text (str): The text of the message.
        number (Union[int, List[int]], optional): The phone number or a list of phone numbers to send the message to.
        group_id (int, optional): The ID of the group to send the message to.
        image_source (str, optional): The source of the image in the message.
        text_button (str, optional): The text of the button in the message.
        link_button (str, optional): The link of the button in the message.
        date_send (str, optional): The date to send the message.
        sign_sms (str, optional): The signature of the SMS fallback.
        channel_sms (str, optional): The channel of the SMS fallback.
        text_sms (str, optional): The text of the SMS fallback.
        price_sms (int, optional): The price of the SMS fallback.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 12345,
            "number": "79031234567",
            "count": 1,
            "sign": "Viber",
            "channel": "OFFICIAL",
            "text": "Hello, World!",
            "cost": 2.25,
            "status": 1,
            "extendStatus": "moderation",
            "dateCreate": 1511153253,
            "dateSend": 1511153253,
            "countSend": 0,
            "countDelivered": 0,
            "countWrite": 0,
            "countUndelivered": 0,
            "countError": 0
        }
        """

        self.viber_send_validate(
            sign,
            channel,
            text,
            number,
            group_id,
            image_source,
            text_button,
            link_button,
            date_send,
            sign_sms,
            channel_sms,
            text_sms,
            price_sms,
        )

        data = {
            "groupId": group_id and int(group_id),
            "sign": sign and str(sign),
            "channel": channel and str(channel),
            "text": text,
            "imageSource": image_source,
            "textButton": text_button,
            "linkButton": link_button,
            "dateSend": date_send,
            "signSms": sign_sms,
            "channelSms": channel_sms,
            "textSms": text_sms,
            "priceSms": price_sms,
        }
        if number:
            data.update(self.fill_nums(number))
        return self.request("viber/send", data)

    def viber_sign_list(self) -> Dict:
        """
        Retrieves a list of Viber signs.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "0": {
                "id": 12345,
                "name": "GOOD SIGN",
                "status": 1,
                "extendStatus": "active",
                "statusOperators": {
                    "1": {
                        "operator": 1,
                        "extendOperator": "MEGAFON",
                        "status": 0,
                        "extendStatus": "moderation"
                    },
                    ....
                }
            },
            ...
        }
        """
        return self.request("viber/sign/list")

    def viber_list(self, page: Optional[int] = None) -> Dict:
        """
        Retrieves a list of Viber messages.

        Parameters:
        page (int, optional): The page number for the URL.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            0: {
                "id": 1,
                "number": "79031234567",
                "count": 1,
                "sign": "Viber",
                "channel": "OFFICIAL",
                "text": "Hello, World!",
                "cost": 2.25,
                "status": 1,
                "extendStatus": "moderation",
                "dateCreate": 1511153253,
                "dateSend": 1511153253,
                "countSend": 0,
                "countDelivered": 0,
                "countWrite": 0,
                "countUndelivered": 0,
                "countError": 0
            },
            ...
            "links": {
                "self": "/v2/viber/list?page=1",
                "next": "/v2/viber/list?page=2",
                "last": "/v2/viber/list?page=3"
            }
        """
        self.page_validate(page)
        return self.request("viber/list", page=page)

    def viber_statistics(self, sending_id: int, page: Optional[int] = None) -> Dict:
        """
        Retrieves the statistics for a specific Viber message.

        Parameters:
        sending_id (int): The ID of the Viber message.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            0: {
                "number": "79031234567",
                "status": 0,
                "extendStatus": "send",
                "dateSend": 1511153341
            },
            1: {
                "number": "79031234568",
                "status": 2,
                "extendStatus": "write",
                "dateSend": 1511153341
            },
            "links": {
                "self": "/v2/viber/statistic?sendingId=1&page=1"
            }
        }
        """
        self.page_validate(page)
        return self.request("viber/statistic", {"sendingId": int(sending_id)}, page=page)

    def send_telegram(
        self,
        number: Union[int, List[int]],
        code: int,
        sign: Optional[str] = None,
        text: Optional[str] = None,
    ) -> Dict:
        """
        Sends a Telegram code to the specified number or numbers.

        Parameters:
        number (Union[int, List[int]]): The recipient's phone number or a list of phone numbers.
        code (int): The Telegram code (4 to 8 digits).
        sign (str, optional): The SMS sender name.
        text (str, optional): The SMS message text.

        When using text and sign parameters, if the Telegram code is not delivered,
        an SMS will be sent with the specified values.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 1,
            "number": "79990000000",
            "telegramCode": "1234",
            "smsText": "Ваш код 1234",
            "smsFrom": "SMS Aero",
            "idSms": null,
            "status": 0,
            "extendStatus": "queue",
            "cost": "1.00",
            "dateCreate": 1732796285
        }
        """
        self.send_telegram_validate(number, code, sign, text)
        data: Dict = {"code": int(code)}
        data.update(**self.fill_nums(number))
        if sign:
            data["sign"] = sign
        if text:
            data["text"] = text
        return self.request("telegram/send", data)

    def telegram_status(self, telegram_id: int) -> Dict:
        """
        Retrieves the status of a Telegram code delivery.

        Parameters:
        telegram_id (int): The message ID returned by the service when sending.

        Returns:
        Dict: The server's response in JSON format.

        Example response:
        {
            "id": 1,
            "number": "79990000000",
            "telegramCode": "1234",
            "smsText": "Ваш код 1234",
            "smsFrom": "SMS Aero",
            "idSms": null,
            "status": 1,
            "extendStatus": "delivery",
            "cost": "1.00",
            "dateCreate": 1732796285
        }
        """
        return self.request("telegram/status", {"id": int(telegram_id)})

    def phone_validation(self, number: Union[int, List[int]]) -> None:
        """
        Validates the phone number or a list of phone numbers.

        If number is of type int or a list of ints and if it is within the valid length range (7 to 15).
        If number is not of type int or a list of ints, or is not within the valid length range, it raises exception.

        Parameters:
        number (Union[int, List[int]]): The phone number or a list of phone numbers to validate.

        Raises:
        TypeError: If the number is not of type int or a list of ints.
        ValueError: If the number is not within the valid length range.
        """
        if not isinstance(number, (int, list)):
            raise TypeError("number must be an integer or a list of integers")
        if isinstance(number, int) and not 7 <= len(str(number)) <= 15:
            raise ValueError("Length of number must be between 7 and 15")
        if isinstance(number, list) and any(not (7 <= len(str(num)) <= 15) for num in number):
            raise ValueError("Length of each number in the list must be between 7 and 15")
        if isinstance(number, list) and any(not isinstance(num, int) for num in number):
            raise ValueError("Type of each number in the list must be integer")

        # Validate phone numbers by phonenumbers library only if it is allowed
        if self.__pnum:
            self.phonenumbers_validate(number)

    @staticmethod
    def phonenumbers_validate(number: Union[int, List[int]]) -> None:
        """
        Validates the phone number or a list of phone numbers using the phonenumbers library.

        This function checks if the number is of type int or a list of ints and if it is a valid phone number.
        If number is not a valid number, it raises an appropriate exception.

        Parameters:
        number (Union[int, List[int]]): The phone number or a list of phone numbers to validate.

        Raises:
        TypeError: If the number is not of type int or a list of ints.
        ValueError: If the number is not a valid phone number.
        """
        if isinstance(number, list):
            for num in number:
                try:
                    parsed_number = phonenumbers.parse("+" + str(num), None)
                    if not phonenumbers.is_valid_number(parsed_number):
                        raise ValueError("Each number in the list must be a valid phone number")
                except phonenumbers.phonenumberutil.NumberParseException as e:
                    raise ValueError("Each number in the list must be a valid phone number!") from e
        else:
            try:
                parsed_number = phonenumbers.parse("+" + str(number), None)
                if not phonenumbers.is_valid_number(parsed_number):
                    raise ValueError("Number must be a valid phone number")
            except phonenumbers.phonenumberutil.NumberParseException as e:
                raise ValueError("Number must be a valid phone number!") from e

    @staticmethod
    def page_validate(page: Optional[int]) -> None:
        """
        Validates the page parameter.

        This function checks if the page is of type int and if it is greater than 0.
        If the page is not of type int or is less than or equal to 0, it raises an appropriate exception.

        Parameters:
        page (Optional[int]): The page number to validate.

        Raises:
        ValueError: If any of the parameters are invalid.
        TypeError: If any of the parameters have an incorrect type.
        """
        if page is not None:
            if not isinstance(page, int):
                raise TypeError("page must be an integer")
            if page <= 0:
                raise ValueError("page must be greater than 0")

    def send_sms_validate(
        self,
        number: Union[int, List[int]],
        text: str,
        sign: Optional[str] = None,
        date_to_send: Optional[datetime.datetime] = None,
        callback_url: Optional[str] = None,
    ) -> None:
        """
        Validates the parameters for the send_sms method.

        Parameters:
        number (Union[int, List[int]]): The recipient's phone number or a list of phone numbers.
        text (str): The text of the message.
        sign (str, optional): The signature of the message.
        date_to_send (datetime, optional): The date to send the message.
        callback_url (str, optional): The callback URL for the message status.

        Raises:
        TypeError: If any of the parameters have an incorrect type.
        ValueError: If any of the parameters have an incorrect value.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not 2 <= len(text) <= 640:
            raise ValueError("Length of text must be between 2 and 640")
        if sign is not None and not isinstance(sign, str):
            raise TypeError("sign must be a string")
        if date_to_send is not None and not isinstance(date_to_send, datetime.datetime):
            raise TypeError("date_to_send must be a datetime object")
        if callback_url is not None and not isinstance(callback_url, str):
            raise TypeError("callback_url must be a string")
        if callback_url is not None:
            parsed_url = urlparse(callback_url)
            if not all([parsed_url.scheme, parsed_url.netloc, parsed_url.path]):
                raise ValueError("callback_url must be a valid URL")

        self.phone_validation(number)

    def sms_list_validate(
        self,
        number: Optional[Union[int, List[int]]] = None,
        text: Optional[str] = None,
        page: Optional[int] = None,
    ) -> None:
        """
        Validates the parameters for the sms_list method.

        Parameters:
        number (Union[int, List[int]], optional): The recipient's phone number or a list of phone numbers.
        text (str, optional): The text of the message.
        page (int, optional): The page number for the URL.

        Raises:
        TypeError: If any of the parameters have an incorrect type.
        ValueError: If any of the parameters have an incorrect value.
        """
        if number:
            self.phone_validation(number)
        if text is not None and not isinstance(text, str):
            raise TypeError("text must be a string")
        self.page_validate(page)

    def viber_send_validate(
        self,
        sign: str,
        channel: str,
        text: str,
        number: Optional[Union[int, List[int]]] = None,
        group_id: Optional[int] = None,
        image_source: Optional[str] = None,
        text_button: Optional[str] = None,
        link_button: Optional[str] = None,
        date_send: Optional[str] = None,
        sign_sms: Optional[str] = None,
        channel_sms: Optional[str] = None,
        text_sms: Optional[str] = None,
        price_sms: Optional[int] = None,
    ) -> None:
        """
        Validates the parameters for the viber_send method.

        Parameters:
        number (Union[int, List[int]]): The recipient's phone number or a list of phone numbers.
        text (str): The text of the message.
        sign (str, optional): The signature of the message.
        channel (str, optional): The channel of the message.
        group_id (int, optional): The ID of the group to send the message to.
        image_source (str, optional): The source of the image in the message.
        text_button (str, optional): The text of the button in the message.
        link_button (str, optional): The link of the button in the message.
        date_send (str, optional): The date to send the message.
        sign_sms (str, optional): The signature of the SMS fallback.
        channel_sms (str, optional): The channel of the SMS fallback.
        text_sms (str, optional): The text of the SMS fallback.
        price_sms (int, optional): The price of the SMS fallback.

        Raises:
        TypeError: If any of the parameters have an incorrect type.
        ValueError: If any of the parameters have an incorrect value.
        """
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")
        if not 2 <= len(text) <= 640:
            raise ValueError("Text length must be between 2 and 640 characters.")
        if sign is not None and not isinstance(sign, str):
            raise TypeError("Sign must be a string.")
        if sign is not None and not 2 <= len(sign) <= 64:
            raise ValueError("Sign length must be between 2 and 64 characters.")
        if channel is not None and not isinstance(channel, str):
            raise TypeError("Channel must be a string.")
        if group_id is not None and not isinstance(group_id, int):
            raise TypeError("Group ID must be an integer.")
        if image_source is not None and not isinstance(image_source, str):
            raise TypeError("Image source must be a string.")
        if text_button is not None and not isinstance(text_button, str):
            raise TypeError("Text button must be a string.")
        if link_button is not None and not isinstance(link_button, str):
            raise TypeError("Link button must be a string.")
        if date_send is not None and not isinstance(date_send, str):
            raise TypeError("Date send must be a string.")
        if sign_sms is not None and not isinstance(sign_sms, str):
            raise TypeError("Sign SMS must be a string.")
        if channel_sms is not None and not isinstance(channel_sms, str):
            raise TypeError("Channel SMS must be a string.")
        if text_sms is not None and not isinstance(text_sms, str):
            raise TypeError("Text SMS must be a string.")
        if price_sms is not None and not isinstance(price_sms, int):
            raise TypeError("Price SMS must be an integer.")
        if number is not None:
            self.phone_validation(number)

    def contact_add_validate(
        self,
        number: Union[int, List[int]],
        group_id: Optional[int] = None,
        birthday: Optional[str] = None,
        sex: Optional[str] = None,
        last_name: Optional[str] = None,
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        param1: Optional[str] = None,
        param2: Optional[str] = None,
        param3: Optional[str] = None,
    ) -> None:
        """
        Validates the parameters for the contact_add method.

        Parameters:
        number (Union[int, List[int]]): The phone number or a list of phone numbers of the contacts.
        group_id (int, optional): The ID of the group to which the contacts belong.
        birthday (str, optional): The birthday of the contact.
        sex (str, optional): The sex of the contact.
        last_name (str, optional): The last name of the contact.
        first_name (str, optional): The first name of the contact.
        surname (str, optional): The surname of the contact.
        param1 (str, optional): The first custom parameter for the contact.
        param2 (str, optional): The second custom parameter for the contact.
        param3 (str, optional): The third custom parameter for the contact.

        Raises:
        TypeError: If any of the parameters have an incorrect type.
        ValueError: If any of the parameters have an incorrect value.
        """
        if number is not None:
            self.phone_validation(number)
        if group_id is not None and not isinstance(group_id, int):
            raise TypeError("Group ID must be an integer.")
        if birthday is not None and not isinstance(birthday, str):
            raise TypeError("Birthday must be a string.")
        if sex is not None and not isinstance(sex, str):
            raise TypeError("Sex must be a string.")
        if last_name is not None and not isinstance(last_name, str):
            raise TypeError("Last name must be a string.")
        if first_name is not None and not isinstance(first_name, str):
            raise TypeError("First name must be a string.")
        if surname is not None and not isinstance(surname, str):
            raise TypeError("Surname must be a string.")
        if param1 is not None and not isinstance(param1, str):
            raise TypeError("Param1 must be a string.")
        if param2 is not None and not isinstance(param2, str):
            raise TypeError("Param2 must be a string.")
        if param3 is not None and not isinstance(param3, str):
            raise TypeError("Param3 must be a string.")

    def contact_list_validate(
        self,
        number: Optional[Union[int, List[int]]] = None,
        group_id: Optional[int] = None,
        birthday: Optional[str] = None,
        sex: Optional[str] = None,
        operator: Optional[str] = None,
        last_name: Optional[str] = None,
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        page: Optional[int] = None,
    ) -> None:
        """
        Validates the parameters for the contact_list method.

        Parameters:
        number (Union[int, List[int]], optional): The phone number or a list of phone numbers of the contacts.
        group_id (int, optional): The ID of the group to which the contacts belong.
        birthday (str, optional): The birthday of the contact.
        sex (str, optional): The sex of the contact.
        operator (str, optional): The operator of the contact.
        last_name (str, optional): The last name of the contact.
        first_name (str, optional): The first name of the contact.
        surname (str, optional): The surname of the contact.
        page (int, optional): The page number for the URL.

        Raises:
        TypeError: If any of the parameters have an incorrect type.
        ValueError: If any of the parameters have an incorrect value.
        """
        if number:
            self.phone_validation(number)
        if group_id is not None and not isinstance(group_id, int):
            raise TypeError("Group ID must be an integer.")
        if birthday is not None and not isinstance(birthday, str):
            raise TypeError("Birthday must be a string.")
        if sex is not None and not isinstance(sex, str):
            raise TypeError("Sex must be a string.")
        if operator is not None and not isinstance(operator, str):
            raise TypeError("Operator must be a string.")
        if last_name is not None and not isinstance(last_name, str):
            raise TypeError("Last name must be a string.")
        if first_name is not None and not isinstance(first_name, str):
            raise TypeError("First name must be a string.")
        if surname is not None and not isinstance(surname, str):
            raise TypeError("Surname must be a string.")
        self.page_validate(page)

    def send_telegram_validate(
        self,
        number: Union[int, List[int]],
        code: int,
        sign: Optional[str] = None,
        text: Optional[str] = None,
    ) -> None:
        """
        Validates the parameters for the send_telegram method.

        Parameters:
        number (Union[int, List[int]]): The recipient's phone number or a list of phone numbers.
        code (int): The Telegram code (4 to 8 digits).
        sign (str, optional): The SMS sender name.
        text (str, optional): The SMS message text.

        Raises:
        TypeError: If any of the parameters have an incorrect type.
        ValueError: If any of the parameters have an incorrect value.
        """
        if not isinstance(code, int):
            raise TypeError("Code must be an integer")
        if not 4 <= len(str(code)) <= 8:
            raise ValueError("Code length must be between 4 and 8 digits")
        if sign is not None and not isinstance(sign, str):
            raise TypeError("Sign must be a string")
        if sign is not None and not 2 <= len(sign) <= 64:
            raise ValueError("Sign length must be between 2 and 64 characters")
        if text is not None and not isinstance(text, str):
            raise TypeError("Text must be a string")
        if text is not None and not 2 <= len(text) <= 640:
            raise ValueError("Text length must be between 2 and 640 characters")

        self.phone_validation(number)

    @staticmethod
    def init_validate(
        email: str,
        api_key: str,
        signature: str = SIGNATURE,
        timeout: int = 15,
        allow_phone_validation: bool = True,
        url_gate: Optional[str] = None,
        test_mode: bool = False,
    ) -> None:
        """
        Validates the parameters for the __init__ method of the `SmsAero` class.

        Parameters:
        email (str): A string representing the user's email.
        @api_key (str): A string representing the API key for the SmsAero service. Should be 32 characters.
        signature (str): A string representing the signature for the SmsAero service.
        timeout (int): An integer representing the timeout for requests to the SmsAero service.
        allow_phone_validation (bool): A boolean indicating whether phone number validation is allowed.
        url_gate (str): A string representing the URL gate for the SmsAero service.
        test_mode (bool): A boolean indicating whether test mode is active.

        Raises:
        ValueError: If any of the parameters are invalid.
        TypeError: If any of the parameters have an incorrect type.
        """
        try:
            validate_email(email)
        except EmailNotValidError as e:
            raise ValueError(str(e)) from e
        if not isinstance(api_key, str):
            raise TypeError("API key must be a string.")
        if not 16 <= len(api_key) <= 32:
            raise ValueError("API key length must be between 20 and 32 characters.")
        if not isinstance(signature, str):
            raise TypeError("Signature must be a string.")
        if len(signature) < 2:
            raise ValueError("Signature length must be at least 2 characters.")
        if not isinstance(timeout, int):
            raise TypeError("Timeout must be an integer.")
        if timeout <= 2:
            raise ValueError("Timeout must be a positive integer.")
        if not isinstance(allow_phone_validation, bool):
            raise TypeError("Allow phone validation must be a boolean.")
        if url_gate is not None and not isinstance(url_gate, str):
            raise TypeError("URL gate must be a string.")
        if not isinstance(test_mode, bool):
            raise TypeError("Test mode must be a boolean.")
