import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random
import string
from datetime import datetime
from flask import Flask
import threading

# ==========================================
# 1. Configuration & Setup
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789")) 
bot = telebot.TeleBot(BOT_TOKEN)

# --- Firebase Setup ---
try:
    cred = credentials.Certificate("firebase_cred.json") 
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🔥 Firebase Connected Successfully!")
except Exception as e:
    print(f"❌ Firebase Connection Error: {e}")

# ==========================================
# 2. Database Initializer (Settings)
# ==========================================
def init_db():
    settings_ref = db.collection('settings')
    
    conf_doc = settings_ref.document('config').get()
    if not conf_doc.exists:
        settings_ref.document('config').set({
            'buy_price': 15.0, 'sell_new': 10.0, 'sell_old': 10.0, 
            'ref_bonus': 5.0, 'min_dep': 50.0, 'min_with': 50.0,
            'usdt_rate': 120.0, 'support_link': 'https://t.me/YourAdminUsername'
        })
    else:
        conf = conf_doc.to_dict()
        updates = {}
        if 'min_with' not in conf: updates['min_with'] = 50.0
        if 'support_link' not in conf: updates['support_link'] = 'https://t.me/YourAdminUsername'
        if updates: settings_ref.document('config').update(updates)
        
    if not settings_ref.document('payments').get().exists:
        settings_ref.document('payments').set({
            'bkash': '01985664862', 'nagad': '01985664862',
            'rocket': '01985664862', 'upay': '01985664862',
            'binance': '0xde2734362bb006142c0613e68b40f54203561703'
        })
        
    if not settings_ref.document('texts').get().exists:
        help_en = "📖 *How to use:*\n\n🛒 *Buy:* Click 'Buy Gmail' -> Enter quantity -> Get Mails.\n🤝 *Sell:* Click 'Sell Gmail' -> Submit details -> Wait for approval.\n💳 *Deposit:* Wallet -> Deposit -> Send money -> Submit TrxID.\n🎁 *Refer:* Share your link to earn bonus."
        help_bn = "📖 *কিভাবে ব্যবহার করবেন:*\n\n🛒 *কেনা:* 'জিমেইল কিনুন' এ ক্লিক করুন -> পরিমাণ লিখুন -> জিমেইল পেয়ে যাবেন।\n🤝 *বিক্রি:* 'জিমেইল বিক্রি' তে ক্লিক করে তথ্য দিন -> অ্যাডমিন এপ্রুভ করলে টাকা পাবেন।\n💳 *ডিপোজিট:* ওয়ালেট -> ডিপোজিট -> টাকা পাঠিয়ে TrxID দিন।\n🎁 *রেফার:* বন্ধুদের ইনভাইট করে বোনাস পান।"
        settings_ref.document('texts').set({
            'welcome_en': "Welcome to Premium Gmail Market! 🌐\nSelect an option below:",
            'welcome_bn': "প্রিমিয়াম জিমেইল মার্কেটে স্বাগতম! 🌐\nনিচের একটি অপশন বেছে নিন:",
            'banner_id': "",
            'help_en': help_en, 'help_bn': help_bn
        })

init_db()

def get_config(): return db.collection('settings').document('config').get().to_dict()
def get_payments(): return db.collection('settings').document('payments').get().to_dict()
def get_texts(): return db.collection('settings').document('texts').get().to_dict()

# ==========================================
# 3. Dynamic Currency Formatter
# ==========================================
def fmt_money(bdt_amount, currency, usdt_rate):
    if currency == 'USDT':
        return f"${round(bdt_amount / usdt_rate, 2)} USDT"
    return f"{bdt_amount} BDT"

# ==========================================
# 4. Multi-Language Strings
# ==========================================
LANG = {
    'en': {
        'buy': "🛒 Buy Gmail", 'sell': "🤝 Sell Gmail",
        'wallet': "💳 Wallet", 'profile': "👤 Profile",
        'refer': "🎁 Refer & Earn", 'stock': "📊 Stock Info",
        'history': "📜 History", 'help': "📖 Help",
        'support': "🎧 Support", 'lang': "🌐 Language / Currency", 
        'cancel': "❌ Cancel", 'admin_btn': "👑 Admin Panel",
        'profile_txt': "👤 *Your Profile*\nName: {name}\nID: `{id}`\nUsername: {uname}\n\n💰 *Balance:*\nBDT: `{bdt}` ৳\nUSDT: `${usdt}`\n\n🛒 Bought: `{bought}`\n🤝 Sold: `{sold}`\n🎁 Referrals: `{ref}`",
        'sell_type': "What kind of Gmail do you want to sell?\nNew Mail: {} | Old Mail: {}",
        'new_mail': "🆕 New Gmail", 'old_mail': "🔄 Old Gmail",
        'task_new': "Create a new Gmail using this username:\n👉 `{}`\n\nSend the *Password* here:",
        'task_old': "Enter the Old Gmail Address:",
        'task_pass': "Enter password for `{}`:",
        'buy_msg': "Gmail Price: {}\nDo you want to buy?",
        'buy_qty': "💰 Your Balance: {}\nYou can buy max: *{}* Gmails.\n\n✏️ *Enter how many Gmails you want to buy:*",
        'buy_confirm': "✅ Confirm Buy",
        'qty_err': "⚠️ Please enter a valid number.",
        'no_bal': "❌ Insufficient balance!",
        'stock_less': "⚠️ Only {} Gmails available in stock. Do you want to buy {}?",
        'buy_success': "🎉 *Purchase Successful!*\n\nYou bought {} Gmails. Remaining balance: {}.\n\n*Your Gmails:*\n{}",
        'pending': "✅ Submitted successfully! Wait for admin approval.",
        'deposit': "📥 Deposit", 'withdraw': "📤 Withdraw",
        'min_dep': "⚠️ Minimum deposit is {}.\n\n✏️ *Enter deposit amount:*",
        'send_money': "💳 Method: {}\n📞 Number/Address: `{}`\n\nPlease send {} to this number.\nAfter sending, enter your *TrxID* below:",
        'banned': "🚫 You are banned from using this bot.",
        'canceled': "Action canceled.",
        'wallet_msg': "💳 *Wallet & Transactions*\n\n⚠️ *BINANCE USERS:* Always use *BSC BNB Smart Chain (BEP20)* network for USDT transactions.\n\nSelect an option below:",
        'stock_info': "📊 *Live Stock Info*\n\nAvailable Gmails: `{}`",
        'history_empty': "📜 You haven't bought any Gmails yet.",
        'refer_txt': "🎁 *Refer & Earn*\n\nShare your link with friends. When they join, you get {} bonus!\n(Bonus is added after 24 hours verification)\n\n🔗 Your Link: `https://t.me/{}?start={}`"
    },
    'bn': {
        'buy': "🛒 জিমেইল কিনুন", 'sell': "🤝 জিমেইল বিক্রি করুন",
        'wallet': "💳 ওয়ালেট", 'profile': "👤 প্রোফাইল",
        'refer': "🎁 রেফার এন্ড আর্ন", 'stock': "📊 স্টক",
        'history': "📜 ইতিহাস", 'help': "📖 সাহায্য",
        'support': "🎧 সাপোর্ট", 'lang': "🌐 ভাষা / কারেন্সি", 
        'cancel': "❌ বাতিল করুন", 'admin_btn': "👑 অ্যাডমিন প্যানেল",
        'profile_txt': "👤 *আপনার প্রোফাইল*\nনাম: {name}\nআইডি: `{id}`\nইউজারনেম: {uname}\n\n💰 *ব্যালেন্স:*\nBDT: `{bdt}` ৳\nUSDT: `${usdt}`\n\n🛒 কেনা হয়েছে: `{bought}`\n🤝 বিক্রি হয়েছে: `{sold}`\n🎁 রেফারেল: `{ref}`",
        'sell_type': "আপনি কোন ধরনের জিমেইল বিক্রি করতে চান?\nনতুন: {} | পুরাতন: {}",
        'new_mail': "🆕 নতুন জিমেইল", 'old_mail': "🔄 পুরাতন জিমেইল",
        'task_new': "এই ইউজারনেমটি দিয়ে একটি নতুন জিমেইল খুলুন:\n👉 `{}`\n\nখোলার পর *পাসওয়ার্ডটি* নিচে দিন:",
        'task_old': "আপনার পুরাতন জিমেইল এড্রেসটি দিন:",
        'task_pass': "`{}` এর পাসওয়ার্ডটি দিন:",
        'buy_msg': "প্রতিটি জিমেইলের দাম: {}\nআপনি কি কিনতে চান?",
        'buy_qty': "💰 আপনার ব্যালেন্স: {}\nআপনি সর্বোচ্চ *{}* টি জিমেইল কিনতে পারবেন।\n\n✏️ *আপনি কয়টি জিমেইল কিনতে চান তা লিখে মেসেজ করুন:*",
        'buy_confirm': "✅ কনফার্ম করুন",
        'qty_err': "⚠️ অনুগ্রহ করে সঠিক সংখ্যা লিখুন।",
        'no_bal': "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই!",
        'stock_less': "⚠️ স্টকে মাত্র {} টি জিমেইল আছে। আপনি কি {} টি নিতে চান?",
        'buy_success': "🎉 *সফলভাবে কেনা হয়েছে!*\n\nআপনি {} টি জিমেইল কিনেছেন। বর্তমান ব্যালেন্স: {}।\n\n*আপনার জিমেইলগুলো:*\n{}",
        'pending': "✅ রিকোয়েস্ট সফলভাবে পাঠানো হয়েছে! অ্যাডমিন চেক করা পর্যন্ত অপেক্ষা করুন।",
        'deposit': "📥 ডিপোজিট", 'withdraw': "📤 টাকা উত্তোলন",
        'min_dep': "⚠️ সর্বনিম্ন ডিপোজিট {}।\n\n✏️ *আপনি কত টাকা ডিপোজিট করবেন তা লিখুন:*",
        'send_money': "💳 মাধ্যম: {}\n📞 নাম্বার/অ্যাড্রেস: `{}`\n\nদয়া করে এই নাম্বারে {} পাঠান।\nটাকা পাঠানোর পর আপনার *TrxID* নিচে দিন:",
        'banned': "🚫 আপনাকে ব্যান করা হয়েছে।",
        'canceled': "বাতিল করা হয়েছে।",
        'wallet_msg': "💳 *ওয়ালেট এবং লেনদেন*\n\n⚠️ *বাইনান্স (BINANCE) ইউজারদের জন্য:* ডলার আদান-প্রদানে সর্বদা *BSC BNB Smart Chain (BEP20)* নেটওয়ার্ক ব্যবহার করবেন।\n\nআপনার ওয়ালেট থেকে একটি অপশন নির্বাচন করুন:",
        'stock_info': "📊 *লাইভ স্টক ইনফো*\n\nবর্তমানে স্টকে থাকা জিমেইল: `{}` টি",
        'history_empty': "📜 আপনি এখনো কোনো জিমেইল কিনেননি।",
        'refer_txt': "🎁 *রেফার করে আয় করুন*\n\nআপনার বন্ধুদের সাথে লিংক শেয়ার করুন। তারা জয়েন করলে আপনি {} বোনাস পাবেন!\n(নিরাপত্তার জন্য বোনাস ২৪ ঘন্টা পর একাউন্টে যুক্ত হবে)\n\n🔗 আপনার লিংক: `https://t.me/{}?start={}`"
    }
}

# ==========================================
# 5. Helper & Time Functions
# ==========================================
def get_user(user_id): 
    doc = db.collection('users').document(str(user_id)).get()
    if doc.exists: return doc.to_dict()
    return {'id': str(user_id), 'lang': 'bn', 'currency': 'BDT', 'balance_bdt': 0.0, 'total_bought': 0, 'total_sold': 0, 'total_ref': 0}

def main_menu(user_id, lang):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(LANG[lang]['buy']), KeyboardButton(LANG[lang]['sell']),
        KeyboardButton(LANG[lang]['wallet']), KeyboardButton(LANG[lang]['profile']),
        KeyboardButton(LANG[lang]['stock']), KeyboardButton(LANG[lang]['history']),
        KeyboardButton(LANG[lang]['refer']), KeyboardButton(LANG[lang]['help']),
        KeyboardButton(LANG[lang]['support']), KeyboardButton(LANG[lang]['lang'])
    )
    if int(user_id) == ADMIN_ID: markup.add(KeyboardButton(LANG[lang]['admin_btn']))
    return markup

def cancel_menu(lang):
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(LANG[lang]['cancel']))
    return markup

def now(): return datetime.now().strftime("%Y-%m-%d %I:%M %p")

def is_menu_button(text):
    all_buttons = list(LANG['en'].values()) + list(LANG['bn'].values())
    return text in all_buttons

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['cancel'], LANG['bn']['cancel']])
def cancel_action(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    lang = get_user(message.from_user.id).get('lang', 'bn')
    bot.send_message(message.chat.id, LANG[lang]['canceled'], reply_markup=main_menu(message.from_user.id, lang))

# --- Check 24h Pending Referrals ---
def process_pending_refs(user_id):
    refs = db.collection('pending_referrals').where('referrer', '==', str(user_id)).where('status', '==', 'pending').stream()
    added_bdt = 0
    for r in refs:
        data = r.to_dict()
        try:
            time_joined = datetime.strptime(data['time'], "%Y-%m-%d %I:%M %p")
            if (datetime.now() - time_joined).total_seconds() >= 86400: # 24 Hours
                db.collection('users').document(str(user_id)).set({'balance_bdt': firestore.Increment(data['bonus']), 'total_ref': firestore.Increment(1)}, merge=True)
                db.collection('pending_referrals').document(r.id).update({'status': 'paid'})
                added_bdt += data['bonus']
        except: pass
    
    if added_bdt > 0:
        cfg = get_config()
        u = get_user(user_id)
        fmt_amt = fmt_money(added_bdt, u.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
        txt = f"🎊 *Congratulations!*\nYour pending referral bonus of {fmt_amt} has been successfully added to your main balance after 24h verification."
        if u.get('lang', 'bn') == 'bn':
            txt = f"🎊 *অভিনন্দন!*\n২৪ ঘন্টা ভেরিফিকেশন শেষে আপনার পেন্ডিং রেফারেল বোনাস {fmt_amt} মেইন ব্যালেন্সে যুক্ত হয়েছে।"
        bot.send_message(user_id, txt, parse_mode="Markdown")

# ==========================================
# 6. Core Menus & Profile
# ==========================================
@bot.message_handler(commands=['start'])
def start_bot(message):
    user_id = str(message.from_user.id)
    user_ref = db.collection('users').document(user_id)
    user_data = user_ref.get().to_dict() if user_ref.get().exists else None
    
    if user_data and user_data.get('status') == 'banned':
        return bot.send_message(message.chat.id, LANG['en']['banned'])

    # Process any pending referrals for existing users
    if user_data: process_pending_refs(user_id)

    if not user_data:
        args = message.text.split()
        referrer_id = args[1] if len(args) > 1 else None
        
        user_name = message.from_user.first_name or "User"
        user_ref.set({
            'id': user_id, 
            'first_name': user_name,
            'username': message.from_user.username, 
            'lang': 'bn', 'currency': 'BDT', 'balance_bdt': 0.0,
            'total_bought': 0, 'total_sold': 0, 'total_ref': 0,
            'status': 'active', 'join_date': now()
        }, merge=True)
        
        # 24 Hour Pending Referral Logic
        if referrer_id and referrer_id != user_id:
            cfg = get_config()
            ref_bonus = cfg.get('ref_bonus', 5.0)
            
            db.collection('pending_referrals').add({
                'referrer': referrer_id, 'referred_name': user_name,
                'bonus': ref_bonus, 'time': now(), 'status': 'pending'
            })
            
            ref_user = get_user(referrer_id)
            fmt_bonus = fmt_money(ref_bonus, ref_user.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
            
            notify_txt = f"🎉 *New Referral Joined!*\n\n👤 Name: {user_name}\n⏳ Bonus: {fmt_bonus} (Pending)\n\n_Note: Bonus will be automatically added to your balance after 24 hours._"
            if ref_user.get('lang', 'bn') == 'bn':
                notify_txt = f"🎉 *নতুন রেফারেল জয়েন করেছে!*\n\n👤 নাম: {user_name}\n⏳ বোনাস: {fmt_bonus} (পেন্ডিং)\n\n_নোট: নিরাপত্তার জন্য বোনাসটি ২৪ ঘন্টা পর আপনার মেইন ব্যালেন্সে যুক্ত হবে।_"
                
            try: bot.send_message(referrer_id, notify_txt, parse_mode="Markdown")
            except: pass

    lang = get_user(user_id).get('lang', 'bn')
    texts = get_texts()
    banner = texts.get('banner_id', '')
    welcome = texts['welcome_bn'] if lang == 'bn' else texts['welcome_en']
    
    if banner: bot.send_photo(message.chat.id, banner, caption=welcome, reply_markup=main_menu(user_id, lang))
    else: bot.send_message(message.chat.id, welcome, reply_markup=main_menu(user_id, lang))

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['profile'], LANG['bn']['profile']])
def profile_handler(message):
    process_pending_refs(str(message.from_user.id)) # Check pending refs on profile open
    
    u = get_user(message.from_user.id)
    cfg = get_config()
    bal = u.get('balance_bdt', 0.0)
    usdt_bal = round(bal / cfg.get('usdt_rate', 120.0), 2)
    
    name = message.from_user.first_name or "User"
    uname = f"@{message.from_user.username}" if message.from_user.username else "NONE"
    
    text = LANG[u.get('lang', 'bn')]['profile_txt'].format(
        name=name, id=u.get('id', 'N/A'), uname=uname, 
        bdt=bal, usdt=usdt_bal, 
        bought=u.get('total_bought', 0), 
        sold=u.get('total_sold', 0), 
        ref=u.get('total_ref', 0)
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['help'], LANG['bn']['help']])
def help_handler(message):
    u = get_user(message.from_user.id)
    texts = get_texts()
    txt = texts['help_bn'] if u.get('lang', 'bn') == 'bn' else texts['help_en']
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['support'], LANG['bn']['support']])
def support_handler(message):
    cfg = get_config()
    bot.send_message(message.chat.id, f"🎧 *Support / Help Center*\n\nIf you need any assistance, contact our admin directly via the link below:\n👉 {cfg.get('support_link', '@Admin')}", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['stock'], LANG['bn']['stock']])
def stock_handler(message):
    u = get_user(message.from_user.id)
    stock_count = len(list(db.collection('stock_gmails').where('status', '==', 'unsold').stream()))
    bot.send_message(message.chat.id, LANG[u.get('lang', 'bn')]['stock_info'].format(stock_count), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['history'], LANG['bn']['history']])
def history_handler(message):
    u = get_user(message.from_user.id)
    lang = u.get('lang', 'bn')
    purchases = db.collection('stock_gmails').where('bought_by', '==', u.get('id')).stream()
    history_text = "📜 *Your Purchase History*\n\n"
    count = 0
    for doc in purchases:
        d = doc.to_dict()
        history_text += f"📧 `{d['email']}`\n🔑 `{d['password']}`\n\n"
        count += 1
    if count == 0: bot.send_message(message.chat.id, LANG[lang]['history_empty'])
    else: bot.send_message(message.chat.id, history_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['refer'], LANG['bn']['refer']])
def refer_handler(message):
    u = get_user(message.from_user.id)
    bot_info = bot.get_me()
    cfg = get_config()
    fmt_bonus = fmt_money(cfg.get('ref_bonus', 5.0), u.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
    text = LANG[u.get('lang', 'bn')]['refer_txt'].format(fmt_bonus, bot_info.username, message.from_user.id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['lang'], LANG['bn']['lang']])
def settings_handler(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"), InlineKeyboardButton("🇧🇩 বাংলা", callback_data="set_lang_bn"))
    markup.add(InlineKeyboardButton("🪙 Use BDT", callback_data="set_cur_BDT"), InlineKeyboardButton("💵 Use USDT", callback_data="set_cur_USDT"))
    bot.send_message(message.chat.id, "⚙️ Settings:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def update_settings(call):
    bot.answer_callback_query(call.id) 
    parts = call.data.split("_")
    val = parts[2]
    field = 'lang' if parts[1] == 'lang' else 'currency'
    db.collection('users').document(str(call.from_user.id)).update({field: val})
    bot.send_message(call.message.chat.id, f"✅ Settings updated to {val}!", reply_markup=main_menu(call.from_user.id, val if field=='lang' else get_user(call.from_user.id).get('lang','bn')))
    bot.delete_message(call.message.chat.id, call.message.message_id)

# ==========================================
# 7. Binance Advanced Deposit & Withdraw
# ==========================================
@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['wallet'], LANG['bn']['wallet']])
def wallet_handler(message):
    lang = get_user(message.from_user.id).get('lang', 'bn')
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton(LANG[lang]['deposit'], callback_data="dep_menu"),
        InlineKeyboardButton(LANG[lang]['withdraw'], callback_data="with_menu")
    )
    bot.send_message(message.chat.id, LANG[lang]['wallet_msg'], parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "dep_menu")
def dep_menu(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("bKash", callback_data="dep_bkash"), InlineKeyboardButton("Nagad", callback_data="dep_nagad"),
        InlineKeyboardButton("Rocket", callback_data="dep_rocket"), InlineKeyboardButton("Upay", callback_data="dep_upay"),
        InlineKeyboardButton("🟡 Binance USDT", callback_data="dep_binance")
    )
    bot.edit_message_text("Select Deposit Method:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dep_") and call.data != "dep_menu")
def get_dep_amount(call):
    bot.answer_callback_query(call.id)
    method = call.data.split("_")[1]
    u = get_user(call.from_user.id)
    cfg = get_config()
    lang = u.get('lang', 'bn')
    
    # Binance Specific Handling
    if method == 'binance':
        min_dep = 5.0 # Fixed $5 Minimum for Binance
        msg_txt = "⚠️ Minimum deposit is *$5 USDT*.\n\n✏️ *Enter the amount of USDT you want to deposit:*"
        if lang == 'bn': msg_txt = "⚠️ বাইনান্সে সর্বনিম্ন ডিপোজিট *$5 USDT*.\n\n✏️ *আপনি কত USDT ডিপোজিট করবেন তা লিখুন:*"
        msg = bot.send_message(call.message.chat.id, msg_txt, parse_mode="Markdown", reply_markup=cancel_menu(lang))
        bot.register_next_step_handler(msg, process_dep_amount, method, min_dep, u, True)
    else:
        min_dep = cfg.get('min_dep', 50)
        fmt_min = fmt_money(min_dep, u.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
        msg = bot.send_message(call.message.chat.id, LANG[lang]['min_dep'].format(fmt_min), parse_mode="Markdown", reply_markup=cancel_menu(lang))
        bot.register_next_step_handler(msg, process_dep_amount, method, min_dep, u, False)

def process_dep_amount(message, method, min_dep, u, is_usdt):
    text = message.text
    lang = u.get('lang', 'bn')
    if text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    if is_menu_button(text): return bot.send_message(message.chat.id, "Action canceled.", reply_markup=main_menu(message.from_user.id, lang))
        
    try:
        amount_input = float(text)
        if amount_input < min_dep:
            msg = bot.send_message(message.chat.id, f"❌ Minimum is {min_dep}. Try again:", reply_markup=cancel_menu(lang))
            return bot.register_next_step_handler(msg, process_dep_amount, method, min_dep, u, is_usdt)
            
        pays = get_payments()
        acc = pays.get(method, "Not Set")
        
        if is_usdt:
            send_msg = f"💳 Method: *BINANCE (USDT)*\n🌐 Network: *BSC BNB Smart Chain (BEP20)*\n📞 Address: `{acc}`\n\nPlease send exactly *${amount_input} USDT* to this address.\nAfter sending, enter your *TrxID* below:"
            if lang == 'bn':
                send_msg = f"💳 মাধ্যম: *BINANCE (USDT)*\n🌐 নেটওয়ার্ক: *BSC BNB Smart Chain (BEP20)*\n📞 অ্যাড্রেস: `{acc}`\n\nদয়া করে এই অ্যাড্রেসে ঠিক *${amount_input} USDT* পাঠান।\nটাকা পাঠানোর পর আপনার *TrxID* নিচে দিন:"
        else:
            cfg = get_config()
            fmt_amt = fmt_money(amount_input, u.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
            send_msg = LANG[lang]['send_money'].format(method.upper(), acc, fmt_amt)
            
        msg = bot.send_message(message.chat.id, send_msg, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_dep_trx, method, amount_input, u, is_usdt)
    except:
        bot.send_message(message.chat.id, LANG[lang]['qty_err'], reply_markup=main_menu(message.from_user.id, lang))

def process_dep_trx(message, method, amount_input, u, is_usdt):
    text = message.text
    lang = u.get('lang', 'bn')
    if text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    if is_menu_button(text): return bot.send_message(message.chat.id, "Action canceled.", reply_markup=main_menu(message.from_user.id, lang))
        
    cfg = get_config()
    usdt_rate = cfg.get('usdt_rate', 120.0)
    
    # Standardize everything to BDT for Admin Database
    final_bdt_amount = amount_input * usdt_rate if is_usdt else amount_input
    display_amount = f"${amount_input} USDT (~{final_bdt_amount} BDT)" if is_usdt else f"{amount_input} BDT"
    
    trx_id = text
    doc_ref = db.collection('deposits').document()
    doc_ref.set({'user_id': u['id'], 'method': method, 'amount': final_bdt_amount, 'trx_id': trx_id, 'status': 'pending', 'time': now()})
    
    name = message.from_user.first_name or "User"
    uname = f"@{message.from_user.username}" if message.from_user.username else "NONE"
    
    adm_txt = f"💰 <b>Deposit Request</b>\n\n<b>Name:</b> {name}\n<b>User:</b> {uname} (<code>{u['id']}</code>)\n<b>Amount:</b> <code>{display_amount}</code>\n<b>Method:</b> {method.upper()}\n<b>TrxID:</b> <code>{trx_id}</code>\n<b>Time:</b> {now()}"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Approve", callback_data=f"admdep_app_{doc_ref.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"admdep_rej_{doc_ref.id}")
    )
    bot.send_message(ADMIN_ID, adm_txt, parse_mode="HTML", reply_markup=markup)
    bot.send_message(message.chat.id, LANG[lang]['pending'], reply_markup=main_menu(message.from_user.id, lang))

# --- Withdraw Flow ---
@bot.callback_query_handler(func=lambda call: call.data == "with_menu")
def with_menu(call):
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("bKash", callback_data="with_bkash"), InlineKeyboardButton("Nagad", callback_data="with_nagad"),
        InlineKeyboardButton("Rocket", callback_data="with_rocket"), InlineKeyboardButton("Upay", callback_data="with_upay"),
        InlineKeyboardButton("🟡 Binance USDT", callback_data="with_binance")
    )
    bot.edit_message_text("Select Withdraw Method:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("with_") and call.data != "with_menu")
def get_with_amount(call):
    bot.answer_callback_query(call.id)
    method = call.data.split("_")[1]
    u = get_user(call.from_user.id)
    cfg = get_config()
    lang = u.get('lang', 'bn')
    
    if method == 'binance':
        min_with = 5.0
        txt = "⚠️ Minimum withdraw is *$5 USDT*.\n\n✏️ *Enter withdraw amount in USDT:*"
        if lang == 'bn': txt = "⚠️ বাইনান্সে সর্বনিম্ন উত্তোলন *$5 USDT*.\n\n✏️ *উত্তোলনের পরিমাণ লিখুন (USDT):*"
        msg = bot.send_message(call.message.chat.id, txt, parse_mode="Markdown", reply_markup=cancel_menu(lang))
        bot.register_next_step_handler(msg, process_with_amount, method, min_with, u, True)
    else:
        min_with = cfg.get('min_with', 50.0)
        fmt_min = fmt_money(min_with, u.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
        msg = bot.send_message(call.message.chat.id, f"⚠️ Minimum withdraw is {fmt_min}.\n\n✏️ *Enter withdraw amount:*", parse_mode="Markdown", reply_markup=cancel_menu(lang))
        bot.register_next_step_handler(msg, process_with_amount, method, min_with, u, False)

def process_with_amount(message, method, min_with, u, is_usdt):
    text = message.text
    lang = u.get('lang', 'bn')
    if text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    if is_menu_button(text): return bot.send_message(message.chat.id, "Action canceled.", reply_markup=main_menu(message.from_user.id, lang))
    
    try:
        amount_input = float(text)
        if amount_input < min_with:
            msg = bot.send_message(message.chat.id, f"❌ Minimum is {min_with}. Try again:", reply_markup=cancel_menu(lang))
            return bot.register_next_step_handler(msg, process_with_amount, method, min_with, u, is_usdt)
            
        cfg = get_config()
        usdt_rate = cfg.get('usdt_rate', 120.0)
        required_bdt = amount_input * usdt_rate if is_usdt else amount_input
        
        if required_bdt > u.get('balance_bdt', 0):
            return bot.send_message(message.chat.id, "❌ Insufficient balance!", reply_markup=main_menu(u['id'], lang))
            
        if is_usdt:
            txt = "✏️ *Enter your BINANCE Address:*\nNetwork MUST be: *BSC BNB Smart Chain (BEP20)*"
            if lang == 'bn': txt = "✏️ *আপনার BINANCE অ্যাড্রেস দিন:*\nনেটওয়ার্ক অবশ্যই *BSC BNB Smart Chain (BEP20)* হতে হবে।"
        else:
            txt = f"✏️ *Enter your {method.upper()} Account Number:*"
            if lang == 'bn': txt = f"✏️ *আপনার {method.upper()} একাউন্ট নাম্বারটি দিন:*"
            
        msg = bot.send_message(message.chat.id, txt, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_with_number, method, required_bdt, amount_input, u, is_usdt)
    except:
        bot.send_message(message.chat.id, LANG[lang]['qty_err'], reply_markup=main_menu(message.from_user.id, lang))

def process_with_number(message, method, required_bdt, display_amount, u, is_usdt):
    text = message.text
    lang = u.get('lang', 'bn')
    if text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    if is_menu_button(text): return bot.send_message(message.chat.id, "Action canceled.", reply_markup=main_menu(message.from_user.id, lang))
    
    number = text
    doc_ref = db.collection('withdraws').document()
    doc_ref.set({'user_id': u['id'], 'method': method, 'amount': required_bdt, 'number': number, 'status': 'pending', 'time': now()})
    
    db.collection('users').document(u['id']).set({'balance_bdt': firestore.Increment(-required_bdt)}, merge=True)
    
    name = message.from_user.first_name or "User"
    uname = f"@{message.from_user.username}" if message.from_user.username else "NONE"
    
    show_amt = f"${display_amount} USDT" if is_usdt else f"{display_amount} BDT"

    adm_txt = f"📤 <b>Withdraw Request</b>\n\n<b>Name:</b> {name}\n<b>User:</b> {uname} (<code>{u['id']}</code>)\n<b>Amount:</b> <code>{show_amt}</code>\n<b>Method:</b> {method.upper()}\n<b>Address/Num:</b> <code>{number}</code>\n<b>Time:</b> {now()}"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Paid", callback_data=f"admwith_app_{doc_ref.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"admwith_rej_{doc_ref.id}")
    )
    bot.send_message(ADMIN_ID, adm_txt, parse_mode="HTML", reply_markup=markup)
    bot.send_message(message.chat.id, "✅ Withdraw request sent to admin!", reply_markup=main_menu(message.from_user.id, lang))

# ==========================================
# 8. Smart Buy Gmail System (Currency Supported)
# ==========================================
@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['buy'], LANG['bn']['buy']])
def buy_start(message):
    u = get_user(message.from_user.id)
    cfg = get_config()
    lang = u.get('lang', 'bn')
    fmt_price = fmt_money(cfg.get('buy_price', 15.0), u.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
    
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton(LANG[lang]['buy_confirm'], callback_data="buy_qty_ask"))
    bot.send_message(message.chat.id, LANG[lang]['buy_msg'].format(fmt_price), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_qty_ask")
def buy_qty_ask(call):
    bot.answer_callback_query(call.id) 
    u = get_user(call.from_user.id)
    cfg = get_config()
    price = cfg.get('buy_price', 15.0)
    bal = u.get('balance_bdt', 0.0)
    max_qty = int(bal // price)
    lang = u.get('lang', 'bn')
    
    if max_qty < 1:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton(LANG[lang]['deposit'], callback_data="dep_menu"))
        return bot.send_message(call.message.chat.id, LANG[lang]['no_bal'], reply_markup=markup)
        
    fmt_bal = fmt_money(bal, u.get('currency', 'BDT'), cfg.get('usdt_rate', 120))
    msg = bot.send_message(call.message.chat.id, LANG[lang]['buy_qty'].format(fmt_bal, max_qty), parse_mode="Markdown", reply_markup=cancel_menu(lang))
    bot.register_next_step_handler(msg, process_buy_qty, max_qty, price, u)

def process_buy_qty(message, max_qty, price, u):
    text = message.text
    lang = u.get('lang', 'bn')
    if text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    if is_menu_button(text): return bot.send_message(message.chat.id, "Action canceled.", reply_markup=main_menu(message.from_user.id, lang))
        
    try:
        qty = int(text)
        if qty <= 0: raise ValueError
        if qty > max_qty:
            msg = bot.send_message(message.chat.id, f"❌ You only have balance for {max_qty} Gmails. Try again:", reply_markup=cancel_menu(lang))
            return bot.register_next_step_handler(msg, process_buy_qty, max_qty, price, u)
            
        stock = list(db.collection('stock_gmails').where('status', '==', 'unsold').limit(qty).stream())
        avail = len(stock)
        
        if avail == 0:
            return bot.send_message(message.chat.id, "⚠️ Stock is empty!", reply_markup=main_menu(message.from_user.id, lang))
            
        if avail < qty:
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton(f"✅ Buy {avail}", callback_data=f"buy_exec_{avail}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")
            )
            bot.send_message(message.chat.id, LANG[lang]['stock_less'].format(avail, avail), reply_markup=markup)
        else:
            execute_buy(message.chat.id, u['id'], qty, price, lang, stock, u.get('currency', 'BDT'))
    except Exception as e:
        bot.send_message(message.chat.id, LANG[lang]['qty_err'], reply_markup=main_menu(message.from_user.id, lang))

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_exec_"))
def buy_exec_cb(call):
    bot.answer_callback_query(call.id)
    qty = int(call.data.split("_")[2])
    u = get_user(call.from_user.id)
    cfg = get_config()
    stock = list(db.collection('stock_gmails').where('status', '==', 'unsold').limit(qty).stream())
    bot.delete_message(call.message.chat.id, call.message.message_id)
    execute_buy(call.message.chat.id, str(call.from_user.id), qty, cfg.get('buy_price', 15.0), u.get('lang', 'bn'), stock, u.get('currency', 'BDT'))

@bot.callback_query_handler(func=lambda call: call.data == "cancel_action")
def cancel_inline(call):
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    u = get_user(call.from_user.id)
    bot.send_message(call.message.chat.id, LANG[u.get('lang', 'bn')]['canceled'], reply_markup=main_menu(call.from_user.id, u.get('lang', 'bn')))

def execute_buy(chat_id, user_id, qty, price, lang, stock_docs, currency):
    cost = qty * price
    db.collection('users').document(user_id).set({
        'balance_bdt': firestore.Increment(-cost),
        'total_bought': firestore.Increment(qty)
    }, merge=True)
    
    mail_list_txt = ""
    for doc in stock_docs:
        d = doc.to_dict()
        mail_list_txt += f"📧 `{d['email']}` | 🔑 `{d['password']}`\n"
        db.collection('stock_gmails').document(doc.id).update({'status': 'sold', 'bought_by': user_id, 'date': now()})
        
    cfg = get_config()
    rem_bal = get_user(user_id).get('balance_bdt', 0.0)
    fmt_rem = fmt_money(rem_bal, currency, cfg.get('usdt_rate', 120))
    
    final_msg = LANG[lang]['buy_success'].format(qty, fmt_rem, mail_list_txt)
    bot.send_message(chat_id, final_msg, parse_mode="Markdown", reply_markup=main_menu(user_id, lang))

# ==========================================
# 9. Sell Gmail System
# ==========================================
@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['sell'], LANG['bn']['sell']])
def sell_start(message):
    u = get_user(message.from_user.id)
    cfg = get_config()
    lang = u.get('lang', 'bn')
    curr = u.get('currency', 'BDT')
    usdt = cfg.get('usdt_rate', 120)
    
    p_new = fmt_money(cfg.get('sell_new',10), curr, usdt)
    p_old = fmt_money(cfg.get('sell_old',10), curr, usdt)
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(
        KeyboardButton(LANG[lang]['new_mail']), KeyboardButton(LANG[lang]['old_mail']), KeyboardButton(LANG[lang]['cancel'])
    )
    bot.send_message(message.chat.id, LANG[lang]['sell_type'].format(p_new, p_old), reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['new_mail'], LANG['bn']['new_mail']])
def sell_new(message):
    u = get_user(message.from_user.id)
    email = f"user_{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))}@gmail.com"
    msg = bot.send_message(message.chat.id, LANG[u.get('lang', 'bn')]['task_new'].format(email), parse_mode="Markdown", reply_markup=cancel_menu(u.get('lang', 'bn')))
    bot.register_next_step_handler(msg, process_sell_pass, email, "New", u)

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['old_mail'], LANG['bn']['old_mail']])
def sell_old(message):
    u = get_user(message.from_user.id)
    msg = bot.send_message(message.chat.id, LANG[u.get('lang', 'bn')]['task_old'], reply_markup=cancel_menu(u.get('lang', 'bn')))
    bot.register_next_step_handler(msg, process_sell_email, u)

def process_sell_email(message, u):
    text = message.text
    if text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    if is_menu_button(text): return bot.send_message(message.chat.id, "Action canceled.", reply_markup=main_menu(message.from_user.id, u.get('lang', 'bn')))
    
    email = text
    msg = bot.send_message(message.chat.id, LANG[u.get('lang', 'bn')]['task_pass'].format(email), parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_sell_pass, email, "Old", u)

def process_sell_pass(message, email, mail_type, u):
    text = message.text
    if text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    if is_menu_button(text): return bot.send_message(message.chat.id, "Action canceled.", reply_markup=main_menu(message.from_user.id, u.get('lang', 'bn')))
    
    password = text
    doc_ref = db.collection('pending_mails').document()
    doc_ref.set({'user_id': u['id'], 'email': email, 'password': password, 'type': mail_type, 'status': 'pending', 'time': now()})
    
    name = message.from_user.first_name or "User"
    uname = f"@{message.from_user.username}" if message.from_user.username else "NONE"

    adm_txt = f"🔔 <b>New Gmail Sell</b>\n\n<b>Name:</b> {name}\n<b>User:</b> {uname} (<code>{u['id']}</code>)\n<b>Type:</b> {mail_type}\n<b>Email:</b> <code>{email}</code>\n<b>Pass:</b> <code>{password}</code>\n<b>Time:</b> {now()}"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Approve", callback_data=f"admsell_app_{doc_ref.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"admsell_rej_{doc_ref.id}")
    )
    bot.send_message(ADMIN_ID, adm_txt, parse_mode="HTML", reply_markup=markup)
    bot.send_message(message.chat.id, LANG[u.get('lang', 'bn')]['pending'], reply_markup=main_menu(message.from_user.id, u.get('lang', 'bn')))

# ==========================================
# 10. Interactive Super Admin Panel
# ==========================================
def get_admin_main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚙️ Price Setup", callback_data="adm_menu_price"),
        InlineKeyboardButton("💳 Wallet Mgmt", callback_data="adm_menu_wallet"),
        InlineKeyboardButton("💰 Dep/With Mgmt", callback_data="adm_menu_depwith"),
        InlineKeyboardButton("🎁 Refer Mgmt", callback_data="adm_menu_ref"),
        InlineKeyboardButton("📝 Customize Text", callback_data="adm_menu_texts"),
        InlineKeyboardButton("📢 Broadcasts", callback_data="adm_menu_broad"),
        InlineKeyboardButton("📊 Bot Status", callback_data="adm_menu_status"),
        InlineKeyboardButton("📧 Mails List", callback_data="adm_menu_mails"),
        InlineKeyboardButton("➕ Add Stock", callback_data="adm_menu_addstock")
    )
    return markup

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['admin_btn'], LANG['bn']['admin_btn']] and msg.from_user.id == ADMIN_ID)
def admin_panel(message):
    bot.send_message(ADMIN_ID, "👑 *Super Admin Panel*\nSelect an option to manage your bot:", parse_mode="Markdown", reply_markup=get_admin_main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_menu_"))
def admin_menu_handler(call):
    bot.answer_callback_query(call.id) 
    if call.from_user.id != ADMIN_ID: return
    action = call.data.split("_")[2]
    
    if action == "price":
        markup = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("🛒 Buy Price (BDT)", callback_data="adm_edit_config_buy_price"),
            InlineKeyboardButton("🆕 Sell New Price (BDT)", callback_data="adm_edit_config_sell_new"),
            InlineKeyboardButton("🔄 Sell Old Price (BDT)", callback_data="adm_edit_config_sell_old"),
            InlineKeyboardButton("💵 USDT Rate (1$ = ? BDT)", callback_data="adm_edit_config_usdt_rate"),
            InlineKeyboardButton("🔙 Back", callback_data="adm_menu_back")
        )
        bot.edit_message_text("⚙️ *Price Setup*\nSelect which price to update:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif action == "wallet":
        markup = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("bKash", callback_data="adm_edit_payments_bkash"),
            InlineKeyboardButton("Nagad", callback_data="adm_edit_payments_nagad"),
            InlineKeyboardButton("Rocket", callback_data="adm_edit_payments_rocket"),
            InlineKeyboardButton("Upay", callback_data="adm_edit_payments_upay"),
            InlineKeyboardButton("Binance (BEP20)", callback_data="adm_edit_payments_binance"),
            InlineKeyboardButton("🔙 Back", callback_data="adm_menu_back")
        )
        bot.edit_message_text("💳 *Wallet Management*\nSelect method to update number/address:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif action == "texts":
        markup = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("Welcome Message (EN)", callback_data="adm_edit_texts_welcome_en"),
            InlineKeyboardButton("Welcome Message (BN)", callback_data="adm_edit_texts_welcome_bn"),
            InlineKeyboardButton("Help Message (EN)", callback_data="adm_edit_texts_help_en"),
            InlineKeyboardButton("Help Message (BN)", callback_data="adm_edit_texts_help_bn"),
            InlineKeyboardButton("Banner Image (URL)", callback_data="adm_edit_texts_banner_id"),
            InlineKeyboardButton("Support Link", callback_data="adm_edit_config_support_link"),
            InlineKeyboardButton("🔙 Back", callback_data="adm_menu_back")
        )
        bot.edit_message_text("📝 *Customize Texts*\nSelect what you want to edit:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif action == "depwith":
        markup = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("📥 Min Deposit (BDT)", callback_data="adm_edit_config_min_dep"),
            InlineKeyboardButton("📤 Min Withdraw (BDT)", callback_data="adm_edit_config_min_with"),
            InlineKeyboardButton("🔙 Back", callback_data="adm_menu_back")
        )
        bot.edit_message_text("💰 *Deposit & Withdraw Settings*\nSelect which one to update:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif action == "ref":
        msg = bot.send_message(ADMIN_ID, "✏️ *Enter new Refer Bonus amount (BDT):*\n(Type /cancel to abort)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_input, 'ref_bonus', 'config')
        
    elif action == "broad":
        msg = bot.send_message(ADMIN_ID, "📢 *Enter message to broadcast to all users:*\n(Type /cancel to abort)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_input, 'none', 'broadcast')
        
    elif action == "addstock":
        msg = bot.send_message(ADMIN_ID, "➕ *Add Stock*\nSend emails and passwords in this format:\n`email1@gmail.com:pass1`\n`email2@gmail.com:pass2`\n(Type /cancel to abort)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_input, 'none', 'addstock')
        
    elif action == "status":
        users = len(list(db.collection('users').stream()))
        
        stock_all = list(db.collection('stock_gmails').stream())
        unsold = sum(1 for s in stock_all if s.to_dict().get('status') == 'unsold')
        sold = sum(1 for s in stock_all if s.to_dict().get('status') == 'sold')
        
        deposits = list(db.collection('deposits').where('status', '==', 'approved').stream())
        total_income = sum(d.to_dict().get('amount', 0) for d in deposits)
        
        withdraws = list(db.collection('withdraws').where('status', '==', 'paid').stream())
        total_paid = sum(w.to_dict().get('amount', 0) for w in withdraws)
        
        txt = f"📊 *Advanced Bot Status*\n\n👥 Total Users: `{users}`\n📦 Available Stock: `{unsold}`\n🛒 Sold Mails: `{sold}`\n💰 Total Income: `{total_income}` BDT\n💸 Total Paid: `{total_paid}` BDT"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="adm_menu_back")))
        
    elif action == "mails":
        pending = len(list(db.collection('pending_mails').where('status', '==', 'pending').stream()))
        sold = len(list(db.collection('stock_gmails').where('status', '==', 'sold').stream()))
        bot.edit_message_text(f"📧 *Mail Stats*\n⏳ Pending Approvals: `{pending}`\n🛒 Sold Mails: `{sold}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="adm_menu_back")))

    elif action == "back":
        bot.edit_message_text("👑 *Super Admin Panel*\nSelect an option to manage your bot:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_admin_main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_edit_"))
def admin_edit_handler(call):
    bot.answer_callback_query(call.id)
    parts = call.data.split("_", 3)
    cat = parts[2]
    field = parts[3]
    msg = bot.send_message(call.message.chat.id, f"✏️ Enter new value for `{field}`:\n(Type /cancel to abort)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_admin_input, field, cat)

def process_admin_input(message, field, category):
    if message.text.lower() == '/cancel': return bot.send_message(message.chat.id, "❌ Action Canceled.")
    val = message.text
    try:
        if category == 'config':
            if field == 'support_link':
                db.collection('settings').document('config').update({field: val})
            else:
                val = float(val)
                db.collection('settings').document('config').update({field: val})
            bot.send_message(message.chat.id, f"✅ Settings updated! `{field}` is now `{val}`", parse_mode="Markdown")
            
        elif category == 'payments':
            db.collection('settings').document('payments').update({field: val})
            bot.send_message(message.chat.id, f"✅ Payment method `{field}` updated to `{val}`", parse_mode="Markdown")
            
        elif category == 'texts':
            db.collection('settings').document('texts').update({field: val})
            bot.send_message(message.chat.id, f"✅ Text updated successfully!", parse_mode="Markdown")
            
        elif category == 'broadcast':
            users = db.collection('users').stream()
            c = 0
            for u in users:
                try:
                    bot.send_message(u.id, f"📢 *Notice:*\n\n{val}", parse_mode="Markdown")
                    c += 1
                except: pass
            bot.send_message(message.chat.id, f"✅ Broadcast sent to {c} users.")
            
        elif category == 'addstock':
            lines = val.split('\n')
            c = 0
            for line in lines:
                if ":" in line:
                    em, pw = line.split(":", 1)
                    db.collection('stock_gmails').add({'email': em.strip(), 'password': pw.strip(), 'status': 'unsold', 'added_by': 'Admin', 'date': now()})
                    c += 1
            bot.send_message(message.chat.id, f"✅ {c} Mails added to stock!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: Please enter valid input.")

# --- Admin Approvals (Dep, With, Sell) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm"))
def admin_approvals(call):
    bot.answer_callback_query(call.id) 
    if call.from_user.id != ADMIN_ID: return
    parts = call.data.split("_")
    cat = parts[0] 
    action = parts[1] 
    doc_id = parts[2]
    
    try:
        if cat == "admdep":
            doc_ref = db.collection('deposits').document(doc_id)
            d = doc_ref.get().to_dict()
            if not d or d.get('status') != 'pending': return bot.send_message(ADMIN_ID, "Already processed")
            
            if action == "app":
                doc_ref.update({'status': 'approved'})
                db.collection('users').document(d['user_id']).set({'balance_bdt': firestore.Increment(d['amount'])}, merge=True)
                
                u_curr = get_user(d['user_id']).get('currency', 'BDT')
                fmt_amt = fmt_money(d['amount'], u_curr, get_config().get('usdt_rate', 120))
                
                bot.send_message(d['user_id'], f"✅ Your deposit of {fmt_amt} has been approved!")
                bot.edit_message_text(f"✅ Approved <b>{d['amount']} BDT</b>", ADMIN_ID, call.message.message_id, parse_mode="HTML")
            else:
                doc_ref.update({'status': 'rejected'})
                bot.send_message(d['user_id'], f"❌ Your deposit request was rejected.")
                bot.edit_message_text(f"❌ Rejected <b>{d['amount']} BDT</b>", ADMIN_ID, call.message.message_id, parse_mode="HTML")

        elif cat == "admwith":
            doc_ref = db.collection('withdraws').document(doc_id)
            d = doc_ref.get().to_dict()
            if not d or d.get('status') != 'pending': return bot.send_message(ADMIN_ID, "Already processed")
            
            if action == "app":
                doc_ref.update({'status': 'paid'})
                bot.send_message(d['user_id'], f"✅ Your withdraw request has been PAID!")
                bot.edit_message_text(f"✅ Paid <b>{d['amount']} BDT</b>", ADMIN_ID, call.message.message_id, parse_mode="HTML")
            else:
                doc_ref.update({'status': 'rejected'})
                db.collection('users').document(d['user_id']).set({'balance_bdt': firestore.Increment(d['amount'])}, merge=True) # Refund
                bot.send_message(d['user_id'], f"❌ Your withdraw request was rejected. Balance refunded.")
                bot.edit_message_text(f"❌ Rejected <b>{d['amount']} BDT</b>", ADMIN_ID, call.message.message_id, parse_mode="HTML")

        elif cat == "admsell":
            doc_ref = db.collection('pending_mails').document(doc_id)
            m = doc_ref.get().to_dict()
            if not m or m.get('status') != 'pending': return bot.send_message(ADMIN_ID, "Already processed")
            
            cfg = get_config()
            reward = cfg.get('sell_new',10) if m['type'] == 'New' else cfg.get('sell_old',10)
            
            if action == "app":
                doc_ref.update({'status': 'approved'})
                db.collection('users').document(m['user_id']).set({'balance_bdt': firestore.Increment(reward), 'total_sold': firestore.Increment(1)}, merge=True)
                db.collection('stock_gmails').add({'email': m['email'], 'password': m['password'], 'status': 'unsold', 'added_by': m['user_id'], 'date': now()})
                bot.send_message(m['user_id'], f"✅ Admin approved your {m['type']} Gmail `{m['email']}`! Bonus added.", parse_mode="Markdown")
                bot.edit_message_text(f"✅ Mail Approved & Added to Stock", ADMIN_ID, call.message.message_id)
            else:
                doc_ref.update({'status': 'rejected'})
                bot.send_message(m['user_id'], f"❌ Admin rejected your Gmail `{m['email']}`.", parse_mode="Markdown")
                bot.edit_message_text(f"❌ Mail Rejected", ADMIN_ID, call.message.message_id)
                
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Action failed: {e}")

# ==========================================
# 11. Fake Web Server for Render & Bot Start
# ==========================================
app = Flask(__name__)

@app.route('/')
def home(): return "Bot is running perfectly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print("🤖 Premium Gmail Bot is running (V7 Crypto & Pending Ref Fixes)...")
    bot.remove_webhook()
    web_thread = threading.Thread(target=run_web)
    web_thread.start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
