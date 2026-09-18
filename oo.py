import asyncio
import re
import json
import requests
import phonenumbers
from phonenumbers import geocoder
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

try:
    from telegram import CopyTextButton
except ImportError:
    CopyTextButton = None

BOT_TOKEN = "8389209190:AAHGqxrGlaZv0aGaEOXtJ0DmYyqATzE2OXU"
GROUP_ID = -1004342739367

# আপনার দেওয়া Telegram User ID
ADMIN_ID = 7270449654

API_KEY = "ZNX_ZMJG4X1QBNIUR1HDSZ1P31ED"
API_URL = "https://www.zenexnetwork.com/api/v1/global-broadcast"
POLL_INTERVAL = 6

# ইউজার ডাটাবেজ (ব্রডকাস্টের জন্য)
USER_FILE = "users.json"

def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_users(users):
    try:
        with open(USER_FILE, "w") as f:
            json.dump(list(users), f)
    except Exception as e:
        print(f"Error saving users: {e}")

bot_users = load_users()

APP_EMOJIS = {
    "whatsapp": "💬",
    "telegram": "✈️",
    "facebook": "📘",
    "instagram": "📸",
    "tiktok": "🎵",
    "google": "🌐",
    "twitter": "🐦"
}

def get_app_emoji(service_name):
    service_name = str(service_name).lower()
    for key, emoji in APP_EMOJIS.items():
        if key in service_name:
            return emoji
    return "📱"

def get_country_info(phone_number):
    if not str(phone_number).startswith('+'):
        phone_number = '+' + str(phone_number)
    try:
        parsed = phonenumbers.parse(phone_number)
        country_name = geocoder.country_name_for_number(parsed, "en") or "Unknown"
        region = phonenumbers.region_code_for_number(parsed)
        if region:
            flag = chr(ord(region[0]) + 127397) + chr(ord(region[1]) + 127397)
        else:
            flag = "🏳️"
        iso = region or "UN"
        return country_name, flag, iso
    except:
        return "Unknown", "🏳️", "UN"

def extract_otp(msg):
    otp_match = re.search(r'\d{3}[-\s]?\d{3,4}|\d{4,8}', str(msg))
    return otp_match.group(0) if otp_match else 'Unknown'

def mask_number(num):
    num = str(num).replace('+', '')
    if len(num) <= 6:
        return num
    return num[:3] + "x" * (len(num) - 6) + num[-3:]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    
    # ইউজার আইডি সেভ করা (ব্রডকাস্টের জন্য)
    if user_id not in bot_users:
        bot_users.add(user_id)
        save_users(bot_users)
    
    msg1 = (
        "💯% <b>System Ready!</b>\n"
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 100%\n\n"
        "╭───[ <b>ROOT@SIJAN TECH OTP</b> ]────────────\n"
        "├─🐱 <b>ACCESS GRANTED</b>\n"
        f"└─➡️ Hey <b>{user_name}</b>, Welcome to Free OTP Bot!"
    )
    
    msg2 = (
        "╔═════════════════════════╗\n"
        "       👑 <b>NUMBER BOT</b>\n"
        "╚═════════════════════════╝\n\n"
        "🚀 <b>Welcome to Number & OTP Service</b>\n"
        "━━━━━━━\n"
        "🛑 <b>Choose an option below to continue using the bot.</b>\n"
        "━━━━━━━\n\n"
        "💎 <i>Premium OTP Service</i>\n"
        "🛡️ <b>DEVELOPED BY SIJAN</b> 🛡️"
    )
    
    keyboard = [
        [KeyboardButton("📱 GET NUMBER"), KeyboardButton("🔍 Search Number")],
        [KeyboardButton("👑 TRAFFIC"), KeyboardButton("🌐 2FA ONLINE")],
        [KeyboardButton("🎁 Refer"), KeyboardButton("🏧 WITHDRAWAL")],
        [KeyboardButton("👤 SUPPORT")]
    ]
    
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("⚙️ Admin Panel")])
        
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(msg1, parse_mode=ParseMode.HTML)
    await update.message.reply_text(msg2, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # ব্রডকাস্ট মেসেজ ওয়েটিং চেক
    if context.user_data.get("waiting_for_broadcast"):
        context.user_data["waiting_for_broadcast"] = False
        await update.message.reply_text("📢 <b>ব্রডকাস্ট শুরু হচ্ছে...</b>", parse_mode=ParseMode.HTML)
        
        success = 0
        failed = 0
        for uid in list(bot_users):
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 <b>[ANNOUNCEMENT]</b>\n\n{text}", parse_mode=ParseMode.HTML)
                success += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1
                
        await update.message.reply_text(f"✅ <b>ব্রডকাস্ট সম্পন্ন!</b>\n\nমেসেজ সফল: {success}\nব্যর্থ: {failed}", parse_mode=ParseMode.HTML)
        return

    if text == "⚙️ Admin Panel":
        if user_id == ADMIN_ID:
            admin_text = (
                "🛠️ <b>ADMIN PANEL</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 মোট রেজিস্টার্ড মেম্বার: <b>{len(bot_users)}</b>\n\n"
                "কন্ট্রোল করতে নিচের অপশন ব্যবহার করুন:"
            )
            keyboard = [
                [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
                [InlineKeyboardButton("📊 Total Users", callback_data="admin_stats")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(admin_text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await update.message.reply_text("❌ আপনার এই সেকশনে প্রবেশের অনুমতি নেই।")
            
    elif text == "📱 GET NUMBER":
        headers = {"User-Agent": "Mozilla/5.0", "mapikey": API_KEY}
        try:
            res = requests.get(API_URL, headers=headers, timeout=10)
            data = res.json()
            items = data if isinstance(data, list) else data.get("data", data.get("otps", []))
            
            if items:
                msg_text = "📱 <b>AVAILABLE LIVE NUMBERS:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                buttons = []
                for item in items[:5]:
                    service = item.get("service") or item.get("app", "Service")
                    num = item.get("number") or item.get("phone") or "000000"
                    country_name, flag, iso = get_country_info(num)
                    msg_text += f"{flag} <b>{service.capitalize()}</b>: <code>{num}</code>\n"
                
                msg_text += "\nটিপস: উপরের নাম্বারে ওটিপি পাঠালে কোডটি সরাসরি এখানে ও গ্রুপে চলে আসবে!"
                await update.message.reply_text(msg_text, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text("❌ এই মুহূর্তে এপিআই থেকে কোনো অ্যাক্টিভ নাম্বার পাওয়া যায়নি।")
        except Exception as e:
            await update.message.reply_text("⚠️ নাম্বার লোড করতে সমস্যা হয়েছে, কিছুক্ষণ পর চেষ্টা করুন।")
            
    elif text == "👤 SUPPORT":
        await update.message.reply_text("📞 সাপোর্ট পেতে যোগাযোগ করুন: @xclusor")
    else:
        await update.message.reply_text(f"আপনার সিলেক্ট করা মেনু: {text}")

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_broadcast":
        if query.from_user.id == ADMIN_ID:
            context.user_data["waiting_for_broadcast"] = True
            await query.edit_message_text("✍️ আপনার ব্রডকাস্ট মেসেজটি লিখে পাঠান:")
    elif query.data == "admin_stats":
        await query.edit_message_text(f"📊 মোট ব্যবহারকারী: {len(bot_users)} জন।")

async def send_to_group_and_users(bot, service, num, msg):
    country_name, flag, iso = get_country_info(num)
    app_emoji = get_app_emoji(service)
    masked = mask_number(num)
    otp = extract_otp(msg)
    
    text = f"{flag} <b>#{iso} {app_emoji}{service} {masked}</b>"
    
    if CopyTextButton:
        try:
            row1 = [InlineKeyboardButton(text=f"{otp}", copy_text=CopyTextButton(text=otp))]
        except:
            row1 = [InlineKeyboardButton(text=f"🔑 {otp}", callback_data="noop")]
    else:
        row1 = [InlineKeyboardButton(text=f"🔑 {otp}", callback_data="noop")]
        
    row2 = [
        InlineKeyboardButton(text="Methods", url="https://youtube.com/@xclusor"),
        InlineKeyboardButton(text="Channel", url="https://t.me/+a0zwxrh1Il43NjM1")
    ]
    row3 = [InlineKeyboardButton(text="OTP Panel", url="https://www.zenexnetwork.com")]
    markup = InlineKeyboardMarkup([row1, row2, row3])
    
    # ১. টেলিগ্রাম গ্রুপে ফরোয়ার্ড করা
    try:
        await bot.send_message(
            chat_id=GROUP_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"❌ Failed to send to group: {e}")

async def poll_api(bot):
    seen_otps = set()
    headers = {"User-Agent": "Mozilla/5.0", "mapikey": API_KEY}
    
    while True:
        try:
            res = requests.get(API_URL, headers=headers, timeout=10)
            data = res.json()
            items = data if isinstance(data, list) else data.get("data", data.get("otps", []))
            
            for item in reversed(items):
                service = item.get("service") or item.get("app", "Service")
                num = item.get("number") or item.get("phone") or item.get("range", "000000")
                msg = item.get("message") or item.get("otp") or item.get("sms", "")
                nid = item.get("nid", f"{service}_{num}_{msg}")
                
                if nid not in seen_otps:
                    seen_otps.add(nid)
                    await send_to_group_and_users(bot, service, num, msg)
                    await asyncio.sleep(1)
                    
            if len(seen_otps) > 10000:
                seen_otps = set(list(seen_otps)[-5000:])
        except Exception as e:
            print(f"⚠️ Error fetching API: {e}")
            
        await asyncio.sleep(POLL_INTERVAL)

async def main():
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    asyncio.create_task(poll_api(app.bot))
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

