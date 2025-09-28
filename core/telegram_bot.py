import os, requests

class TelegramBot:
    def __init__(self):
        self.token=os.getenv("TELEGRAM_TOKEN")
        self.channel=os.getenv("TELEGRAM_CHANNEL")
        self.api_url=f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_alert(self,message):
        if not self.token or not self.channel: 
            return
        try:
            requests.post(self.api_url,data={"chat_id":self.channel,"text":message})
        except Exception as e: 
            print("Telegram error",e)
