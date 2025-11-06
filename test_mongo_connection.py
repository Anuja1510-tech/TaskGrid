# test_mongo_connection.py
from pymongo import MongoClient

try:
    client = MongoClient("mongodb://localhost:27017/")  # Update this if you have a remote URI
    print("✅ Connection successful!")

    # Optional: List all databases
    db_list = client.list_database_names()
    print("Databases:", db_list)

except Exception as e:
    print("❌ Connection failed:", e)
