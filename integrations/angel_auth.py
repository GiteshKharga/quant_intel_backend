# integrations/angel_auth.py

"""
Angel One Authentication Helper
Generates Access Token from Request Token.
"""

import requests
import logging

logger = logging.getLogger(__name__)

AUTH_URL = "https://api.angelone.in/rest/auth/angel-login"  # Angel One official login endpoint

def generate_access_token(api_key: str, api_secret: str, request_token: str):
    """
    Generate Access Token using Angel One request_token.
    This must be done DAILY.
    """
    payload = {
        "api_key": api_key,
        "api_secret": api_secret,
        "request_token": request_token
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    resp = requests.post(AUTH_URL, json=payload, headers=headers)

    try:
        resp.raise_for_status()
    except Exception as e:
        logger.error("Token generation failed: %s", e)
        logger.error("Response: %s", resp.text)
        raise

    data = resp.json()

    # Typical response:
    # { "status": true, "access_token": "xxxxx", "refresh_token": "xxxxx" }

    return {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token")
    }
