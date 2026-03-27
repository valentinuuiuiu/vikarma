import requests
import json
import base64

class Functions:
    def __init__(self):
        self.n8n_url = "http://host.docker.internal:5678/webhook/invoice-vision"
        self.api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjYWM5ZmRjMS0yYzQzLTRiYTgtYTVmMi04ODljN2ExYWIzZTkiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzc0NTQ0MTA4LCJleHAiOjE3NzcwODk2MDB9.6orHA0Qg_vEzjVUJVTMfMbzfY5lou7GoYtcmJeQKHfQ"

    def process_invoice(self, data: dict, binary_data: bytes = None):
        """
        Sends invoice data and optional image to n8n for processing.
        """
        headers = {
            "X-N8N-API-KEY": self.api_key
        }

        files = {}
        if binary_data:
            files['data'] = ('invoice.png', binary_data, 'image/png')

        response = requests.post(
            self.n8n_url,
            headers=headers,
            data=data,
            files=files
        )

        return response.json()

    def fetch_invoice(self, url: str):
        """
        Fetches a web page (e.g. invoice portal) via n8n browser automation.
        """
        response = requests.post(
            "http://host.docker.internal:5678/webhook/fetch-invoice",
            headers={"X-N8N-API-KEY": self.api_key},
            json={"url": url}
        )
        return response.json()
