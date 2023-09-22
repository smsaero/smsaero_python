# SmsAero Python Api


### Installation:

    $ pip install -U smsaero_api


### Usage:

Get credentials from account settings page: https://smsaero.ru/cabinet/settings/apikey/
    
    from pprint import pprint
    from smsaero import SmsAero


    SMSAERO_EMAIL = 'your email'
    SMSAERO_API_KEY = 'your api key'
    
    
    def send_sms(phone: int, message: str) -> dict:
        """
        Send sms and return results.
    
                Parameters:
                        phone (int): Phone number
                        message (str): Message to send
    
                Returns:
                        data (dict): API request result
        """
        api = SmsAero(SMSAERO_EMAIL, SMSAERO_API_KEY)
        res = api.send(phone, message)
        assert res.get('success'), res.get('message')
        return res.get('data')
    
    
    if __name__ == '__main__':
        data = send_sms(70000000000, 'Hello, World!')
        pprint(data)
