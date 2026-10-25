import os
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. RENDER HEALTH CHECK SERVER ---
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
        "The ultimate Telegram pet simulator and degen ecosystem. "
        "Choose your game below to start stacking coins and raiding!"
    )
    
    # Menu with two separate game options
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙 Game 1: Moon Launcher & Raids", callback_data="game_raids")],
        [InlineKeyboardButton("🚀 Game 2: Rocket Crash (100x)", callback_data="game_crash")]
    ])
    
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "game_raids":
        # Game 1 Logic: Moon Launcher / Raid Simulation
        await query.edit_message_text(
            text="🪙 <b>Kote Moon Launcher & Raids Active!</b>\n\n"
                 "• Feed, play & raid.\n"
                 "• Build streaks & stack coins.\n"
                 "• Live leaderboard tracking!\n\n"
                 "<i>Status: Ready for your next raid! Type /start to return.</i>",
            parse_mode="HTML"
        )
        
    elif query.data == "game_crash":
        # Game 2 Logic: Simulated 100x Crash Multiplier
        crash_point = round(random.uniform(1.00, 15.00), 2)
        await query.edit_message_text(
            text=f"🚀 <b>Kote Rocket Crash Started!</b>\n\n"
                 f"The rocket launched into the degen atmosphere...\n"
                 f"💥 <b>Rug-pulled at {crash_point}x!</b>\n\n"
                 f"<i>Did you secure the bag in time? Type /start to play again.</i>",
            parse_mode="HTML"
        )

# --- 3. MAIN APPLICATION STARTUP ---
def main():
    TOKEN = "8991916858:AAGHJ3e4mXXi5rh7MfBq8uDYzr63HHj8mcw"

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Kote Bot with 2 games is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
