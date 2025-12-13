# tests/quick_test.py

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Adjust import paths for testing
from integrations.angel_one import AngelOneClient
from execution.engine import ExecutionEngine

client = AngelOneClient(
    api_key=os.getenv("ANGEL_API_KEY"),
    api_secret=os.getenv("ANGEL_API_SECRET"),
    access_token=os.getenv("ANGEL_ACCESS_TOKEN")
)

engine = ExecutionEngine(broker_client=client)

print("Running Angel One MVP connectivity test...\n")

result = engine.execute_signal({
    "symbol": "NIFTY",
    "action": "BUY",
    "qty": 1
})

print("\n--- EXECUTION RESULT ---")
print(result)
