import requests
import json
import time

class SetuAAHandler:
    def __init__(self, client_id, client_secret, product_id):
        self.base_url = "https://fiu-sandbox.setu.co" # Sandbox URL
        self.headers = {
            "x-client-id": client_id,
            "x-client-secret": client_secret,
            "x-product-instance-id": product_id,
            "Content-Type": "application/json"
        }

    def initiate_consent(self, phone_number):
        """Step 1: Create a consent request for the user"""
        url = f"{self.base_url}/consents"
        payload = {
            "Detail": {
                "consentStart": "2023-01-01T00:00:00Z",
                "consentExpiry": "2026-12-31T00:00:00Z",
                "Customer": {"id": f"{phone_number}@onemoney"}, # Standard Sandbox VPA
                "FIDataRange": {"from": "2023-01-01T00:00:00Z", "to": "2024-01-01T00:00:00Z"},
                "consentMode": "STORE",
                "consentTypes": ["TRANSACTIONS", "PROFILE", "SUMMARY"],
                "fiTypes": ["DEPOSIT"]
            },
            "redirectUrl": "http://localhost:3000/callback" # Your React callback path [cite: 343]
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json() # Returns 'id' (consent_id) and 'url' (for user) [cite: 336]

    def fetch_fi_data(self, consent_id):
        """Step 2: Fetch raw transaction data once user has approved"""
        # Note: In a real app, you'd wait for a webhook, but for a hackathon, 
        # you can poll this endpoint or call it after redirect[cite: 339, 346].
        url = f"{self.base_url}/fi/fetch/{consent_id}"
        response = requests.get(url, headers=self.headers)
        return response.json() # Raw JSON transactions [cite: 337]