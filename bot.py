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

# --- IN-MEMORY DATA STORES ---
user_balances = {}
active_games = {}  # {user_id: {"bet": int, "mult": float, "claimed": bool, "active": bool, "msg_id": int}}

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

    # Check if user already has an active game
    if user_id in active_games and active_games[user_id].get("active"):
        await update.message.reply_text("⚠️ You already have an active rocket launch in progress!")
        return

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
            await update.message.reply_text
