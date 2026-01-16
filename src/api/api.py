import datetime
import requests
import time
import urllib

class API():
    _last_request_sent = datetime.datetime.now()

    _base_url = ""
    _headers = {}

    def _handle_http_status(self, response):
        if (str(response.status_code).startswith('2')):
            return True
        return False

    def _get_request(self, url, delay=0):
        try:
            if (delay != 0):
                while ((datetime.datetime.now() - self._last_request_sent).seconds < delay):
                    time.sleep(1)
            self._last_request_sent = datetime.datetime.now()
            print(f"Making GET request to '{url}'")
            response = requests.get(url, headers=self._headers)
            if (self._handle_http_status(response) and response.text != ''):
                return response.json()
        except requests.exceptions.ConnectionError:
            print("Issue with making GET request")
        return {}
    
    def _post_request(self, url, body, delay=0):
        try:
            if (delay != 0):
                while ((datetime.datetime.now() - self._last_request_sent).seconds < delay):
                    time.sleep(1)
            self._last_request_sent = datetime.datetime.now()
            print(f"Making POST request to '{url}'")
            response = requests.post(url, json=body, headers=self._headers)
            if (self._handle_http_status(response) and response.text != ''):
                return response.json()
        except requests.exceptions.ConnectionError:
            print("Issue with making POST request")
        return {}

    def _put_request(self, url, body, delay=0):
        try:
            if (delay != 0):
                while ((datetime.datetime.now() - self._last_request_sent).seconds < delay):
                    time.sleep(1)
            self._last_request_sent = datetime.datetime.now()
            print(f"Making PUT request to '{url}'")
            response = requests.put(url, json=body, headers=self._headers)
            if (self._handle_http_status(response) and response.text != ''):
                return response.json()
        except requests.exceptions.ConnectionError:
            print("Issue with making PUT request")
        return {}

    def _create_url(self, url, query_params={}):
        return f"{url}{'?' if query_params != {} else ''}{urllib.parse.urlencode(query_params)}"