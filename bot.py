import os
import random
import asyncio
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- IN-MEMORY USER BALANCES ---
user_balances = {}

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
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

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

    # Check bet amount argument (e.g. /rocket 500)
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

    # Deduct bet and start lobby phase
    user_balances[user_id] -= bet_amount
    
    msg = await update.message.reply_text(
        f"""🚀 <b>Kote Crash Lobby Open!</b>

👤 Player: {update.effective_user.first_name}
🪙 Wagered: <b>{bet_amount:,} Tokens</b>
⏳ <i>Waiting 10 seconds for other degens to place bets...</i>""",
        parse_mode="HTML"
    )

    # 10-Second Countdown Phase
    for remaining in range(10, 0, -2):
        await asyncio.sleep(2)
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

    # --- LAUNCH PHASE ---
    crash_point = round(random.uniform(1.20, 15.00), 2)
    current_multiplier = 1.00
    game_active = True

    class GameState:
        claimed = False
        cashed_out_at = 0.0

    state = GameState()

    async def check_claim_callback(update_cb: Update, context_cb: ContextTypes.DEFAULT_TYPE):
        query = update_cb.callback_query
        if query.message.message_id == msg.message_id:
            if query.from_user.id == user_id:
                if game_active and not state.claimed:
                    state.claimed = True
                    state.cashed_out_at = current_multiplier
                    winnings = int(bet_amount * current_multiplier)
                    user_balances[user_id] += winnings
                    await query.answer(f"🎉 Secured {winnings:,} tokens!")
                else:
                    await query.answer("❌ Already claimed or game ended!", show_alert=True)
            else:
                await query.answer("❌ This isn't your rocket game session!", show_alert=True)

    handler = CallbackQueryHandler(check_claim_callback, pattern="claim_bag")
    context.application.add_handler(handler)

    # Climbing loop
    while current_multiplier < crash_point and not state.claimed:
        await asyncio.sleep(0.7)
        current_multiplier = round(current_multiplier + random.uniform(0.10, 0.35), 2)
        
        if current_multiplier >= crash_point:
            current_multiplier = crash_point
            break

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"💰 CLAIM BAG ({current_multiplier:.2f}x)", callback_data="claim_bag")]
        ])

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

    game_active = False
    
    try:
        context.application.remove_handler(handler)
    except Exception:
        pass

    # End game result message
    if state.claimed:
        winnings = int(bet_amount * state.cashed_out_at)
        new_bal = get_balance(user_id)
        await msg.edit_text(
            f"""🎉 <b>SUCCESS! Secured the Bag!</b>

📈 Cashed out at: <b>{state.cashed_out_at:.2f}x</b>
💰 Won: <b>+{winnings:,} Tokens</b>
🏦 New Balance: <b>{new_bal:,} Tokens</b>

<i>Type /rocket [amount] to play again!</i>""",
            parse_mode="HTML"
        )
    else:
        new_bal = get_balance(user_id)
        await msg.edit_text(
            f"""💥 <b>BOOM! RUG-PULLED AT {crash_point:.2f}x!</b>

📉 You waited too long and lost your {bet_amount:,} token wager.
🏦 Balance remaining: <b>{new_bal:,} Tokens</b>

<i>Type /rocket [amount] to try and win it back!</i>""",
            parse_mode="HTML"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_rocket_prompt":
        await query.message.reply_text("💡 Type `/rocket 1000` (or just `/rocket`) in chat to place your bet and launch!")

# --- 3. MAIN APPLICATION STARTUP ---
def main():
    TOKEN = "8991916858:AAGHJ3e4mXXi5rh7MfBq8uDYzr63HHj8mcw"

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rocket", rocket_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
