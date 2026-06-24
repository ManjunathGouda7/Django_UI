import requests

class SynologyClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.sid = None

    def login(self):
        url = f"{self.base_url}/auth.cgi"
        params = {
            "api": "SYNO.API.Auth",
            "version": "6",
            "method": "login",
            "account": self.username,
            "passwd": self.password,
            "session": "FileStation",
            "format": "sid"
        }
        res = requests.get(url, params=params, verify=False)
        self.sid = res.json()['data']['sid']

    def ensure_login(self):
        if not self.sid:
            self.login()