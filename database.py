# database.py
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("MONGO_DB_NAME", "telegram_bot")]

        self.db = db
        self.bookings = db["bookings"]
        self.uploads = db["uploads"]
        self.users = db["users"]

    # ── BOOKINGS ─────────────────────────

    def is_date_available(self, date: str, max_per_date: int = 10) -> bool:
        count = self.bookings.count_documents({
            "date": date,
            "status": "confirmed"
        })
        return count < max_per_date

    def create_booking(self, user_id: int, username: str, full_name: str, date: str):
        self.bookings.insert_one({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "date": date,
            "status": "confirmed",
            "created_at": datetime.utcnow()
        })

    # ── UPLOADS ─────────────────────────

    def save_upload(self, user_id: int, file_id: str, file_name: str = "unknown"):
        self.uploads.insert_one({
            "user_id": user_id,
            "file_id": file_id,
            "file_name": file_name,
            "uploaded_at": datetime.utcnow()
        })

    def get_uploads(self, user_id: int):
        return list(self.uploads.find({"user_id": user_id}))

    # ✅ FIXED — SESSION BASED UPLOADS
    def get_session_uploads(self, user_id: int, since: datetime) -> list:
        return list(self.uploads.find({
            "user_id": user_id,
            "uploaded_at": {"$gte": since}
        }))

    # ── FEEDBACK ─────────────────────────

    def save_feedback(self, user_id: int, rating: str, comment: str = ""):
        self.db["feedback"].insert_one({
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "submitted_at": datetime.utcnow()
        })

    # ── USER STATE ───────────────────────

    def set_user_state(self, user_id: int, state: str, data: dict = {}):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "state": state,
                "data": data,
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )

    def get_user_state(self, user_id: int):
        user = self.users.find_one({"user_id": user_id})
        return user if user else {}
