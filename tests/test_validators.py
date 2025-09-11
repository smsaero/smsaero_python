import unittest

from smsaero import SmsAero


class TestSmsAeroValidators(unittest.TestCase):
    def setUp(self):
        self.smsaero = SmsAero("admin@smsaero.ru", "test_api_key_lX8APMlgliHvkHk04i7")

    def test_send_sms_validate(self):
        with self.assertRaises(TypeError):
            self.smsaero.send_sms_validate("invalid_number", "test text")
        with self.assertRaises(TypeError):
            self.smsaero.send_sms_validate(70000000000, 123)
        with self.assertRaises(TypeError):
            self.smsaero.send_sms_validate(70000000000, "test text", 123)
        with self.assertRaises(TypeError):
            self.smsaero.send_sms_validate(70000000000, "test text", date_to_send="invalid_date")
        with self.assertRaises(TypeError):
            self.smsaero.send_sms_validate(70000000000, "test text", callback_url=123)
        with self.assertRaises(ValueError):
            self.smsaero.send_sms_validate(1, "test text")
        with self.assertRaises(ValueError):
            self.smsaero.send_sms_validate(70000000000, "t")
        with self.assertRaises(ValueError):
            self.smsaero.send_sms_validate(70000000000, "test text", callback_url="invalid_url")
        with self.assertRaises(ValueError):
            self.smsaero.send_sms_validate(number=[70000000000], text="Test message")
        with self.assertRaises(ValueError):
            self.smsaero.send_sms_validate(number=70000000000, text="Test message")
        with self.assertRaises(ValueError):
            self.smsaero.send_sms_validate(number=[123, 1234567890123456], text="Test message")

    def test_send_sms_validate_without_phonenumbers(self):
        smsaero = SmsAero("admin@smsaero.ru", "test_api_key_lX8APMlgliHvkHk04i7", allow_phone_validation=False)
        smsaero.send_sms_validate(number=[70000000000], text="Test message")
        smsaero.send_sms_validate(number=70000000000, text="Test message")

    def test_validate_phonenumbers(self):
        self.smsaero.phonenumbers_validate(number=79038805678)
        self.smsaero.phonenumbers_validate(number=[79038805678, 79038805679])
        with self.assertRaises(ValueError):
            self.smsaero.phonenumbers_validate(number=70000000001)
        with self.assertRaises(ValueError):
            self.smsaero.phonenumbers_validate(number=[70000000001])
        with self.assertRaises(ValueError):
            self.smsaero.phonenumbers_validate(number="invalid_number")
        with self.assertRaises(ValueError):
            self.smsaero.phonenumbers_validate(number=["invalid_number"])

    def test_sms_list_validate(self):
        with self.assertRaises(TypeError):
            self.smsaero.sms_list_validate(number="invalid_number")
        with self.assertRaises(TypeError):
            self.smsaero.sms_list_validate(text=123)
        with self.assertRaises(TypeError):
            self.smsaero.sms_list_validate(page="invalid_page")
        with self.assertRaises(ValueError):
            self.smsaero.sms_list_validate(page=0)
        with self.assertRaises(ValueError):
            self.smsaero.sms_list_validate(number=[79038805678, "invalid_number"])
        with self.assertRaises(ValueError):
            self.smsaero.sms_list_validate(number=[79038805678, 70000000000])

    def test_viber_send_validate(self):
        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(123, "channel", "text")

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate("sign", 123, "text")

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate("sign", "channel", 123)

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                "invalid_number",
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                "invalid_group_id",
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                "image_source",
                123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                "image_source",
                "text_button",
                123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                "image_source",
                "text_button",
                "link_button",
                123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                "image_source",
                "text_button",
                "link_button",
                "date_send",
                123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                "image_source",
                "text_button",
                "link_button",
                "date_send",
                "sign_sms",
                123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                "image_source",
                "text_button",
                "link_button",
                "date_send",
                "sign_sms",
                "channel_sms",
                123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                1234567890,
                123,
                "image_source",
                "text_button",
                "link_button",
                "date_send",
                "sign_sms",
                "channel_sms",
                "text_sms",
                "invalid_price_sms",
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                number=112345678901234567890,
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                number=[112345678901234567890, 12345678901234567890],
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                number=123,
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                "sign",
                "channel",
                "text",
                number=[1234567890, 123],
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                sign="TestSign",
                channel="TestChannel",
                text="T" * 641,
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                sign="TestSign",
                channel="TestChannel",
                text="",
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                sign="T" * 65,
                channel="TestChannel",
                text="TestText",
            )

        with self.assertRaises(ValueError):
            self.smsaero.viber_send_validate(
                sign="T",
                channel="TestChannel",
                text="TestText",
            )

    def test_contact_add_validate(self):
        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(number="invalid_number")

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(number=79038805678, group_id="invalid_group_id")

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(number=79038805678, group_id=123, birthday=123)

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(number=79038805678, group_id=123, birthday="01-01-2000", sex=123)

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(
                number=79038805678, group_id=123, birthday="01-01-2000", sex="male", last_name=123
            )

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(
                number=79038805678, group_id=123, birthday="01-01-2000", sex="male", last_name="Doe", first_name=123
            )

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(
                number=79038805678,
                group_id=123,
                birthday="01-01-2000",
                sex="male",
                last_name="Doe",
                first_name="John",
                surname=123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(
                number=79038805678,
                group_id=123,
                birthday="01-01-2000",
                sex="male",
                last_name="Doe",
                first_name="John",
                surname="Smith",
                param1=123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(
                number=79038805678,
                group_id=123,
                birthday="01-01-2000",
                sex="male",
                last_name="Doe",
                first_name="John",
                surname="Smith",
                param1="param1",
                param2=123,
            )

        with self.assertRaises(TypeError):
            self.smsaero.contact_add_validate(
                number=79038805678,
                group_id=123,
                birthday="01-01-2000",
                sex="male",
                last_name="Doe",
                first_name="John",
                surname="Smith",
                param1="param1",
                param2="param2",
                param3=123,
            )

        with self.assertRaises(ValueError):
            self.smsaero.contact_add_validate(number=[123, "invalid_number"])

        with self.assertRaises(ValueError):
            self.smsaero.contact_add_validate(number=[123, 1234567890123456])

        with self.assertRaises(ValueError):
            self.smsaero.contact_add_validate(number=1234567890123456)

    def test_contact_list_validate(self):
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(number="invalid_number")
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(group_id="invalid_group_id")
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(birthday=123)
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(sex=123)
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(operator=123)
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(last_name=123)
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(first_name=123)
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(surname=123)
        with self.assertRaises(TypeError):
            self.smsaero.contact_list_validate(page="invalid_page")
        with self.assertRaises(ValueError):
            self.smsaero.contact_list_validate(number=[79038805678, "invalid_number"])

    def test_init_validate_with_invalid_email(self):
        with self.assertRaises(ValueError):
            self.smsaero.init_validate(
                "invalid_email",
                "test_api_key_lX8APMlgliHvkHk04i7",
                "test_signature",
                15,
                True,
                None,
                False,
            )
        with self.assertRaises(TypeError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                123,
                "test_signature",
                15,
                True,
                None,
                False,
            )
        with self.assertRaises(TypeError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key_lX8APMlgliHvkHk04i7",
                123,
                15,
                True,
                None,
                False,
            )
        with self.assertRaises(TypeError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key_lX8APMlgliHvkHk04i7",
                "test_signature",
                "invalid_timeout",
                True,
                None,
                False,
            )
        with self.assertRaises(TypeError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key_lX8APMlgliHvkHk04i7",
                "test_signature",
                15,
                "invalid_allow_phone_validation",
                None,
                False,
            )
        with self.assertRaises(TypeError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key_lX8APMlgliHvkHk04i7",
                "test_signature",
                15,
                True,
                123,
                False,
            )
        with self.assertRaises(TypeError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key_lX8APMlgliHvkHk04i7",
                "test_signature",
                15,
                True,
                None,
                "invalid_test_mode",
            )
        with self.assertRaises(ValueError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key",
                "test_signature",
                15,
                True,
                None,
                "invalid_test_mode",
            )
        with self.assertRaises(ValueError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key_lX8APMlgliHvkHk04i7",
                "t",
                15,
                True,
                None,
                False,
            )
        with self.assertRaises(ValueError):
            self.smsaero.init_validate(
                "admin@smsaero.ru",
                "test_api_key_lX8APMlgliHvkHk04i7",
                "tуест_signature",
                1,
                True,
                None,
                False,
            )

    def test_send_telegram_validate(self):
        with self.assertRaises(TypeError):
            self.smsaero.send_telegram_validate("invalid_number", 1234)
        with self.assertRaises(TypeError):
            self.smsaero.send_telegram_validate(79031234567, "invalid_code")
        with self.assertRaises(TypeError):
            self.smsaero.send_telegram_validate(79031234567, 1234, sign=123)
        with self.assertRaises(TypeError):
            self.smsaero.send_telegram_validate(79031234567, 1234, text=123)
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(79031234567, 123)  # code too short
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(79031234567, 123456789)  # code too long
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(79031234567, 1234, sign="T")  # sign too short
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(79031234567, 1234, sign="T" * 65)  # sign too long
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(79031234567, 1234, text="T")  # text too short
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(79031234567, 1234, text="T" * 641)  # text too long
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(123, 1234)  # number too short
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate(1234567890123456, 1234)  # number too long
        with self.assertRaises(ValueError):
            self.smsaero.send_telegram_validate([123, 1234567890123456], 1234)  # mixed invalid numbers

    def test_send_telegram_validate_without_phonenumbers(self):
        smsaero = SmsAero("admin@smsaero.ru", "test_api_key_lX8APMlgliHvkHk04i7", allow_phone_validation=False)
        smsaero.send_telegram_validate(number=[79031234567], code=1234)
        smsaero.send_telegram_validate(number=79031234567, code=1234)
