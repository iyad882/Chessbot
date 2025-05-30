"""
Admin command handlers for the Telegram bot
Handles commands that are restricted to administrators only
"""

import json
import logging
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from utils.auth import AuthManager

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.user_activity_file = "data/user_activity.json"
        self.user_profiles_file = "data/user_profiles.json"

    def load_user_stats(self):
        """Load user activity statistics"""
        try:
            if os.path.exists(self.user_activity_file):
                with open(self.user_activity_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load user stats: {e}")
            return {}

    def load_user_profiles(self):
        """Load user profiles with Lichess accounts and balance"""
        try:
            if os.path.exists(self.user_profiles_file):
                with open(self.user_profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load user profiles: {e}")
            return {}

    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin menu"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        user_id = update.effective_user.id
        logger.info(f"Admin menu accessed by {user_id}")

        menu_message = """
🔧 **لوحة الإدارة**

**إدارة المستخدمين:**
• `/users` - عرض جميع المستخدمين
• `/ban <user_id>` - حظر مستخدم
• `/unban <user_id>` - إلغاء حظر مستخدم

**الإحصائيات:**
• `/stats` - عرض إحصائيات البوت
• `/logs` - عرض سجلات النشاط الأخيرة

**الإذاعة:**
• `/broadcast <message>` - إرسال رسالة لجميع المستخدمين

**إدارة المديرين:**
• `/addadmin <user_id>` - إضافة مدير جديد
• `/removeadmin <user_id>` - إزالة مدير

**أمثلة الاستخدام:**
• `/ban 123456789`
• `/broadcast مرحباً بالجميع!`
• `/addadmin 987654321`

**ملاحظة:** استخدم الأوامر بحذر لأنها تؤثر على جميع المستخدمين.
        """

        await update.message.reply_text(menu_message, parse_mode='Markdown')

    async def get_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        user_id = update.effective_user.id
        logger.info(f"Stats command by admin {user_id}")

        try:
            user_stats = self.load_user_stats()
            user_profiles = self.load_user_profiles()
            
            total_users = len(user_stats)
            total_messages = sum(stats.get("message_count", 0) for stats in user_stats.values())
            
            # Calculate active users (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            active_users = sum(1 for stats in user_stats.values() 
                             if stats.get("last_seen", "") > week_ago)
            
            # Get admin count
            admin_count = len(self.auth_manager.config.admin_ids)
            banned_count = len(self.auth_manager.config.banned_users)
            
            # Get profile statistics
            total_registered = sum(1 for profile in user_profiles.values() if profile.get("registration_complete", False))
            total_balance = sum(profile.get("balance", 0) for profile in user_profiles.values())
            avg_balance = total_balance / total_registered if total_registered > 0 else 0
            
            # Count users with Lichess accounts
            lichess_users = sum(1 for profile in user_profiles.values() 
                              if profile.get("lichess_username") and profile.get("registration_complete", False))
            
            stats_message = f"""
📊 **إحصائيات البوت**

**المستخدمين:**
• إجمالي المستخدمين: {total_users}
• المستخدمين النشطين (7 أيام): {active_users}
• المسجلين بالكامل: {total_registered}
• لديهم حساب Lichess: {lichess_users}
• المحظورين: {banned_count}

**النشاط:**
• إجمالي الرسائل: {total_messages}
• متوسط الرسائل لكل مستخدم: {total_messages / total_users if total_users > 0 else 0:.1f}

**الأرصدة:**
• إجمالي الأرصدة: {total_balance} نقطة
• متوسط الرصيد: {avg_balance:.1f} نقطة

**الإدارة:**
• إجمالي المديرين: {admin_count}
• معرفات المديرين: {', '.join(map(str, self.auth_manager.config.admin_ids))}

**النظام:**
• حالة البوت: متصل ✅
• جمع البيانات: نشط
• آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await update.message.reply_text(stats_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("❌ Error retrieving statistics.")

    async def list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all users"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        user_id = update.effective_user.id
        logger.info(f"List users command by admin {user_id}")

        try:
            user_stats = self.load_user_stats()
            user_profiles = self.load_user_profiles()
            
            if not user_stats:
                await update.message.reply_text("📝 لا توجد مستخدمين في قاعدة البيانات.")
                return
            
            # Sort users by last seen (most recent first)
            sorted_users = sorted(user_stats.items(), 
                                key=lambda x: x[1].get("last_seen", ""), 
                                reverse=True)
            
            users_message = "👥 **قائمة المستخدمين:**\n\n"
            
            for user_id_str, stats in sorted_users[:15]:  # Limit to 15 users for better display
                username = stats.get("username", "لا يوجد")
                last_seen = stats.get("last_seen", "غير معروف")
                message_count = stats.get("message_count", 0)
                
                # Get profile information
                profile = user_profiles.get(user_id_str, {})
                lichess_username = profile.get("lichess_username", "غير محدد")
                balance = profile.get("balance", 0)
                is_registered = profile.get("registration_complete", False)
                
                # Format last seen
                if last_seen != "غير معروف":
                    try:
                        last_seen_date = datetime.fromisoformat(last_seen)
                        last_seen = last_seen_date.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                # Check if user is admin or banned
                status = ""
                if int(user_id_str) in self.auth_manager.config.admin_ids:
                    status = " 👑"
                elif int(user_id_str) in self.auth_manager.config.banned_users:
                    status = " 🚫"
                
                # Registration status
                reg_status = "✅" if is_registered else "❌"
                
                users_message += f"• **{user_id_str}** (@{username}){status}\n"
                users_message += f"  ├ حساب Lichess: {lichess_username}\n"
                users_message += f"  ├ الرصيد: {balance} نقطة\n"
                users_message += f"  ├ مسجل: {reg_status} | رسائل: {message_count}\n"
                users_message += f"  └ آخر نشاط: {last_seen}\n\n"
            
            if len(sorted_users) > 15:
                users_message += f"... و {len(sorted_users) - 15} مستخدم آخر\n"
            
            total_registered = sum(1 for profile in user_profiles.values() if profile.get("registration_complete", False))
            total_balance = sum(profile.get("balance", 0) for profile in user_profiles.values())
            
            users_message += f"\n**الإحصائيات:**\n"
            users_message += f"• إجمالي المستخدمين: {len(user_stats)}\n"
            users_message += f"• المسجلين: {total_registered}\n"
            users_message += f"• إجمالي الأرصدة: {total_balance} نقطة"
            
            await update.message.reply_text(users_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            await update.message.reply_text("❌ Error retrieving user list.")

    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a message to broadcast.\n"
                "Usage: `/broadcast Your message here`",
                parse_mode='Markdown'
            )
            return

        message = ' '.join(context.args)
        
        if len(message) > 4000:
            await update.message.reply_text("❌ Message too long. Maximum 4000 characters.")
            return

        logger.info(f"Broadcast initiated by admin {user_id}: {message[:50]}...")

        try:
            user_stats = self.load_user_stats()
            
            if not user_stats:
                await update.message.reply_text("❌ No users found to broadcast to.")
                return

            broadcast_message = f"📢 **Admin Broadcast:**\n\n{message}"
            
            success_count = 0
            failed_count = 0
            
            await update.message.reply_text(f"📡 Broadcasting to {len(user_stats)} users...")
            
            for target_user_id in user_stats.keys():
                try:
                    # Skip banned users
                    if int(target_user_id) in self.auth_manager.config.banned_users:
                        continue
                        
                    await context.bot.send_message(
                        chat_id=int(target_user_id),
                        text=broadcast_message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to send broadcast to {target_user_id}: {e}")
                    failed_count += 1

            result_message = f"""
✅ **Broadcast Complete**

• Successfully sent: {success_count}
• Failed to send: {failed_count}
• Total users: {len(user_stats)}

Message: "{message[:100]}{'...' if len(message) > 100 else ''}"
            """
            
            await update.message.reply_text(result_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            await update.message.reply_text("❌ Error during broadcast operation.")

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban a user"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        admin_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to ban.\n"
                "Usage: `/ban 123456789`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            
            if target_user_id in self.auth_manager.config.admin_ids:
                await update.message.reply_text("❌ Cannot ban an administrator.")
                return
            
            if self.auth_manager.config.ban_user(target_user_id):
                logger.info(f"User {target_user_id} banned by admin {admin_id}")
                await update.message.reply_text(f"✅ User {target_user_id} has been banned.")
                
                # Notify the banned user
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="🚫 You have been banned from using this bot."
                    )
                except:
                    pass  # User might have blocked the bot
                    
            else:
                await update.message.reply_text("❌ User is already banned or not found.")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format.")
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            await update.message.reply_text("❌ Error banning user.")

    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban a user"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        admin_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to unban.\n"
                "Usage: `/unban 123456789`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            
            if self.auth_manager.config.unban_user(target_user_id):
                logger.info(f"User {target_user_id} unbanned by admin {admin_id}")
                await update.message.reply_text(f"✅ User {target_user_id} has been unbanned.")
                
                # Notify the unbanned user
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="✅ You have been unbanned and can now use the bot again."
                    )
                except:
                    pass  # User might have blocked the bot
                    
            else:
                await update.message.reply_text("❌ User is not banned or not found.")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format.")
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            await update.message.reply_text("❌ Error unbanning user.")

    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new admin"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        admin_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to make admin.\n"
                "Usage: `/addadmin 123456789`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            
            if self.auth_manager.config.add_admin(target_user_id):
                logger.info(f"User {target_user_id} promoted to admin by {admin_id}")
                await update.message.reply_text(f"✅ User {target_user_id} is now an administrator.")
                
                # Notify the new admin
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="👑 Congratulations! You have been promoted to administrator."
                    )
                except:
                    pass  # User might have blocked the bot
                    
            else:
                await update.message.reply_text("❌ User is already an administrator.")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format.")
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            await update.message.reply_text("❌ Error adding administrator.")

    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove an admin"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        admin_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to remove from admins.\n"
                "Usage: `/removeadmin 123456789`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            
            if target_user_id == admin_id:
                await update.message.reply_text("❌ You cannot remove yourself as administrator.")
                return
            
            if self.auth_manager.config.remove_admin(target_user_id):
                logger.info(f"Admin {target_user_id} removed by {admin_id}")
                await update.message.reply_text(f"✅ User {target_user_id} is no longer an administrator.")
                
                # Notify the removed admin
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="ℹ️ Your administrator privileges have been removed."
                    )
                except:
                    pass  # User might have blocked the bot
                    
            else:
                await update.message.reply_text("❌ User is not an administrator.")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format.")
        except Exception as e:
            logger.error(f"Error removing admin: {e}")
            await update.message.reply_text("❌ Error removing administrator.")

    async def get_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent logs"""
        if not await self.auth_manager.check_admin_access(update, context):
            return

        user_id = update.effective_user.id
        logger.info(f"Logs requested by admin {user_id}")

        try:
            # Read recent log entries
            log_file = "bot.log"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Get last 20 lines
                recent_logs = lines[-20:] if len(lines) > 20 else lines
                
                if recent_logs:
                    logs_message = "📋 **Recent Logs:**\n\n```\n"
                    for line in recent_logs:
                        # Truncate long lines
                        if len(line) > 100:
                            line = line[:97] + "...\n"
                        logs_message += line
                    logs_message += "```"
                    
                    if len(logs_message) > 4000:
                        logs_message = logs_message[:4000] + "```"
                    
                    await update.message.reply_text(logs_message, parse_mode='Markdown')
                else:
                    await update.message.reply_text("📋 No logs found.")
            else:
                await update.message.reply_text("📋 Log file not found.")
                
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            await update.message.reply_text("❌ Error reading log file.")
