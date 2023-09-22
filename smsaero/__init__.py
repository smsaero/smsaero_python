#!/usr/bin/env python

import time
import requests
import json

from requests import exceptions

try:
    from urllib.parse import urljoin, quote_plus
except ImportError:
    from urllib import quote_plus
    from urlparse import urljoin

from datetime import datetime


class SmsAeroError(Exception):
    """ Super class of all SmsAero Errors. """


class SmsAeroHTTPError(SmsAeroError):
    """ A Connection error occurred. """


class SmsAeroConnectionError(SmsAeroError):
    """ A Connection error occurred. """


class SmsAero:
    GATE_URLS = [
        '@gate.smsaero.ru/v2/',
        '@gate.smsaero.org/v2/',
        '@gate.smsaero.net/v2/',
        '@gate.smsaero.uz/v2/',
    ]
    SIGNATURE = 'Sms Aero'
    TYPE_SEND = 2

    def __init__(
            self, email, api_key,
            url_gate=None,
            signature=SIGNATURE,
            type_send=TYPE_SEND
    ):
        self.email = email
        self.api_key = api_key

        self.url_gate = url_gate
        self.signature = signature
        self.type_send = type_send
        self.session = requests.session()

    def _get_gate_urls(self):
        if self.url_gate:
            return [self.url_gate]
        return self.GATE_URLS

    def _request(self, selector, data=None, page=None, proto='https'):
        try:
            for gate in self._get_gate_urls():
                try:
                    url = urljoin("{}://{}:{}{}".format(proto, quote_plus(self.email), self.api_key, gate), selector)
                    if page:
                        url = urljoin(url, "?page={}".format(page))
                    response = self.session.post(url, json=data or {})
                    return self._check_response(response.content)
                except exceptions.SSLError:
                    proto = 'http'
                    continue
                except exceptions.ConnectionError:
                    continue
            else:
                raise SmsAeroConnectionError
        except requests.RequestException as err:
            raise SmsAeroHTTPError(err)

    @staticmethod
    def _get_num(number):
        if type(number) is list:
            num = 'numbers'
        else:
            num = 'number'
            number = str(number)
        return [num, number]

    @staticmethod
    def _check_response(content):
        try:
            response = json.loads(content)
            if 'result' in response and response['result'] == 'reject':
                raise SmsAeroError(response['reason'])
            elif 'result' in response and response['result'] == 'no credits':
                raise SmsAeroError(response['result'])
            return response
        except ValueError:
            if 'incorrect language' in content:
                raise SmsAeroError("incorrect language in '...' use \
                    the cyrillic or roman alphabet.")
            else:
                raise SmsAeroError('unexpected format is received')

    def send(self, number, text, date_send=None, callback_url=None):
        num, number = self._get_num(number)
        data = {
            num: number,
            'sign': self.signature,
            'text': text,
            'callbackUrl': callback_url
        }
        if date_send is not None:
            if isinstance(date_send, datetime):
                data['dateSend'] = int(time.mktime(date_send.timetuple()))
            else:
                raise SmsAeroError('param `date` is not datetime object')
        return self._request('sms/send', data)

    def sms_status(self, sms_id):
        return self._request('sms/status', {'id': sms_id})

    def sms_list(self, number=None, text=None, page=None):
        data = {}
        if number:
            data.update({'number': str(number)})
        if text:
            data.update({'text': text})
        return self._request('sms/list', data, page)

    def balance(self):
        return self._request('balance')

    def auth(self):
        return self._request('auth')

    def cards(self):
        return self._request('cards')

    def add_balance(self, _sum, card_id):
        return self._request('balance/add', {'sum': _sum, 'cardId': card_id})

    def tariffs(self):
        return self._request('tariffs')

    def sign_add(self, name):
        return self._request('sign/add', {'name': name})

    def sign_list(self, page=None):
        return self._request('sign/list', page=page)

    def group_add(self, name):
        return self._request('group/add', {'name': name})

    def group_delete(self, group_id):
        return self._request('group/delete', {'id': group_id})

    def group_list(self, page=None):
        return self._request('group/list', page=page)

    def contact_add(self, number, group_id=None, birthday=None, sex=None,
                    lname=None, fname=None, sname=None,
                    param1=None, param2=None, param3=None):
        return self._request('contact/add', {
            'number': str(number),
            'groupId': group_id,
            'birthday': birthday,
            'sex': sex,
            'lname': lname,
            'fname': fname,
            'sname': sname,
            'param1': param1,
            'param2': param2,
            'param3': param3
        })

    def contact_delete(self, contact_id):
        return self._request('contact/delete', {'id': contact_id})

    def contact_list(
            self, number=None, group_id=None, birthday=None, sex=None,
            operator=None, lname=None, fname=None, sname=None, page=None):
        return self._request('contact/list', {
            'number': number and str(number),
            'groupId': group_id,
            'birthday': birthday,
            'sex': sex,
            'operator': operator,
            'lname': lname,
            'fname': fname,
            'sname': sname
        }, page)

    def blacklist_add(self, number):
        num, number = self._get_num(number)
        return self._request('blacklist/add', {num: number})

    def blacklist_list(self, number=None, page=None):
        data = number and {'number': str(number)}
        return self._request('blacklist/list', data, page)

    def blacklist_delete(self, blacklist_id):
        return self._request('blacklist/delete', {'id': int(blacklist_id)})

    def hlr_check(self, number):
        num, number = self._get_num(number)
        return self._request('hlr/check', {num: number})

    def hlr_status(self, hlr_id):
        return self._request('hlr/status', {'id': int(hlr_id)})

    def number_operator(self, number):
        num, number = self._get_num(number)
        return self._request('number/operator', {num: number})

    def viber_send(self, sign, channel, text, number=None, group_id=None,
                   image_source=None, text_button=None,
                   link_button=None, date_send=None, sign_sms=None,
                   channel_sms=None, text_sms=None, price_sms=None):
        num, number = self._get_num(number)
        return self._request('viber/send', {
            num: number,
            'groupId': group_id and int(group_id),
            'sign': sign and str(sign),
            'channel': channel and str(channel),
            'text': text,
            'imageSource': image_source,
            'textButton': text_button,
            'linkButton': link_button,
            'dateSend': date_send,
            'signSms': sign_sms,
            'channelSms': channel_sms,
            'textSms': text_sms,
            'priceSms': price_sms
        })

    def viber_sign_list(self):
        return self._request('viber/sign/list')

    def viber_list(self, page=None):
        return self._request('viber/list', page=page)

    def flashcall_send(self, number, code):
        return self._request('flashcall/send', {
            'phone': number,
            'code': int(code)
        })

    def flashcall_list(self, number=None, text=None, page=None):
        data = {}
        if number:
            data.update({'number': str(number)})
        if text:
            data.update({'text': text})
        return self._request('flashcall/list', data, page)

    def flashcall_status(self, pk):
        return self._request('flashcall/status', {'id': pk})
