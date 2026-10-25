import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. RENDER HEALTH CHECK SERVER ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kote Bot Mini App is live 24/7!")
    
    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# --- 2. TELEGRAM BOT COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""<b>🚀 Welcome to Kote Cat Bot, {user.first_name}!</b>

The ultimate degen ecosystem with smooth visual mini-apps.
Tap below to open the live visual rocket game!"""
    
    # Replace with your actual GitHub Pages URL from Step 2
    webapp_url = "https://yourusername.github.io/kote-cat-bot/"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Open Visual Rocket Game 🚀", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=keyboard)

async def rocket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    webapp_url = "https://yourusername.github.io/kote-cat-bot/"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Launch Visual Crash Game", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await update.message.reply_text(
        "🚀 <b>Kote Visual Rocket Game Ready!</b>\n\nClick below to open the fluid 60fps web app, watch the rocket lift off, and cash out instantly!",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# --- 3. MAIN APPLICATION STARTUP ---
def main():
    TOKEN = "8991916858:AAGHJ3e4mXXi5rh7MfBq8uDYzr63HHj8mcw"

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rocket", rocket_command))

    application.run_polling()

if __name__ == "__main__":
    main()
