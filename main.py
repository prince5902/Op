import os
import re
import asyncio
import requests
import phonenumbers
from phonenumbers import geocoder
from flask import Flask
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes
)

try:
    from telegram import CopyTextButton
except ImportError:
    CopyTextButton = None

# === CONFIGURATION ===
BOT_TOKEN = "8658535528:AAG_LrE7L5TRkTM7fkC-RaqPIR8N1qOfttk"
PANEL_API_KEY = "ZNX_ZMJG4X1QBNIUR1HDSZ1P31ED"
GROUP_ID = -1004342739367

API_BASE_URL = "https://numberpanel.tech/api"
OTP_FEED_URL = "https://numberpanel.tech/api/otp?count=200"
POLL_INTERVAL = 10

# Flask সার্ভার (Render-এ বট সচল রাখার জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "Number Panel Pro Bot is active and running!"

def get_country_info(phone_number):
    if not str(phone_number).startswith('+'):
        phone_number = '+' + str(phone_number)
    try:
        parsed = phonenumbers.parse(phone_number)
        region = phonenumbers.region_code_for_number(parsed)
        if region:
            flag = chr(ord(region[0]) + 127397) + chr(ord(region[1]) + 127397)
        else:
            flag = "🏳️"
        iso = region or "UN"
        return flag, iso
    except:
        return "🏳️", "UN"

def extract_otp(msg):
    otp_match = re.search(r'\d{3}[-\s]?\d{3,4}|\d{4,8}', str(msg))
    return otp_match.group(0) if otp_match else 'Unknown'

# গ্রুপে ওটিপি ফরোয়ার্ড করার ফাংশন
async def send_to_group(bot, entry):
    service = entry[0]
    num = entry[1]
    msg = entry[2]
    
    flag, iso = get_country_info(num)
    otp = extract_otp(msg)
    
    text = f"{flag} <b>#{iso} 📱 {service} {num}</b> ➡️"
    
    if CopyTextButton:
        try:
            row1 = [InlineKeyboardButton(text=f"🔑 {otp}", copy_text=CopyTextButton(text=otp))]
        except:
            row1 = [InlineKeyboardButton(text=f"🔑 {otp}", callback_data="noop")]
    else:
        row1 = [InlineKeyboardButton(text=f"🔑 {otp}", callback_data="noop")]
        
    markup = InlineKeyboardMarkup([
        row1,
        [InlineKeyboardButton(text="⚡ OTP Panel", url="https://t.me/XclusoRPanelBot")]
    ])
    
    try:
        await bot.send_message(
            chat_id=GROUP_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup
        )
    except Exception as e:
        print(f"❌ Failed to send to group: {e}")

# ব্যাকগ্রাউন্ডে প্যানেলের ফিড চেক করার লুপ
async def background_otp_forwarder(bot):
    seen_otps = set()
    try:
        resp = requests.get(OTP_FEED_URL).json()
        for item in resp:
            uid = f"{item[0]}_{item[1]}_{item[3]}"
            seen_otps.add(uid)
    except:
        pass
        
    while True:
        try:
            resp = requests.get(OTP_FEED_URL).json()
            for item in reversed(resp):
                uid = f"{item[0]}_{item[1]}_{item[3]}"
                if uid not in seen_otps:
                    seen_otps.add(uid)
                    await send_to_group(bot, item)
                    await asyncio.sleep(0.5)
        except:
            pass
        await asyncio.sleep(POLL_INTERVAL)

# /start কমান্ড ও মেইন মেনু
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👑 **NUMBER BOT**\n\n"
        "🚀 **Welcome to Number & OTP Service**\n\n"
        "✅ Choose an option below to continue using the bot.\n\n"
        "💎 **Premium OTP Service**\n"
        "🛡️ **DEVELOPED BY SIJAN** 🛡️"
    )
    
    keyboard = [
        [InlineKeyboardButton("📱 GET NUMBER", callback_data="menu_services"), InlineKeyboardButton("🔍 Search Number", callback_data="search_num")],
        [InlineKeyboardButton("👑 TRAFFIC", callback_data="traffic"), InlineKeyboardButton("🔐 2FA ONLINE", callback_data="2fa")],
        [InlineKeyboardButton("🎁 Refer", callback_data="refer"), InlineKeyboardButton("📅 WITHDRAWAL", callback_data="withdrawal")],
        [InlineKeyboardButton("👤 SUPPORT", url="https://t.me/")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_text, reply_markup=markup, parse_mode="Markdown")

# সার্ভিস সিলেকশন মেনু
async def menu_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "📍 **Select a service:**"
    keyboard = [
        [InlineKeyboardButton("💬 WHATSAPP", callback_data="get_WhatsApp_BD"), InlineKeyboardButton("✈️ TELEGRAM", callback_data="get_Telegram_BD")],
        [InlineKeyboardButton("📘 FACEBOOK", callback_data="get_Facebook_BD"), InlineKeyboardButton("📸 INSTAGRAM", callback_data="get_Instagram_BD")],
        [InlineKeyboardButton("🎵 TIKTOK", callback_data="get_TikTok_BD"), InlineKeyboardButton("🌐 GOOGLE", callback_data="get_Google_BD")],
        [InlineKeyboardButton("❌ Close", callback_data="main_menu")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# প্যানেল থেকে অটো নম্বর রিকোয়েস্ট করে ডিসপ্লে করা
async def fetch_and_show_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Fetching number from panel...")
    
    data_parts = query.data.split("_")
    service = data_parts[1]
    country = "BD" if len(data_parts) < 3 else data_parts[2]

    headers = {
        "Authorization": f"Bearer {PANEL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "service": service,
        "country": country
    }

    try:
        response = requests.post(f"{API_BASE_URL}/request_number", json=payload, headers=headers)
        res_data = response.json()

        if res_data.get("success"):
            number = res_data.get("number")
            
            text = (
                f"🌐 **Country:** 🇳🇬 Nigeria (NG)\n"
                f"🛠️ **Service:** {service}\n\n"
                f"⏳ **Waiting for OTP...**"
            )
            
            if CopyTextButton:
                try:
                    num_btn = InlineKeyboardButton(text=f"🇳🇬 📋 {number}", copy_text=CopyTextButton(text=number))
                except:
                    num_btn = InlineKeyboardButton(text=f"🇳🇬 📱 {number}", callback_data=f"otp_{number}")
            else:
                num_btn = InlineKeyboardButton(text=f"🇳🇬 📱 {number}", callback_data=f"otp_{number}")

            keyboard = [
                [num_btn],
                [InlineKeyboardButton("🗑️ Remove CC", callback_data="main_menu")],
                [InlineKeyboardButton("🔄 Change Number", callback_data="menu_services"), InlineKeyboardButton("🛡️ OTP Group", url=f"https://t.me/{str(GROUP_ID).replace('-100', '')}")],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            error_msg = res_data.get("error", "Unknown error")
            await query.answer(f"❌ প্যানেল এরর: {error_msg}", show_alert=True)
    except Exception as e:
        await query.answer(f"⚠️ Error: {str(e)}", show_alert=True)

# বাটন হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "main_menu":
        await start(update, context)
    elif data == "menu_services":
        await menu_services(update, context)
    elif data.startswith("get_"):
        await fetch_and_show_number(update, context)
    else:
        await query.answer("এই ফিচারটি শীঘ্রই আসছে!", show_alert=True)

async def post_init(application):
    application.create_task(background_otp_forwarder(application.bot))

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Pro Number Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    main()
