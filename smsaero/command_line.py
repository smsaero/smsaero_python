"""
This module provides a command line interface for sending SMS messages via SmsAero.
"""

import argparse
import pprint
import typing
import sys

from smsaero import SmsAero, SmsAeroException


def send_sms(email: str, api_key: str, phone: int, message: str) -> typing.Optional[dict]:
    """
    Sends an SMS message via SmsAero.

    :param email: The email registered with SmsAero.
    :param api_key: The API key from SmsAero.
    :param phone: The phone number to send the SMS message to.
    :param message: The text of the message to be sent.
    :return: Returns a dictionary with the response data from SmsAero, or None if the message was not sent.
    """
    api = SmsAero(email, api_key)
    return api.send_sms(phone, message)


def main() -> None:
    """
    Parses command line arguments and sends an SMS message via SmsAero.

    The command line arguments are:
    --email: The email registered with SmsAero.
    --api_key: The API key from SmsAero.
    --phone: The phone number to send the SMS message to.
    --message: The text of the message to be sent.

    If the SMS message is sent successfully, the response data from SmsAero is printed.
    If an error occurs, the error message is printed and the program exits with status code 1.
    """
    parser = argparse.ArgumentParser(description="Send SMS via smsaero.ru gate")
    parser.add_argument("--email", type=str, required=True, help="Your email registered with SmsAero")
    parser.add_argument("--api_key", type=str, required=True, help="Your SmsAero API key")
    parser.add_argument("--phone", type=int, required=True, help="Phone number to send SMS to")
    parser.add_argument("--message", type=str, required=True, help="Message to send")

    args = parser.parse_args()

    try:
        result = send_sms(args.email, args.api_key, args.phone, args.message)
        pprint.pprint(result)
    except SmsAeroException as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
