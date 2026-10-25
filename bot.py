import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. RENDER HEALTH CHECK SERVER ---
# This lightweight server responds to ping requests on port 10000 
# to prevent Render's free tier from spinning down your bot.
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kote Bot is live and running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# --- 2. TELEGRAM BOT COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "<b>🚀 Welcome to Kote Cat Bot!</b>\n\n"
        "The ultimate Telegram pet simulator and crash game ecosystem[span_0](start_span)[span_0](end_span). "
        "Feed, play, and send Kote on wild crypto raids[span_1](start_span)[span_1](end_span)!"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")

async def kote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Kote is fired up and ready to rocket to 100x!")

# --- 3. MAIN APPLICATION STARTUP ---
def main():
    # Your provided Telegram Bot Token
    TOKEN = "8991916858:AAGHJ3e4mXXi5rh7MfBq8uDYzr63HHj8mcw"

    # Start the HTTP server thread in the background for Render uptime
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Build and run the Telegram Bot application using python-telegram-bot
    application = ApplicationBuilder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("kote", kote))

    print("Kote Bot is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()

