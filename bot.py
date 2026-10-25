import os
import random
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

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

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# --- 2. TELEGRAM BOT COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = get_balance(user.id)
    
    welcome_text = (
        f"<b>🚀 Welcome to Kote Cat Bot, {user.first_name}!</b>\n\n"
        f"💰 Your Balance: <b>{balance:,} Kote Tokens</b>\n\n"
        f"• Feed, play & raid\n"
        f"• Type /rocket to enter the 100x Crash Game!"
    )
    
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
        f"🚀 <b>Kote Crash Lobby Open!</b>\n\n"
        f"👤 Player: {update.effective_user.first_name}\n"
        f"🪙 Wagered: <b>{bet_amount:,} Tokens</b>\n"
        f"⏳ <i>Waiting 10 seconds for other degens to place bets...</i>",
        parse_mode="HTML"
    )

    # 10-Second Countdown Phase
    for remaining in range(10, 0, -2):
        await asyncio.sleep(2)
        try:
            await msg.edit_text(
                f"🚀 <b>Kote Crash Lobby Open!</b>\n\n"
                f"👤 Player: {update.effective_user.first_name}\n"
                f"🪙 Wagered: <b>{bet_amount:,} Tokens</b>\n"
                f"⏳ <i>Starting in {remaining} seconds...</i>",
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

        try:
            await msg.edit_text(
                f"🚀 <b>Kote Rocket is Climbing!</b>\n\n"
                f"📈 Multiplier: <b>{current_multiplier:.2f}x</b>\n"
                f"🪙 Potential Win: <b>{int(bet_amount * current_multiplier):,} Tokens</b>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception:
            pass

    game_active = false_val = False
    
    # Clean
