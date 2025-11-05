import sys
import os

# Allow Python to find your 'backend' folder
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from utils.mongo_db import get_database, is_healthy

if __name__ == "__main__":
    print("Testing MongoDB connection...\n")

    if is_healthy():
        db = get_database()
        print(f"✅ Connected to MongoDB successfully!")
        print(f"📘 Database name: {db.name}")
        print(f"📂 Collections currently available: {db.list_collection_names()}")
    else:
        print("❌ MongoDB connection failed. Check that MongoDB is running and your URI is correct.")
