import datetime
import time
import unittest

from unittest.mock import patch, MagicMock

from smsaero import SmsAero

from . import DEFAULT_RESPONSE


class TestSmsAeroTestMode(unittest.TestCase):
    def setUp(self):
        self.smsaero = SmsAero("admin@smsaero.ru", "test_api_key_lX8APMlgliHvkHk04i7", test_mode=True)

    @patch("requests.Session.post")
    def test_send_with_all_params(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = DEFAULT_RESPONSE
        mock_post.return_value = mock_response

        date_to_send = datetime.datetime.now() + datetime.timedelta(days=1)
        result = self.smsaero.send_sms(
            79031234567,
            "test message",
            sign="test sign",
            callback_url="https://smsaero.ru/callback",
            date_to_send=date_to_send,
        )

        self.assertEqual(result, False)

        mock_post.assert_called_once_with(
            "https://admin%40smsaero.ru:test_api_key_lX8APMlgliHvkHk04i7@gate.smsaero.ru/v2/sms/testsend",
            json={
                "number": 79031234567,
                "text": "test message",
                "sign": "test sign",
                "callbackUrl": "https://smsaero.ru/callback",
                "dateSend": int(time.mktime(date_to_send.timetuple())),
            },
            timeout=15,
        )

    @patch("requests.Session.post")
    def test_sms_status(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = DEFAULT_RESPONSE
        mock_post.return_value = mock_response

        sms_id = 12345
        result = self.smsaero.sms_status(sms_id)

        self.assertEqual(result, False)
        mock_post.assert_called_once_with(
            "https://admin%40smsaero.ru:test_api_key_lX8APMlgliHvkHk04i7@gate.smsaero.ru/v2/sms/teststatus",
            json={"id": sms_id},
            timeout=15,
        )

    @patch.object(SmsAero, "request")
    def test_sms_list(self, mock_request):
        mock_request.return_value = {"success": True}
        numbers = [79031234567, 79038805678]
        text = "Hello, World!"
        result = self.smsaero.sms_list(numbers, text)
        self.assertEqual(result, {"success": True})
        mock_request.assert_called_once_with("sms/testlist", {"numbers": numbers, "text": text}, None)
