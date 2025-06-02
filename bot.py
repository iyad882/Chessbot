
from telegram.ext import ApplicationBuilder
from handlers.user_handlers import UserHandlers

class Bot:
    def __init__(self):
        self.application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
        self.user_handlers = UserHandlers()
        self.user_handlers.register(self.application)

    def start_bot(self):
        self.application.run_polling()

def main():
    bot = Bot()
    bot.start_bot()

if __name__ == "__main__":
    main()
