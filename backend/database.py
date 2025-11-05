# database.py (MongoDB Connection Setup)

from pymongo import MongoClient

# 1️⃣ Connect to MongoDB server (Local or Atlas)
client = MongoClient("mongodb://127.0.0.1:27017/")  
# If using MongoDB Atlas, replace with your cloud URI

# 2️⃣ Create / Select Database
db = client["project_db"]   # You can rename it (e.g. task_db, myapp_db)

# 3️⃣ Define Collections (like tables in SQL)
users_col = db["users"]         # For user data (login, signup)
projects_col = db["projects"]   # For project data
tasks_col = db["tasks"]         # For tasks
worklogs_col = db["worklogs"]   # Optional, for logs or reports

# ✅ Connection Test (Optional)
def test_connection():
    try:
        db.command("ping")
        print("✅ MongoDB Connection Successful!")
    except Exception as e:
        print("❌ MongoDB Connection Failed:", e)
