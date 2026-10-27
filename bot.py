import os
import json
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Leaderboard Memory Store (starts with a default entry)
global_leaderboard = [
    {"name": "KoteCadet 🐱", "score": "2.50x"}
]

# --- 1. RENDER HEALTH CHECK & API SERVER ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        # Endpoint to fetch the global leaderboard
        if parsed_url.path == "/api/leaderboard":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(global_leaderboard).encode("utf-8"))
            return
            
        # Health check endpoint
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kote Bot Mini App is live 24/7!")
    
    def do_POST(self):
        parsed_url = urlparse(self.path)
        
        # Endpoint to submit a new score to the global leaderboard
        if parsed_url.path == "/api/submit":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                name = data.get("name")
                score = data.get("score")
                
                if name and score:
                    global_leaderboard.append({"name": name, "score": score})
                    # Keep only top 50 highest scores sorted
                    global_leaderboard.sort(key=lambda x: float(x["score"].replace("x", "")), reverse=True)
                    if len(global_leaderboard) > 50:
                        global_leaderboard.pop()
                        
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success"}).encode("utf-8"))
                    return
            except Exception as e:
                logger.error(f"Error saving score: {e}")
                
            self.send_response(400)
            self.end_headers()
            return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
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
    
    webapp_url = "https://ewanh275-art.github.io/Kote-crash/"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Open Visual Rocket Game 🚀", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=keyboard)

async def rocket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    webapp_url = "https://ewanh275-art.github.io/Kote-crash/"
    
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
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        logger.error("CRITICAL: No BOT_TOKEN environment variable found. Please configure it in Render settings.")
        return

    # Start health check & API server for Render web service requirement
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rocket", rocket_command))

    logger.info("Starting Telegram bot polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
