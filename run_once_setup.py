# run_once_setup.py
from database import Database

db = Database()
db.bookings.create_index("user_id")
db.bookings.create_index("date")       # fast availability checks
db.uploads.create_index("user_id")
db.users.create_index("user_id", unique=True)

print("Indexes created ✅")