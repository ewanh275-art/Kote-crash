async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""<b>🚀 Welcome to Kote Cat Bot, {user.first_name}!</b>

The ultimate degen ecosystem with smooth visual mini-apps.
Tap below to open the live visual rocket game!"""
    
    # Updated with ?v=99 to force Telegram to load the new code
    webapp_url = "https://ewanh275-art.github.io/Kote-crash/?v=99"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Open Visual Rocket Game 🚀", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=keyboard)

async def rocket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    webapp_url = "https://ewanh275-art.github.io/Kote-crash/?v=99"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Launch Visual Crash Game", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await update.message.reply_text(
        "🚀 <b>Kote Visual Rocket Game Ready!</b>\n\nClick below to open the fluid 60fps web app, watch the rocket lift off, and cash out instantly!",
        parse_mode="HTML",
        reply_markup=keyboard
    )
