"""
Query the custom tool configuration from Cosmos DB
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

endpoint = settings.COSMOS_ENDPOINT
db_name = settings.COSMOS_DATABASE_NAME

print(f"Connecting to Cosmos DB:")
print(f"  Endpoint: {endpoint}")
print(f"  Database: {db_name}")
print()

credential = AzureCliCredential()
client = CosmosClient(endpoint, credential=credential)
database = client.get_database_client(db_name)

# Try to get the custom tools container
try:
    container = database.get_container_client("custom-tools")
    
    # Query for the tool
    response = container.read_item(item="custom-b9041bd2", partition_key="custom-b9041bd2")
    print("=== Custom Tool Configuration ===")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Error querying custom-tools container: {e}")
    print("\nListing available containers...")
    try:
        for container_props in database.list_containers():
            print(f"  - {container_props['id']}")
    except Exception as list_err:
        print(f"  Error listing containers: {list_err}")
