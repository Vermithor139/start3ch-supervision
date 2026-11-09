import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# --- CONFIGURATION ---
JSONBIN_BIN_ID = "6aec5042ac6210605a6e90dd" 
JSONBIN_API_KEY = "$2a$10$QGSNKJ15elRBp8tFd/fBWeJXuX/SMb6lyKj/YL84XxJsGIU9XXA2." 
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
HEADERS = {'X-Master-Key': JSONBIN_API_KEY, 'Content-Type': 'application/json'}

# PASTE YOUR TOKEN BELOW INSIDE THE QUOTES
TELEGRAM_BOT_TOKEN = "9005398733:AAGbhA1GHAWvjr53msJ0s1yND6h0_RZNCB8" 

NAME, PHONE = range(2)
user_data_store = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def load_db():
    try:
        response = requests.get(JSONBIN_URL + "/latest", headers=HEADERS)
        return response.json().get('record', {"agents": ["ALL"], "clients": {}})
    except:
        return {"agents": ["ALL"], "clients": {}}

def save_db(db):
    try:
        requests.put(JSONBIN_URL, json=db, headers=HEADERS)
        return True
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇦🇷🇵🇾 ¡Bienvenido al Canal VIP de Señales MT5!\n\n"
        "Para recibir las señales diarias de alta probabilidad, por favor ingresa tu *Nombre Completo*:",
        parse_mode='Markdown'
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.message.chat_id] = {'name': update.message.text}
    await update.message.reply_text("Gracias. Ahora, por favor ingresa tu *Número de WhatsApp* (con código de país, ej: +54 9 11...):", parse_mode='Markdown')
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    name = user_data_store[chat_id]['name']
    phone = update.message.text
    
    db = load_db()
    tx_id = 'TX-' + str(random.randint(100000, 999999))
    country = "Argentina" if "+54" in phone else "Paraguay" if "+595" in phone else "Unknown"
    flag = "🇦🇷" if country == "Argentina" else "🇵🇾"
    
    new_client = {
        "txId": tx_id, "agent": "UNASSIGNED", "name": name, "country": country, "flag": flag,
        "phone": phone, "email": f"{name.lower().replace(' ', '.')}@telegram.user",
        "lastLogin": "Just now", "balance": 0, "withdrawn": 0, "deposit": 0,
        "status": "NEW LEAD", "retention": "NEW", "subStatus": "POTENTIAL",
        "source": "Telegram Bot", "comment": "Lead captured via Telegram Bot.",
        "comments": [], "transactions": [], "withdrawals": []
    }
    db['clients'][tx_id] = new_client
    save_db(db)
    
    await update.message.reply_text(
        f"✅ ¡Registro exitoso, {name}!\n\n"
        f"Has sido añadido a la lista VIP. Un asesor te contactará pronto al WhatsApp ({phone}).\n\n"
        "📈 ¡Prepárate para operar con ventaja!"
    )
    del user_data_store[chat_id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registro cancelado. Escribe /start para intentar de nuevo.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(conv_handler)
    print("Bot is running... Share this link: https://t.me/VerumMT5_Signals_bot")
    app.run_polling()

if __name__ == '__main__':
    main()