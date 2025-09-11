"""
This module provides a command line interface for sending SMS messages via SmsAero.

Example usage:
    python -m smsaero.command_line --email YOUR_EMAIL --api_key YOUR_API_KEY --phone 70000000000 --message "Hello"
"""

import argparse
import logging
import pprint
import sys
from typing import Dict, Optional

from smsaero import SmsAero, SmsAeroException


logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def send_sms(email: str, api_key: str, phone: int, message: str) -> Optional[Dict]:
    """
    Sends an SMS message via SmsAero.

    Args:
        email: The email registered with SmsAero
        api_key: The API key from SmsAero
        phone: The phone number to send the SMS message to
        message: The text of the message to be sent

    Returns:
        Optional[Dict]: Response data from SmsAero if successful, None otherwise

    Raises:
        SmsAeroException: If there's an error with the SmsAero service
        ValueError: If input validation fails
        ConnectionError: If there's a network connectivity issue
    """
    logger.info("Attempting to send SMS to %s", phone)

    try:
        api = SmsAero(email, api_key)
        response = api.send_sms(phone, message)

        logger.info("Successfully sent SMS to %s", phone)
        logger.debug("API response: %s", response)

        return response

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise
    except SmsAeroException as e:
        logger.error("SmsAero API error: %s", str(e))
        raise
    except ConnectionError as e:
        logger.error("Network connectivity error: %s", str(e))
        raise


def main() -> None:
    """
    Parses command line arguments and sends an SMS message via SmsAero.

    If the SMS message is sent successfully, the response data from SmsAero is printed.
    If an error occurs, the error message is printed and the program exits with status code 1.

    Command line arguments:
        --email: The email registered with SMS Aero
        --api_key: The API key from SMS Aero
        --phone: The phone number to send the SMS message to (international format without +)
        --message: The text of the message to send (2-640 characters)
        --debug: Optional flag to enable debug logging

    Returns:
        None

    Exits:
        0: Success
        1: Error occurred during execution
    """
    parser = argparse.ArgumentParser(
        description="Send SMS via smsaero.ru gate", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--email", type=str, required=True, help="Your email registered with SMS Aero")
    parser.add_argument("--api_key", type=str, required=True, help="Your SMS Aero API key")
    parser.add_argument(
        "--phone", type=int, required=True, help="Phone number to send SMS to (international format without +)"
    )
    parser.add_argument("--message", type=str, required=True, help="Message to send (2-640 characters)")
    parser.add_argument("--debug", action="store_true", default=False, help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    try:
        result = send_sms(args.email, args.api_key, args.phone, args.message)
        if result:
            logger.info("SMS sent successfully")
            pprint.pprint(result)
        sys.exit(0)
    except (SmsAeroException, ValueError, ConnectionError) as e:
        logger.error("Failed to send SMS: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
