"""
Query the current sql-agent configuration from Cosmos DB
"""
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from azure.cosmos import CosmosClient
from azure.identity import AzureCliCredential
from src.config import settings

# Initialize Cosmos DB client
endpoint = settings.COSMOS_ENDPOINT
db_name = settings.COSMOS_DATABASE_NAME

print(f"Connecting to Cosmos DB:")
print(f"  Endpoint: {endpoint}")
print(f"  Database: {db_name}")
print()

# Use Azure CLI credential for authentication
credential = AzureCliCredential()
client = CosmosClient(endpoint, credential=credential)
database = client.get_database_client(db_name)
container = database.get_container_client("agents")

# Query for sql-agent
try:
    response = container.read_item(item="sql-agent", partition_key="sql-agent")
    print("=== SQL Agent Configuration ===")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Error querying agent: {e}")
