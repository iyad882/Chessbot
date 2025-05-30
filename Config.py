import os

class Config:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("Environment variable TELEGRAM_BOT_TOKEN is required")

        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            raise ValueError("Environment variable ADMIN_IDS is required")

        # تحويل قائمة الإدمنز من string إلى أرقام صحيحة
        self.admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
