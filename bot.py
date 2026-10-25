import os
import random
import asyncio
import threading
import logging
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- IN-MEMORY DATA STORES ---
user_balances = {}
active_games = {}

def get_balance(user_id):
    if user_id not in user_balances:
        user_balances[user_id] = 10000  # Default starting tokens
    return user_balances[user_id]

# --- 1. RENDER HEALTH CHECK SERVER ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kote Bot is live and running 24/7!")
    
    def log_message(self, format, *args):
        return

def run_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info(f"Health server bound to port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server failed: {e}")

# --- 2. TELEGRAM BOT COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = get_balance(user.id)
    
    welcome_text = f"""<b>🚀 Welcome to Kote Cat Bot, {user.first_name}!</b>

💰 Your Balance: <b>{balance:,} Kote Tokens</b>

• Feed, play & raid
• Type /rocket to enter the 100x Crash Game!"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Play /rocket Crash Game", callback_data="start_rocket_prompt")]
    ])
    
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=keyboard)

async def rocket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)

    # Prevent concurrent games per user
    if user_id in active_games and active_games[user_id].get("active"):
        await update.message.reply_text("⚠️ You already have an active rocket launch in progress!")
        return

    # Parse bet amount
    if context.args:
        try:
            bet_amount = int(context.args[0])
            if bet_amount <= 0:
                await update.message.reply_text("❌ Bet must be greater than 0 tokens.")
                return
            if bet_amount > balance:
                await update.message.reply_text(f"❌ You only have {balance:,} tokens!")
                return
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number, e.g., `/rocket 500`", parse_mode="HTML")
            return
    else:
        bet_amount = 500
        if balance < bet_amount:
            bet_amount = balance

    if balance < bet_amount or bet_amount <= 0:
        await update.message.reply_text("❌ Insufficient tokens to place bet!")
        return

    # Deduct bet
    user_balances[user_id] -= bet_amount
    
    msg = await update.message.reply_text(
        f"""🚀 <b>Kote Crash Lobby Open!</b>

👤 Player: {update.effective_user.first_name}
🪙 Wagered: <b>{bet_amount:,} Tokens</b>
⏳ <i>Waiting 10 seconds for launch...</i>""",
        parse_mode="HTML"
    )

    # Initialize active session state
    active_games[user_id] = {
        "bet": bet_amount,
        "mult": 1.00,
        "claimed": False,
        "cashed_at": 0.0,
        "active": True,
        "msg_id": msg.message_id
    }

    # 10-Second Lobby Countdown
    for remaining in range(10, 0, -2):
        await asyncio.sleep(2)
        if active_games[user_id]["claimed"]:
            break
        try:
            await msg.edit_text(
                f"""🚀 <b>Kote Crash Lobby Open!</b>

👤 Player: {update.effective_user.first_name}
🪙 Wagered: <b>{bet_amount:,} Tokens</b>
⏳ <i>Starting in {remaining} seconds...</i>""",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # --- WEIGHTED CRASH ALGORITHM ---
    # 45% Chance: Early Rug (1.00x - 1.99x)
    # 40% Chance: Mid Range (2.00x - 4.99x)
    # 15% Chance: Degen Moon (5.00x - 15.00x)
    roll = random.random()
    if roll < 0.45:
        crash_point = round(random.uniform(1.00, 1.99), 2)
    elif roll < 0.85:
        crash_point = round(random.uniform(2.00, 4.99), 2)
    else:
        crash_point = round(random.uniform(5.00, 15.00), 2)

    current_multiplier = 1.00
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 CLAIM BAG! 💰", callback_data=f"claim_{user_id}")]
    ])

    # Rocket Climb Loop
    while current_multiplier < crash_point:
        # Exit immediately if the user claimed via callback
        if active_games[user_id]["claimed"]:
            break

        await asyncio.sleep(0.9)  # Smooth update pacing to avoid Telegram rate limits
        
        if active_games[user_id]["claimed"]:
            break

        current_multiplier = round(current_multiplier + random.uniform(0.15, 0.40), 2)
        if current_multiplier >= crash_point:
            current_multiplier = crash_point
            break

        active_games[user_id]["mult"] = current_multiplier
        potential_win = int(bet_amount * current_multiplier)

        try:
            await msg.edit_text(
                f"""🚀 <b>Kote Rocket is Climbing!</b>

📈 Multiplier: <b>{current_multiplier:.2f}x</b>
🪙 Potential Win: <b>{potential_win:,} Tokens</b>""",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception:
            pass

    # Mark loop ended
    session = active_games[user_id]
    
    # If not claimed, handle crash result
    if not session["claimed"]:
        session["active"] = False
        new_bal = get_balance(user_id)
        try:
            await msg.edit_text(
                f"""💥 <b>BOOM! RUG-PULLED AT {crash_point:.2f}x!</b>

📉 You waited too long and lost your {bet_amount:,} token wager.
🏦 Balance remaining: <b>{new_bal:,} Tokens</b>

<i>Type /rocket [amount] to try and win it back!</i>""",
                parse_mode="HTML"
            )
        except Exception:
            pass

# --- GLOBAL BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "start_rocket_prompt":
        await query.answer()
        await query.message.reply_text("💡 Type `/rocket 1000` (or just `/rocket`) in chat to place your bet and launch!")
        return

    if data.startswith("claim_"):
        target_user_id = int(data.split("_")[1])
        clicker_id = query.from_user.id

        if clicker_id != target_user_id:
            await query.answer("❌ This is not your rocket session!", show_alert=True)
            return

        session = active_games.get(clicker_id)
        
        # Check active state instantly
        if session and session.get("active") and not session.get("claimed"):
            # 1. LOCK STATE IMMEDIATELY IN MEMORY
            session["claimed"] = True
            session["active"] = False
            session["cashed_at"] = session["mult"]
            
            bet_amount = session["bet"]
            multiplier = session["mult"]
            winnings = int(bet_amount * multiplier)
            user_balances[clicker_id] += winnings
            new_bal = get_balance(clicker_id)

            # 2. INSTANT POPUP NOTIFICATION TO USER TELEGRAM CLIENT
            await query.answer(f"🎉 BAG SECURED! Won {winnings:,} tokens at {multiplier:.2f}x!", show_alert=True)

            # 3. UPDATE CHAT MESSAGE WITH FINAL SCORE
            try:
                await query.edit_message_text(
                    f"""🎉 <b>SUCCESS! Secured the Bag!</b>

📈 Cashed out at: <b>{multiplier:.2f}x</b>
💰 Won: <b>+{winnings:,} Tokens</b>
🏦 New Balance: <b>{new_bal:,} Tokens</b>

<i>Type /rocket [amount] to play again!</i>""",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error editing message on claim: {e}")
        else:
            await query.answer("❌ Game already ended or claimed!", show_alert=True)

# --- 3. MAIN APPLICATION STARTUP ---
def main():
    TOKEN = "8991916858:AAGHJ3e4mXXi5rh7MfBq8uDYzr63HHj8mcw"

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    logger.info("Initializing Telegram bot application...")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rocket", rocket_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Starting bot polling loop...")
    application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal startup error: {e}")
        traceback.print_exc()
