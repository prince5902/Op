# =======================
#     BOT HANDLERS
# =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    name = user.first_name
    username = user.username or "None"
    
    users = load_users()
    
    # Check referral if new user
    if user_id not in users:
        if context.args:
            ref_id = context.args[0]
            if ref_id in users and ref_id != user_id:
                config = load_config()
                bonus = config.get("refer_bonus", 10.0)
                users[ref_id]["balance"] = users[ref_id].get("balance", 0.0) + bonus
                if "refers" not in users[ref_id]:
                    users[ref_id]["refers"] = []
                users[ref_id]["refers"].append(user_id)
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_id),
                        text=f"🎁 You received <b>{bonus} BDT</b> referral bonus for inviting {name}!",
                        parse_mode="HTML"
                    )
                except:
                    pass

        users[user_id] = {
            "name": name,
            "username": username,
            "balance": 0.0,
            "lang": "bn",
            "refers": [],
            "referred_by": context.args[0] if context.args else None
        }
        save_users(users)
        
    lang = users[user_id].get("lang", "bn")
    
    # Check Force Join
    unjoined = await get_unjoined_channels(context.bot, int(user_id))
    if unjoined:
        await send_force_join_message(update, context, lang, user_id)
        return
        
    strings = LANG_STRINGS[lang]
    keyboard = get_menu_keyboard(lang)
    
    await update.message.reply_text(
        strings["welcome"].format(name=name),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    user_id = str(user.id)
    
    users = load_users()
    if user_id not in users:
        users[user_id] = {
            "name": user.first_name,
            "username": user.username or "None",
            "balance": 0.0,
            "lang": "bn",
            "refers": [],
            "referred_by": None
        }
        save_users(users)
        
    lang = users[user_id].get("lang", "bn")
    strings = LANG_STRINGS[lang]
    
    # Check Force Join first
    unjoined = await get_unjoined_channels(context.bot, int(user_id))
    if unjoined:
        await send_force_join_message(update, context, lang, user_id)
        return

    # Handle State machine for withdraw
    state = context.user_data.get("state")
    if state == "waiting_withdraw_number":
        method = context.user_data.get("withdraw_method")
        context.user_data["withdraw_number"] = text
        context.user_data["state"] = "waiting_withdraw_amount"
        balance = users[user_id].get("balance", 0.0)
        config = load_config()
        min_w = config.get("min_withdraw", 50.0)
        
        await update.message.reply_text(
            strings["withdraw_enter_amount"].format(min_withdraw=min_w, balance=balance),
            parse_mode="HTML"
        )
        return
        
    elif state == "waiting_withdraw_amount":
        try:
            amount = float(text)
        except ValueError:
            await update.message.reply_text(strings["invalid_amount"], parse_mode="HTML")
            return
            
        config = load_config()
        min_w = config.get("min_withdraw", 50.0)
        balance = users[user_id].get("balance", 0.0)
        
        if amount < min_w or amount > balance:
            await update.message.reply_text(strings["withdraw_insufficient"].format(min_withdraw=min_w), parse_mode="HTML")
            return
            
        method = context.user_data.get("withdraw_method")
        number = context.user_data.get("withdraw_number")
        
        # Deduct balance
        users[user_id]["balance"] -= amount
        save_users(users)
        
        context.user_data["state"] = None
        
        await update.message.reply_text(
            strings["withdraw_success"].format(method=method, number=number, amount=amount),
            reply_markup=get_menu_keyboard(lang),
            parse_mode="HTML"
        )
        
        # Notify Owner
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🔔 <b>New Withdrawal Request!</b>\n\n👤 User: {user.first_name} (<code>{user_id}</code>)\n💳 Method: {method}\n📞 Number: <code>{number}</code>\n💰 Amount: {amount} BDT",
                parse_mode="HTML"
            )
        except:
            pass
        return

    # Menu translations mapping
    all_menus = {
        LANG_STRINGS["en"]["menu_my_account"]: "account",
        LANG_STRINGS["bn"]["menu_my_account"]: "account",
        LANG_STRINGS["hi"]["menu_my_account"]: "account",
        
        LANG_STRINGS["en"]["menu_refer"]: "refer",
        LANG_STRINGS["bn"]["menu_refer"]: "refer",
        LANG_STRINGS["hi"]["menu_refer"]: "refer",
        
        LANG_STRINGS["en"]["menu_withdraw"]: "withdraw",
        LANG_STRINGS["bn"]["menu_withdraw"]: "withdraw",
        LANG_STRINGS["hi"]["menu_withdraw"]: "withdraw",
        
        LANG_STRINGS["en"]["menu_support"]: "support",
        LANG_STRINGS["bn"]["menu_support"]: "support",
        LANG_STRINGS["hi"]["menu_support"]: "support",
        
        LANG_STRINGS["en"]["menu_language"]: "language",
        LANG_STRINGS["bn"]["menu_language"]: "language",
        LANG_STRINGS["hi"]["menu_language"]: "language",
        
        LANG_STRINGS["en"]["menu_get_number"]: "get_number",
        LANG_STRINGS["bn"]["menu_get_number"]: "get_number",
        LANG_STRINGS["hi"]["menu_get_number"]: "get_number",
    }
    
    action = all_menus.get(text)
    
    if action == "account":
        balance = users[user_id].get("balance", 0.0)
        await update.message.reply_text(
            strings["account_info"].format(
                user_id=user_id,
                name=user.first_name,
                username=user.username or "None",
                balance=balance
            ),
            parse_mode="HTML"
        )
        
    elif action == "refer":
        config = load_config()
        bonus = config.get("refer_bonus", 10.0)
        bot_username = config.get("bot_username", "GeminiAiBot")
        link = f"https://t.me/{bot_username}?start={user_id}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(strings["my_refer_btn"], callback_data="my_refers")],
            [InlineKeyboardButton(strings["top_refer_btn"], callback_data="top_refers")]
        ])
        
        await update.message.reply_text(
            strings["refer_info"].format(bonus=bonus, link=link),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    elif action == "withdraw":
        config = load_config()
        balance = users[user_id].get("balance", 0.0)
        min_w = config.get("min_withdraw", 50.0)
        methods = ", ".join(config.get("withdraw_methods", ["BKash", "Nagad"]))
        
        buttons = []
        for m in config.get("withdraw_methods", ["BKash", "Nagad"]):
            buttons.append(InlineKeyboardButton(f"💳 {m}", callback_data=f"withdraw_method_{m}"))
            
        keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
        
        await update.message.reply_text(
            strings["withdraw_info"].format(balance=balance, min_withdraw=min_w, methods=methods),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    elif action == "support":
        config = load_config()
        link = config.get("support_link", "https://t.me/junaidaliniz")
        await update.message.reply_text(
            strings["support_info"].format(link=link),
            parse_mode="HTML"
        )
        
    elif action == "language":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
                InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")
            ],
            [
                InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")
            ]
        ])
        await update.message.reply_text(strings["choose_lang"], reply_markup=keyboard, parse_mode="HTML")
        
    elif action == "get_number":
        # Dynamic services from Zenex API
        data = fetch_zenex_data()
        services = sorted(list(set([str(x.get("service") or x.get("app") or "Service") for x in data])))
        
        if not services:
            await update.message.reply_text("❌ No active services found right now. Try again later.", parse_mode="HTML")
            return
            
        buttons = []
        for s in services[:20]: # limit to 20
            buttons.append(InlineKeyboardButton(f"📱 {s}", callback_data=f"service_{s}"))
            
        grid = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        keyboard = InlineKeyboardMarkup(grid)
        
        await update.message.reply_text(strings["select_service"], reply_markup=keyboard, parse_mode="HTML")


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    user_id = str(user.id)
    
    users = load_users()
    lang = users.get(user_id, {}).get("lang", "bn")
    strings = LANG_STRINGS[lang]
    
    if data == "verify_channel_join":
        unjoined = await get_unjoined_channels(context.bot, int(user_id))
        if unjoined:
            await query.edit_message_text(strings["verified_failed"], parse_mode="HTML")
        else:
            await query.message.delete()
            keyboard = get_menu_keyboard(lang)
            await context.bot.send_message(
                chat_id=user_id,
                text=strings["verified_success"],
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
    elif data.startswith("lang_"):
        new_lang = data.split("_")[1]
        if user_id in users:
            users[user_id]["lang"] = new_lang
            save_users(users)
        else:
            users[user_id] = {
                "name": user.first_name,
                "username": user.username or "None",
                "balance": 0.0,
                "lang": new_lang,
                "refers": [],
                "referred_by": None
            }
            save_users(users)
            
        new_strings = LANG_STRINGS[new_lang]
        keyboard = get_menu_keyboard(new_lang)
        await query.message.edit_text(new_strings["lang_changed"], parse_mode="HTML")
        await context.bot.send_message(chat_id=user_id, text=new_strings["welcome"].format(name=user.first_name), reply_markup=keyboard, parse_mode="HTML")
        
    elif data == "my_refers":
        refers = users.get(user_id, {}).get("refers", [])
        count = len(refers)
        list_str = "\n".join([f"• <code>{r}</code>" for r in refers]) if refers else "No refers yet."
        await query.message.edit_text(
            strings["my_refer_info"].format(count=count, list=list_str),
            parse_mode="HTML"
        )
        
    elif data == "top_refers":
        sorted_users = sorted(users.items(), key=lambda x: len(x[1].get("refers", [])), reverse=True)[:5]
        top_list = []
        for i, (uid, udata) in enumerate(sorted_users, 1):
            name = udata.get("name", "User")
            ref_count = len(udata.get("refers", []))
            top_list.append(f"{i}. {name} - <b>{ref_count}</b> refers")
        list_str = "\n".join(top_list) if top_list else "No data."
        await query.message.edit_text(
            strings["top_refer_info"].format(list=list_str),
            parse_mode="HTML"
        )
        
    elif data.startswith("withdraw_method_"):
        method = data.replace("withdraw_method_", "")
        context.user_data["withdraw_method"] = method
        context.user_data["state"] = "waiting_withdraw_number"
        await query.message.reply_text(
            strings["withdraw_enter_details"].format(method=method),
            parse_mode="HTML"
        )
        
    elif data.startswith("service_"):
        service_name = data.replace("service_", "")
        zenex_data = fetch_zenex_data()
        
        matched = None
        for item in zenex_data:
            s = str(item.get("service") or item.get("app") or "")
            if s.lower() == service_name.lower():
                matched = item
                break
                
        if not matched and zenex_data:
            matched = zenex_data[0]
            
        if matched:
            num = str(matched.get("number") or matched.get("phone") or matched.get("full_number") or "+8801XXXXXXXXX")
            country, flag = get_country_info_from_number(num)
            
            text = strings["generated_num_service"].format(
                flag=flag,
                service=service_name,
                country=country,
                number=num
            )
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(strings["back_to_services"], callback_data="back_services")]])
            await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await query.message.edit_text("❌ No numbers available for this service right now.", parse_mode="HTML")
            
    elif data == "back_services":
        data_api = fetch_zenex_data()
        services = sorted(list(set([str(x.get("service") or x.get("app") or "Service") for x in data_api])))
        buttons = []
        for s in services[:20]:
            buttons.append(InlineKeyboardButton(f"📱 {s}", callback_data=f"service_{s}"))
        grid = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        keyboard = InlineKeyboardMarkup(grid)
        await query.message.edit_text(strings["select_service"], reply_markup=keyboard, parse_mode="HTML")


# =======================
#    ADMIN HANDLERS
# =======================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
        
    help_text = """
👑 <b>Admin Panel Commands</b>

/setchannel <code>[Channel ID | Link]</code> - Set OTP broadcast channel
/addforce <code>[Channel ID | Link | Title]</code> - Add force join channel
/removeforce <code>[Channel ID]</code> - Remove force join channel
/listforce - List all force join channels
/addbalance <code>[User ID] [Amount]</code> - Add balance to user
/broadcast <code>[Message]</code> - Broadcast message to all users
"""
    await update.message.reply_text(help_text, parse_mode="HTML")


async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /setchannel <code>[Channel ID | Link]</code>", parse_mode="HTML")
        return
        
    text = " ".join(context.args)
    chan_id, chan_link = parse_channel_input(text)
    
    config = load_config()
    config["otp_channel_id"] = chan_id
    if chan_link:
        config["otp_channel_link"] = chan_link
        config["official_channel_link"] = chan_link
    save_config(config)
    
    await update.message.reply_text(f"✅ OTP Channel successfully set to: <code>{chan_id}</code>", parse_mode="HTML")


async def add_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /addforce <code>[ID | Link | Title]</code>", parse_mode="HTML")
        return
        
    full_text = " ".join(context.args)
    parts = full_text.split("|")
    
    chan_id = parts[0].strip()
    chan_link = parts[1].strip() if len(parts) > 1 else f"https://t.me/{chan_id.lstrip('@')}"
    chan_title = parts[2].strip() if len(parts) > 2 else "Channel"
    
    config = load_config()
    if "force_channels" not in config:
        config["force_channels"] = []
        
    config["force_channels"].append({
        "id": chan_id,
        "link": chan_link,
        "title": chan_title
    })
    save_config(config)
    
    await update.message.reply_text(f"✅ Force Join Channel added:\nID: <code>{chan_id}</code>\nTitle: {chan_title}", parse_mode="HTML")


async def remove_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /removeforce <code>[Channel ID]</code>", parse_mode="HTML")
        return
        
    target_id = context.args[0].strip()
    config = load_config()
    force_channels = config.get("force_channels", [])
    
    new_channels = [c for c in force_channels if c.get("id") != target_id]
    config["force_channels"] = new_channels
    save_config(config)
    
    await update.message.reply_text(f"✅ Channel <code>{target_id}</code> removed from force join list.", parse_mode="HTML")


async def list_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    config = load_config()
    channels = config.get("force_channels", [])
    
    if not channels:
        await update.message.reply_text("No force join channels configured.", parse_mode="HTML")
        return
        
    msg = "📋 <b>Force Join Channels:</b>\n\n"
    for i, c in enumerate(channels, 1):
        msg += f"{i}. Title: {c.get('title')}\n   ID: <code>{c.get('id')}</code>\n   Link: {c.get('link')}\n\n"
        
    await update.message.reply_text(msg, parse_mode="HTML")


async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addbalance <code>[User ID] [Amount]</code>", parse_mode="HTML")
        return
        
    target_id = context.args[0].strip()
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.", parse_mode="HTML")
        return
        
    users = load_users()
    if target_id not in users:
        await update.message.reply_text("❌ User not found in database.", parse_mode="HTML")
        return
        
    users[target_id]["balance"] = users[target_id].get("balance", 0.0) + amount
    save_users(users)
    
    await update.message.reply_text(f"✅ Successfully added {amount} BDT to user <code>{target_id}</code>.", parse_mode="HTML")
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"🎁 Admin added <b>{amount} BDT</b> to your account balance!",
            parse_mode="HTML"
        )
    except:
        pass


async def broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <code>[Your Message]</code>", parse_mode="HTML")
        return
        
    msg = " ".join(context.args)
    users = load_users()
    
    success = 0
    failed = 0
    
    status_msg = await update.message.reply_text("📢 Broadcasting message...", parse_mode="HTML")
    
    for uid in users.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
            
    await status_msg.edit_text(f"✅ Broadcast finished!\n\nSuccessful: {success}\nFailed: {failed}", parse_mode="HTML")


# =======================
#    BACKGROUND POLLED WORKER
# =======================

async def background_zenex_poller(application):
    seen_ids = set()
    print("[POLLER] Background Zenex OTP Poller started.", flush=True)
    
    while True:
        try:
            data = fetch_zenex_data()
            if data:
                # Assuming items have some unique identifier or we track message count / content
                for item in reversed(data):
                    msg_text, otp = format_sms_message(item)
                    item_id = str(item.get("id") or item.get("message") or item.get("otp"))
                    
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        if len(seen_ids) > 500:
                            seen_ids.pop()
                            
                        # Send to configured channel
                        await send_to_configured_channel(application.bot, msg_text)
        except Exception as e:
        print(f"[POLER ERROR] {e}", flush=True)
            
        await asyncio.sleep(10)


async def post_init(application):
    # Run background poller task
    asyncio.create_task(background_zenex_poller(application))


# =======================
#         MAIN
# =======================

def main():
    # Start Flask thread for Render 24/7 uptime
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("[FLASK] Flask server started on background thread.", flush=True)

    # Build Telegram Application
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("setchannel", set_channel))
    application.add_handler(CommandHandler("addforce", add_force))
    application.add_handler(CommandHandler("removeforce", remove_force))
    application.add_handler(CommandHandler("listforce", list_force))
    application.add_handler(CommandHandler("addbalance", add_balance))
    application.add_handler(CommandHandler("broadcast", broadcast_msg))

    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("[BOT] Telegram Bot is running...", flush=True)
    application.run_polling()


if __name__ == "__main__":
    main()
