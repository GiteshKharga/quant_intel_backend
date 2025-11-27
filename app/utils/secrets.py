# app/utils/secrets.py
import boto3
import os
import json
from botocore.exceptions import ClientError

def get_secret(secret_name: str, region_name: str = None) -> dict:
    region_name = region_name or os.getenv("AWS_REGION", "ap-south-1")
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise
    secret = get_secret_value_response.get("SecretString")
    if secret:
        return json.loads(secret)
    return {}
