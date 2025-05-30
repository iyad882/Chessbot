import os

class Config:
    def __init__(self):
        admin_ids = os.getenv("ADMIN_IDS", "")
        self.admin_ids = [int(i) for i in admin_ids.split(",") if i.strip().isdigit()]
