"""
User command handlers for the Telegram bot
Handles commands available to all users
"""

import json
import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class UserHandlers:
    def __init__(self):
        self.user_activity_file = "data/user_activity.json"
        self.user_profiles_file = "data/user_profiles.json"
        self.user_stats = {}
        self.user_profiles = {}
        self.load_user_stats()
        self.load_user_profiles()

    def load_user_stats(self):
        """Load user activity statistics"""
        try:
            if os.path.exists(self.user_activity_file):
                with open(self.user_activity_file, 'r', encoding='utf-8') as f:
                    self.user_stats = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load user stats: {e}")
            self.user_stats = {}

    def save_user_stats(self):
        """Save user activity statistics"""
        try:
            os.makedirs(os.path.dirname(self.user_activity_file), exist_ok=True)
            with open(self.user_activity_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save user stats: {e}")

    def load_user_profiles(self):
        """Load user profiles with Lichess accounts and balance"""
        try:
            if os.path.exists(self.user_profiles_file):
                with open(self.user_profiles_file, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load user profiles: {e}")
            self.user_profiles = {}

    def save_user_profiles(self):
        """Save user profiles"""
        try:
            os.makedirs(os.path.dirname(self.user_profiles_file), exist_ok=True)
            with open(self.user_profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save user profiles: {e}")

    def get_user_profile(self, user_id: int):
        """Get user profile or create new one"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_profiles:
            self.user_profiles[user_id_str] = {
                "lichess_username": None,
                "balance": 100,
                "registration_complete": False,
                "created_at": datetime.now().isoformat()
            }
            self.save_user_profiles()
        return self.user_profiles[user_id_str]

    def update_user_profile(self, user_id: int, **kwargs):
        """Update user profile"""
        user_id_str = str(user_id)
        profile = self.get_user_profile(user_id)
        profile.update(kwargs)
        self.user_profiles[user_id_str] = profile
        self.save_user_profiles()

    def is_user_registered(self, user_id: int) -> bool:
        """Check if user has completed registration"""
        profile = self.get_user_profile(user_id)
        return profile.get("registration_complete", False)

    def log_user_activity(self, user_id: int, username: str, message: str):
        """Log user activity"""
        user_id_str = str(user_id)
        current_time = datetime.now().isoformat()
        
        if user_id_str not in self.user_stats:
            self.user_stats[user_id_str] = {
                "username": username,
                "first_seen": current_time,
                "last_seen": current_time,
                "message_count": 0,
                "commands_used": []
            }
        
        self.user_stats[user_id_str]["username"] = username
        self.user_stats[user_id_str]["last_seen"] = current_time
        self.user_stats[user_id_str]["message_count"] += 1
        
        # Log command usage
        if message.startswith('/'):
            command = message.split()[0]
            if command not in self.user_stats[user_id_str]["commands_used"]:
                self.user_stats[user_id_str]["commands_used"].append(command)
        
        self.save_user_stats()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "No username"
        
        logger.info(f"Start command from user {user_id} ({username})")
        self.log_user_activity(user_id, username, "/start")
        
        # Check if user is registered
        if not self.is_user_registered(user_id):
            profile = self.get_user_profile(user_id)
            if profile["lichess_username"] is None:
                # First time user - ask for Lichess username
                welcome_message = f"""
🤖 **مرحباً بك في البوت!**

أهلاً {user.first_name}! لإكمال التسجيل، نحتاج منك إدخال اسم المستخدم الخاص بك في موقع Lichess.

**يرجى إرسال اسم المستخدم في Lichess الخاص بك:**
مثال: اكتب فقط اسم المستخدم (بدون @)

**ملاحظة:** سيتم إضافة رصيد ابتدائي قدره 100 نقطة لحسابك بعد التسجيل.

إذا لم يكن لديك حساب في Lichess، يمكنك إنشاؤه من هنا: https://lichess.org/signup
                """
                await update.message.reply_text(welcome_message, parse_mode='Markdown')
                return
        
        # User is registered - show normal welcome
        welcome_message = f"""
🤖 **مرحباً بك في البوت!**

أهلاً {user.first_name}! أنا هنا لمساعدتك.

**الأوامر المتاحة:**
• /start - بدء البوت
• /help - عرض معلومات المساعدة
• /info - عرض معلومات حسابك
• /balance - عرض رصيدك الحالي

للأوامر الإدارية، يرجى التواصل مع المدير.

استخدم /help لمزيد من المعلومات التفصيلية.
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "No username"
        
        logger.info(f"Help command from user {user_id} ({username})")
        self.log_user_activity(user_id, username, "/help")
        
        help_message = """
📋 **مساعدة البوت**

**أوامر المستخدمين:**
• `/start` - بدء البوت وعرض رسالة الترحيب
• `/help` - عرض رسالة المساعدة هذه
• `/info` - عرض معلومات حسابك وإحصائياتك

**ميزات البوت:**
• تسجيل الرسائل وتتبع نشاط المستخدمين
• نظام إدارة المديرين
• واجهة سهلة الاستخدام

**كيفية الاستخدام:**
1. أرسل أي رسالة للتفاعل مع البوت
2. استخدم الأوامر التي تبدأ بـ '/' للوظائف المحددة
3. تواصل مع المدير للميزات المتقدمة

**الدعم:**
إذا كنت بحاجة لمساعدة أو لديك أسئلة، يرجى التواصل مع مديري البوت.

**ملاحظة:** بعض الأوامر مخصصة للمديرين فقط.
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "No username"
        
        logger.info(f"Info command from user {user_id} ({username})")
        self.log_user_activity(user_id, username, "/info")
        
        # Check if user is registered
        if not self.is_user_registered(user_id):
            await update.message.reply_text(
                "❌ يجب عليك إكمال التسجيل أولاً. أرسل /start لبدء التسجيل."
            )
            return
        
        # Get user profile information
        profile = self.get_user_profile(user_id)
        lichess_username = profile.get("lichess_username", "غير محدد")
        balance = profile.get("balance", 0)
        registration_date = profile.get("created_at", "غير معروف")
        
        # Format registration date
        if registration_date != "غير معروف":
            try:
                from datetime import datetime
                reg_date = datetime.fromisoformat(registration_date)
                registration_date = reg_date.strftime('%Y-%m-%d')
            except:
                registration_date = "غير معروف"
        
        # Get user statistics
        user_id_str = str(user_id)
        if user_id_str in self.user_stats:
            stats = self.user_stats[user_id_str]
            first_seen = stats.get("first_seen", "Unknown")
            last_seen = stats.get("last_seen", "Unknown")
            message_count = stats.get("message_count", 0)
            commands_used = len(stats.get("commands_used", []))
        else:
            first_seen = "Now"
            last_seen = "Now"
            message_count = 1
            commands_used = 1
        
        # Format activity dates
        if first_seen != "Unknown" and 'T' in first_seen:
            first_seen = first_seen.split('T')[0]
        if last_seen != "Unknown" and 'T' in last_seen:
            last_seen = last_seen.split('T')[0]
        
        info_message = f"""
👤 **معلومات حسابك**

**حسابات المستخدم:**
• **معرف تلغرام:** `{user_id}`
• **اسم المستخدم في تلغرام:** @{username if username != "No username" else "غير محدد"}
• **الاسم الأول:** {user.first_name or "غير محدد"}
• **الاسم الأخير:** {user.last_name or "غير محدد"}
• **حساب Lichess:** {lichess_username}

**المعلومات المالية:**
• **الرصيد الحالي:** {balance} نقطة 💰

**إحصائيات النشاط:**
• **تاريخ التسجيل:** {registration_date}
• **أول ظهور:** {first_seen}
• **آخر نشاط:** {last_seen}
• **الرسائل المرسلة:** {message_count}
• **الأوامر المستخدمة:** {commands_used}

**حالة الحساب:**
• **الحالة:** مستخدم مفعل ✅
• **نوع الحساب:** عضو عادي

استخدم /help لرؤية الأوامر المتاحة أو /balance لعرض تفاصيل الرصيد.
        """
        
        await update.message.reply_text(info_message, parse_mode='Markdown')

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "No username"
        
        logger.info(f"Balance command from user {user_id} ({username})")
        self.log_user_activity(user_id, username, "/balance")
        
        # Check if user is registered
        if not self.is_user_registered(user_id):
            await update.message.reply_text(
                "❌ يجب عليك إكمال التسجيل أولاً. أرسل /start لبدء التسجيل."
            )
            return
        
        profile = self.get_user_profile(user_id)
        balance = profile.get("balance", 0)
        lichess_username = profile.get("lichess_username", "غير محدد")
        
        balance_message = f"""
💰 **رصيدك الحالي**

**المعلومات:**
• **الرصيد:** {balance} نقطة
• **حساب Lichess:** {lichess_username}
• **حالة الحساب:** مفعل ✅

**ملاحظة:** يمكنك استخدام رصيدك في الخدمات المختلفة المتوفرة في البوت.
        """
        
        await update.message.reply_text(balance_message, parse_mode='Markdown')

    async def handle_lichess_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Lichess username registration"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "No username"
        message_text = update.message.text.strip()
        
        # Check if user is in registration process
        profile = self.get_user_profile(user_id)
        if profile["registration_complete"] or profile["lichess_username"] is not None:
            return False  # User already registered
        
        # Validate Lichess username (basic validation)
        if len(message_text) < 3 or len(message_text) > 20 or not message_text.replace("_", "").replace("-", "").isalnum():
            await update.message.reply_text(
                "❌ اسم المستخدم غير صحيح. يجب أن يكون بين 3-20 حرف ويحتوي على أحرف وأرقام فقط.\n\n"
                "يرجى إرسال اسم المستخدم في Lichess مرة أخرى:"
            )
            return True
        
        # Save Lichess username and complete registration
        self.update_user_profile(
            user_id, 
            lichess_username=message_text.lower(),
            registration_complete=True,
            balance=100
        )
        
        logger.info(f"User {user_id} ({username}) completed registration with Lichess: {message_text}")
        
        success_message = f"""
✅ **تم التسجيل بنجاح!**

**تفاصيل حسابك:**
• **حساب Lichess:** {message_text}
• **الرصيد الابتدائي:** 100 نقطة

🎉 مرحباً بك في البوت! يمكنك الآن استخدام جميع الأوامر المتاحة.

**الأوامر المتاحة:**
• /help - المساعدة
• /info - معلومات حسابك
• /balance - عرض الرصيد

استخدم /help لمزيد من المعلومات.
        """
        
        await update.message.reply_text(success_message, parse_mode='Markdown')
        return True
