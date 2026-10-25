import os
import random
import asyncio
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
        "The ultimate Telegram pet simulator and degen ecosystem.\n"
        "• Feed, play & raid\n"
        "• Build streaks & stack coins\n"
        "• Live leaderboard tracking!\n\n"
        "<i>Use /rocket to play the 100x Crash Game!</i>"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙 Open Raid & Pet Menu", callback_data="game_raids")],
        [InlineKeyboardButton("🚀 Launch /rocket Game", callback_data="trigger_rocket")]
    ])
    
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=keyboard)

# Dedicated /rocket command for the Crash game
async def rocket_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send initial launch message
    msg = await update.message.reply_text(
        "🚀 <b>Kote Rocket Launch Initiated!</b>\n\n"
        "🐱 <i>Kote Cat is strapped in...</i>\n"
        "Multiplier: <b>1.00x</b>",
        parse_mode="HTML"
    )

    # Determine random crash point between 1.20x and 15.00x
    crash_point = round(random.uniform(1.20, 15.00), 2)
    current_multiplier = 1.00

    # Step-by-step climbing animation loop
    while current_multiplier < crash_point:
        await asyncio.sleep(0.8) # Update speed
        current_multiplier = round(current_multiplier + random.uniform(0.15, 0.45), 2)
        
        if current_multiplier >= crash_point:
            current_multiplier = crash_point
            break
            
        try:
            await msg.edit_text(
                f"🚀 <b>Kote Rocket is Climbing!</b>\n\n"
                f"📈 Multiplier: <b>{current_multiplier:.2f}x</b>\n"
                f"<i>Hold on tight, degen!</i>",
                parse_mode="HTML"
            )
        except Exception:
            pass # Prevent flood-limit crashes if updates are too fast

    # Crash / Rug-pull ending
    await asyncio.sleep(0.5)
    await msg.edit_text(
        f"💥 <b>BOOM! RUG-PULLED AT {crash_point:.2f}x!</b> 📉\n\n"
        f"🔥 The flames engulfed the rocket!\n"
        f"<i>Type /rocket to play again or /start for the main menu.</i>",
        parse_mode="HTML"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "game_raids":
        await query.edit_message_text(
            text="🪙 <b>Kote Moon Launcher & Raids Active!</b>\n\n"
                 "• Feed, play & raid.\n"
                 "• Build streaks & stack coins.\n\n"
                 "<i>Type /start to return or /rocket to play the crash game!</i>",
            parse_mode="HTML"
        )
    elif query.data == "trigger_rocket":
        await query.message.delete()
        # Simulate typing /rocket via button click
        context.args = []
        await rocket_game(query, context)

# --- 3. MAIN APPLICATION STARTUP ---
def main():
    TOKEN = "8991916858:AAGHJ3e4mXXi5rh7MfBq8uDYzr63HHj8mcw"

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rocket", rocket_game))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Kote Bot with interactive /rocket game is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
