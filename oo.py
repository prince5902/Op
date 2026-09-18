import asyncio
import re
import requests
import phonenumbers
from phonenumbers import geocoder
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
try:
    from telegram import CopyTextButton
except ImportError:
    CopyTextButton = None

# === CONFIGURATION ===
BOT_TOKEN = "8389209190:AAHGqxrGlaZv0aGaEOXtJ0DmYyqATzE2OXU"
GROUP_ID = -1004342739367

# Zenex Network Config
API_KEY = "ZNX_ZMJG4X1QBNIUR1HDSZ1P31ED"
API_URL = "https://www.zenexnetwork.com/api/v1/global-broadcast"
POLL_INTERVAL = 6

# Emojis for services
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

async def send_to_group(bot, service, num, msg):
    country_name, flag, iso = get_country_info(num)
    app_emoji = get_app_emoji(service)
    masked = mask_number(num)
    otp = extract_otp(msg)
    
    text = f"{flag} <b>#{iso} {app_emoji}{service} {masked}</b> <tg-emoji emoji-id=\"5264919878082509254\">▶️</tg-emoji>"
    
    if CopyTextButton:
        try:
            row1 = [InlineKeyboardButton(text=f"{otp}", copy_text=CopyTextButton(text=otp), icon_custom_emoji_id="6176966310920983412")]
        except:
            row1 = [InlineKeyboardButton(text=f"🔑 {otp}", callback_data="noop")]
    else:
        row1 = [InlineKeyboardButton(text=f"🔑 {otp}", callback_data="noop")]
        
    row2 = [
        InlineKeyboardButton(text="Methods", url="https://youtube.com/@xclusor", icon_custom_emoji_id="5807797645443340724"),
        InlineKeyboardButton(text="Channel", url="https://t.me/+a0zwxrh1Il43NjM1", icon_custom_emoji_id="5429571366384842791")
    ]
    row3 = [InlineKeyboardButton(text="OTP Panel", url="https://www.zenexnetwork.com", icon_custom_emoji_id="5372917041193828849")]
    
    markup = InlineKeyboardMarkup([row1, row2, row3])
    
    # Retry mechanism for ReadError/Timeout
    for attempt in range(3):
        try:
            await bot.send_message(
                chat_id=GROUP_ID,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=True
            )
            print(f"✅ Sent OTP for {num} - {service}")
            break
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(1)
            else:
                print(f"❌ Failed to send to group after retries: {e}")

async def main():
    # Set longer network timeouts to stop Timed out errors
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)
    bot = Bot(token=BOT_TOKEN, request=request)
    seen_otps = set()
    
    print("🚀 Starting Zenex Network Forwarder Bot...")
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "mapikey": API_KEY
    }
    
    try:
        res = requests.get(API_URL, headers=headers, timeout=10)
        data = res.json()
        items = data if isinstance(data, list) else data.get("data", data.get("otps", []))
        
        for item in items:
            service = item.get("service") or item.get("app", "Service")
            num = item.get("number") or item.get("phone") or item.get("range", "000000")
            msg = item.get("message") or item.get("otp") or item.get("sms", "")
            nid = item.get("nid", f"{service}_{num}_{msg}")
            seen_otps.add(nid)
        print(f"📦 Initialized with {len(seen_otps)} existing OTPs.")
    except Exception as e:
        print(f"⚠️ Initial API fetch failed: {e}")
        
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
                    await send_to_group(bot, service, num, msg)
                    await asyncio.sleep(1) # Added 1s delay to respect Telegram limits
                    
            if len(seen_otps) > 10000:
                seen_otps = set(list(seen_otps)[-5000:])
                
        except Exception as e:
            print(f"⚠️ Error fetching API: {e}")
            
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
