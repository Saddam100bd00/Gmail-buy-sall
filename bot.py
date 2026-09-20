import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random
import string
from datetime import datetime

# ==========================================
# 1. Setup & Initialization
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789")) 
bot = telebot.TeleBot(BOT_TOKEN)

# --- Firebase Setup (Render Secret File) ---
try:
    cred = credentials.Certificate("firebase_cred.json") 
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🔥 Firebase Connected Successfully!")
except Exception as e:
    print(f"❌ Firebase Connection Error: {e}")

# Payment Accounts (Can be updated dynamically later if needed)
PAYMENT_METHODS = {
    'bkash': '017XXXXXXXX (Personal)', 
    'nagad': '017XXXXXXXX (Personal)', 
    'binance': 'Pay ID: 123456789'     
}

# ==========================================
# 2. Dynamic Settings Fetcher
# ==========================================
def get_settings():
    doc = db.collection('settings').document('config').get()
    if doc.exists:
        return doc.to_dict()
    default_config = {'buy_price': 15.0, 'sell_price': 10.0, 'ref_bonus': 5.0}
    db.collection('settings').document('config').set(default_config)
    return default_config

# ==========================================
# 3. Multi-Language Dictionary
# ==========================================
LANG = {
    'en': {
        'welcome': "Welcome to Premium Gmail Market! 🌐\nSelect an option below:",
        'buy': "🛒 Buy Gmail", 'sell': "🤝 Sell Gmail",
        'wallet': "💳 Wallet", 'profile': "👤 Profile",
        'refer': "🎁 Refer & Earn", 'stock': "📊 Stock Info",
        'history': "📜 History", 'help': "📖 Help",
        'lang': "🌐 Change Language", 'cancel': "❌ Cancel",
        'profile_txt': "👤 *Your Profile*\nID: `{}`\nUsername: @{}\n\n💰 *Balance*\nBDT: `{}` ৳\n\n🛒 Bought: {}\n🤝 Sold: {}\n🎁 Referrals: {}",
        'wallet_msg': "Select an option from your wallet:",
        'deposit': "📥 Deposit", 'withdraw': "📤 Withdraw",
        'select_payment': "Select your payment method:",
        'send_money': "Please send money to this {}:\n👉 `{}`\n\nAfter sending, enter your *TrxID* (Transaction ID) below:",
        'withdraw_amount': "Enter amount to withdraw (Min 50 BDT):",
        'withdraw_number': "Enter your {} account number:",
        'pending_dep': "✅ Deposit request sent to admin! Please wait for approval.",
        'pending_with': "✅ Withdraw request sent! You will receive money soon.",
        'refer_txt': "🎁 *Refer & Earn*\n\nShare your link with friends. When they join and use the bot, you get `{}` BDT bonus!\n\n🔗 Your Link: `https://t.me/{}?start={}`",
        'sell_type': "What kind of Gmail do you want to sell?\n(You will get {} BDT per mail)",
        'new_mail': "🆕 New Gmail", 'old_mail': "🔄 Old Gmail",
        'task_new': "Create a new Gmail using this username:\n👉 `{}`\n\nSend the *Password* here after creating:",
        'task_old': "Enter the Old Gmail Address:",
        'task_pass': "Enter password for `{}`:",
        'buy_msg': "Gmail Price: {} BDT\nDo you want to buy?",
        'buy_confirm': "✅ Confirm Buy", 'no_balance': "❌ Insufficient balance! Please deposit.",
        'buy_success': "🎉 *Purchase Successful!*\n\nEmail: `{}`\nPass: `{}`\nDate: {}",
        'out_of_stock': "⚠️ Sorry, Gmails are currently out of stock. Try again later.",
        'stock_info': "📊 *Live Stock Info*\n\nAvailable Gmails: `{}`",
        'history_empty': "📜 You haven't bought any Gmails yet.",
        'help_txt': "📖 *Help & Rules*\n\n1. Do not submit wrong passwords.\n2. Minimum withdraw is 50 BDT.\n3. Fake deposit requests will lead to a ban.\n\nSupport: @YourAdminUsername",
        'canceled': "Action canceled. Returned to main menu.",
        'banned': "🚫 You have been banned from using this bot by the admin."
    },
    'bn': {
        'welcome': "প্রিমিয়াম জিমেইল মার্কেটে স্বাগতম! 🌐\nনিচের একটি অপশন বেছে নিন:",
        'buy': "🛒 জিমেইল কিনুন", 'sell': "🤝 জিমেইল বিক্রি করুন",
        'wallet': "💳 ওয়ালেট", 'profile': "👤 প্রোফাইল",
        'refer': "🎁 রেফার এন্ড আর্ন", 'stock': "📊 স্টক ইনফো",
        'history': "📜 ইতিহাস", 'help': "📖 সাহায্য",
        'lang': "🌐 ভাষা পরিবর্তন", 'cancel': "❌ বাতিল করুন",
        'profile_txt': "👤 *আপনার প্রোফাইল*\nআইডি: `{}`\nইউজারনেম: @{}\n\n💰 *ব্যালেন্স*\nBDT: `{}` ৳\n\n🛒 কেনা হয়েছে: {}\n🤝 বিক্রি হয়েছে: {}\n🎁 রেফারেল: {}",
        'wallet_msg': "আপনার ওয়ালেট থেকে একটি অপশন নির্বাচন করুন:",
        'deposit': "📥 ডিপোজিট", 'withdraw': "📤 টাকা উত্তোলন",
        'select_payment': "আপনার পেমেন্ট মেথড নির্বাচন করুন:",
        'send_money': "অনুগ্রহ করে এই {} নাম্বারে টাকা পাঠান:\n👉 `{}`\n\nটাকা পাঠানোর পর আপনার *TrxID* (ট্রানজেকশন আইডি) নিচে দিন:",
        'withdraw_amount': "উত্তোলনের পরিমাণ লিখুন (সর্বনিম্ন ৫০ টাকা):",
        'withdraw_number': "আপনার {} একাউন্ট নাম্বারটি দিন:",
        'pending_dep': "✅ ডিপোজিট রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে! অপডেটের জন্য অপেক্ষা করুন।",
        'pending_with': "✅ উইথড্র রিকোয়েস্ট পাঠানো হয়েছে! খুব শীঘ্রই টাকা পেয়ে যাবেন।",
        'refer_txt': "🎁 *রেফার করে আয় করুন*\n\nআপনার বন্ধুদের সাথে লিংক শেয়ার করুন। তারা জয়েন করলে আপনি `{}` টাকা বোনাস পাবেন!\n\n🔗 আপনার লিংক: `https://t.me/{}?start={}`",
        'sell_type': "আপনি কোন ধরনের জিমেইল বিক্রি করতে চান?\n(প্রতিটি জিমেইলে পাবেন {} টাকা)",
        'new_mail': "🆕 নতুন জিমেইল", 'old_mail': "🔄 পুরাতন জিমেইল",
        'task_new': "এই ইউজারনেমটি দিয়ে একটি নতুন জিমেইল খুলুন:\n👉 `{}`\n\nখোলার পর *পাসওয়ার্ডটি* নিচে দিন:",
        'task_old': "আপনার পুরাতন জিমেইল এড্রেসটি দিন:",
        'task_pass': "`{}` এর পাসওয়ার্ডটি দিন:",
        'buy_msg': "প্রতিটি জিমেইলের দাম: {} টাকা\nআপনি কি কিনতে চান?",
        'buy_confirm': "✅ কনফার্ম করুন", 'no_balance': "❌ আপনার ব্যালেন্স কম! দয়া করে ডিপোজিট করুন।",
        'buy_success': "🎉 *সফলভাবে কেনা হয়েছে!*\n\nইমেইল: `{}`\nপাসওয়ার্ড: `{}`\nতারিখ: {}",
        'out_of_stock': "⚠️ দুঃখিত, বর্তমানে স্টকে কোনো জিমেইল নেই। পরে আবার চেষ্টা করুন।",
        'stock_info': "📊 *লাইভ স্টক ইনফো*\n\nবর্তমানে স্টকে থাকা জিমেইল: `{}` টি",
        'history_empty': "📜 আপনি এখনো কোনো জিমেইল কিনেননি।",
        'help_txt': "📖 *নিয়মাবলি ও সাহায্য*\n\n১. ভুল পাসওয়ার্ড সাবমিট করবেন না।\n২. সর্বনিম্ন উত্তোলন ৫০ টাকা।\n৩. ভুয়া ডিপোজিট রিকোয়েস্ট দিলে ব্যান করা হবে।\n\nসাপোর্ট: @YourAdminUsername",
        'canceled': "অ্যাকশন বাতিল করা হয়েছে। মূল মেনুতে ফিরে যাওয়া হলো।",
        'banned': "🚫 আপনাকে অ্যাডমিন কর্তৃক ব্যান করা হয়েছে। আপনি বটটি ব্যবহার করতে পারবেন না।"
    }
}

# ==========================================
# 4. Helper & Middleware Functions
# ==========================================
def get_user_lang(user_id):
    user_ref = db.collection('users').document(str(user_id)).get()
    return user_ref.to_dict().get('lang', 'en') if user_ref.exists else 'en'

def is_banned(user_id):
    user_ref = db.collection('users').document(str(user_id)).get()
    if user_ref.exists and user_ref.to_dict().get('status') == 'banned':
        return True
    return False

def main_menu(lang):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(LANG[lang]['buy']), KeyboardButton(LANG[lang]['sell']),
        KeyboardButton(LANG[lang]['wallet']), KeyboardButton(LANG[lang]['profile']),
        KeyboardButton(LANG[lang]['stock']), KeyboardButton(LANG[lang]['history']),
        KeyboardButton(LANG[lang]['refer']), KeyboardButton(LANG[lang]['help']),
        KeyboardButton(LANG[lang]['lang'])
    )
    return markup

def cancel_menu(lang):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(LANG[lang]['cancel']))
    return markup

def generate_email():
    return f"user_{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))}@gmail.com"

# --- Cancel Action ---
@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['cancel'], LANG['bn']['cancel']])
def cancel_action(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    lang = get_user_lang(message.from_user.id)
    bot.send_message(message.chat.id, LANG[lang]['canceled'], reply_markup=main_menu(lang))

# ==========================================
# 5. User Registration & Start
# ==========================================
@bot.message_handler(commands=['start'])
def start_bot(message):
    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, LANG['en']['banned'])
        return

    username = message.from_user.username or "User"
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None

    user_ref = db.collection('users').document(user_id)
    if not user_ref.get().exists:
        user_ref.set({
            'id': user_id, 'username': username, 'lang': 'en',
            'balance_bdt': 0.0, 'total_bought': 0, 'total_sold': 0, 
            'total_ref': 0, 'referred_by': referrer_id, 'status': 'active',
            'join_date': datetime.now().strftime("%Y-%m-%d")
        })
        # Add refer bonus
        if referrer_id and referrer_id != user_id:
            cfg = get_settings()
            ref_user = db.collection('users').document(referrer_id)
            if ref_user.get().exists:
                ref_user.update({'balance_bdt': firestore.Increment(cfg['ref_bonus']), 'total_ref': firestore.Increment(1)})
                bot.send_message(referrer_id, f"🎉 You received {cfg['ref_bonus']} BDT for a new referral!")

    lang = get_user_lang(user_id)
    bot.send_message(message.chat.id, LANG[lang]['welcome'], reply_markup=main_menu(lang))

# ==========================================
# 6. Basic Menus (Profile, Lang, Help, Stock, History)
# ==========================================
@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['profile'], LANG['bn']['profile']])
def profile_handler(message):
    if is_banned(message.from_user.id): return
    user_id = str(message.from_user.id)
    lang = get_user_lang(user_id)
    data = db.collection('users').document(user_id).get().to_dict()
    text = LANG[lang]['profile_txt'].format(
        user_id, data.get('username','N/A'), data.get('balance_bdt',0),
        data.get('total_bought',0), data.get('total_sold',0), data.get('total_ref',0)
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['help'], LANG['bn']['help']])
def help_handler(message):
    lang = get_user_lang(message.from_user.id)
    bot.send_message(message.chat.id, LANG[lang]['help_txt'], parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['stock'], LANG['bn']['stock']])
def stock_handler(message):
    lang = get_user_lang(message.from_user.id)
    stock_count = len(list(db.collection('stock_gmails').where('status', '==', 'unsold').stream()))
    bot.send_message(message.chat.id, LANG[lang]['stock_info'].format(stock_count), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['history'], LANG['bn']['history']])
def history_handler(message):
    user_id = str(message.from_user.id)
    lang = get_user_lang(user_id)
    purchases = db.collection('stock_gmails').where('bought_by', '==', user_id).stream()
    
    history_text = "📜 *Your Purchase History*\n\n"
    count = 0
    for doc in purchases:
        d = doc.to_dict()
        history_text += f"📧 `{d['email']}`\n🔑 `{d['password']}`\n\n"
        count += 1
        
    if count == 0:
        bot.send_message(message.chat.id, LANG[lang]['history_empty'])
    else:
        bot.send_message(message.chat.id, history_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['refer'], LANG['bn']['refer']])
def refer_handler(message):
    lang = get_user_lang(message.from_user.id)
    bot_info = bot.get_me()
    cfg = get_settings()
    text = LANG[lang]['refer_txt'].format(cfg['ref_bonus'], bot_info.username, message.from_user.id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['lang'], LANG['bn']['lang']])
def lang_handler(message):
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        InlineKeyboardButton("বাংলা 🇧🇩", callback_data="lang_bn")
    )
    bot.send_message(message.chat.id, "Select your language:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_lang(call):
    new_lang = call.data.split("_")[1]
    db.collection('users').document(str(call.from_user.id)).update({'lang': new_lang})
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Language Updated! ✅", reply_markup=main_menu(new_lang))

# ==========================================
# 7. Wallet (Deposit & Withdraw)
# ==========================================
@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['wallet'], LANG['bn']['wallet']])
def wallet_handler(message):
    if is_banned(message.from_user.id): return
    lang = get_user_lang(message.from_user.id)
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton(LANG[lang]['deposit'], callback_data="wallet_dep"),
        InlineKeyboardButton(LANG[lang]['withdraw'], callback_data="wallet_with")
    )
    bot.send_message(message.chat.id, LANG[lang]['wallet_msg'], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wallet_"))
def wallet_action(call):
    action = call.data.split("_")[1]
    lang = get_user_lang(call.from_user.id)
    markup = InlineKeyboardMarkup(row_width=3).add(
        InlineKeyboardButton("bKash", callback_data=f"pay_{action}_bkash"),
        InlineKeyboardButton("Nagad", callback_data=f"pay_{action}_nagad"),
        InlineKeyboardButton("Binance", callback_data=f"pay_{action}_binance")
    )
    bot.edit_message_text(LANG[lang]['select_payment'], call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def payment_method(call):
    _, action, method = call.data.split("_")
    lang = get_user_lang(call.from_user.id)
    if action == "dep":
        msg = bot.send_message(call.message.chat.id, LANG[lang]['send_money'].format(method.upper(), PAYMENT_METHODS[method]), parse_mode="Markdown", reply_markup=cancel_menu(lang))
        bot.register_next_step_handler(msg, process_deposit, method, lang)
    elif action == "with":
        msg = bot.send_message(call.message.chat.id, LANG[lang]['withdraw_amount'], reply_markup=cancel_menu(lang))
        bot.register_next_step_handler(msg, process_with_amount, method, lang)

def process_deposit(message, method, lang):
    if message.text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    trx_id = message.text
    user_id = str(message.from_user.id)
    
    doc_ref = db.collection('deposits').document()
    doc_ref.set({'user_id': user_id, 'method': method, 'trx_id': trx_id, 'status': 'pending', 'date': datetime.now().strftime("%Y-%m-%d %H:%M")})
    
    admin_txt = f"💰 *Deposit Request*\nUser: `{user_id}`\nMethod: {method}\nTrxID: `{trx_id}`"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Approve", callback_data=f"adep_app_{doc_ref.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"adep_rej_{doc_ref.id}")
    )
    bot.send_message(ADMIN_ID, admin_txt, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(message.chat.id, LANG[lang]['pending_dep'], reply_markup=main_menu(lang))

def process_with_amount(message, method, lang):
    if message.text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    amount = message.text
    msg = bot.send_message(message.chat.id, LANG[lang]['withdraw_number'].format(method.upper()))
    bot.register_next_step_handler(msg, process_with_number, method, amount, lang)

def process_with_number(message, method, amount, lang):
    if message.text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    number = message.text
    user_id = str(message.from_user.id)
    
    doc_ref = db.collection('withdraws').document()
    doc_ref.set({'user_id': user_id, 'method': method, 'amount': amount, 'number': number, 'status': 'pending'})
    
    admin_txt = f"📤 *Withdraw Request*\nUser: `{user_id}`\nAmount: `{amount}`\nMethod: {method}\nNumber: `{number}`"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Paid", callback_data=f"awith_app_{doc_ref.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"awith_rej_{doc_ref.id}")
    )
    bot.send_message(ADMIN_ID, admin_txt, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(message.chat.id, LANG[lang]['pending_with'], reply_markup=main_menu(lang))

# ==========================================
# 8. Buy & Sell Gmail
# ==========================================
@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['sell'], LANG['bn']['sell']])
def sell_handler(message):
    if is_banned(message.from_user.id): return
    lang = get_user_lang(message.from_user.id)
    cfg = get_settings()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton(LANG[lang]['new_mail']), KeyboardButton(LANG[lang]['old_mail']), KeyboardButton(LANG[lang]['cancel']))
    bot.send_message(message.chat.id, LANG[lang]['sell_type'].format(cfg['sell_price']), reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['new_mail'], LANG['bn']['new_mail']])
def sell_new(message):
    lang = get_user_lang(message.from_user.id)
    email = generate_email()
    msg = bot.send_message(message.chat.id, LANG[lang]['task_new'].format(email), parse_mode="Markdown", reply_markup=cancel_menu(lang))
    bot.register_next_step_handler(msg, process_sell_pass, email, "New", lang)

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['old_mail'], LANG['bn']['old_mail']])
def sell_old(message):
    lang = get_user_lang(message.from_user.id)
    msg = bot.send_message(message.chat.id, LANG[lang]['task_old'], reply_markup=cancel_menu(lang))
    bot.register_next_step_handler(msg, process_sell_email, lang)

def process_sell_email(message, lang):
    if message.text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    email = message.text
    msg = bot.send_message(message.chat.id, LANG[lang]['task_pass'].format(email), parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_sell_pass, email, "Old", lang)

def process_sell_pass(message, email, mail_type, lang):
    if message.text in [LANG['en']['cancel'], LANG['bn']['cancel']]: return cancel_action(message)
    password = message.text
    user_id = str(message.from_user.id)
    
    doc_ref = db.collection('pending_mails').document()
    doc_ref.set({'user_id': user_id, 'email': email, 'password': password, 'type': mail_type, 'status': 'pending'})
    
    admin_txt = f"🔔 *New Gmail Sell*\nType: {mail_type}\nEmail: `{email}`\nPass: `{password}`\nUser: `{user_id}`"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Approve", callback_data=f"asell_app_{doc_ref.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"asell_rej_{doc_ref.id}")
    )
    bot.send_message(ADMIN_ID, admin_txt, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(message.chat.id, LANG[lang]['pending_dep'], reply_markup=main_menu(lang))

@bot.message_handler(func=lambda msg: msg.text in [LANG['en']['buy'], LANG['bn']['buy']])
def buy_handler(message):
    if is_banned(message.from_user.id): return
    lang = get_user_lang(message.from_user.id)
    cfg = get_settings()
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton(LANG[lang]['buy_confirm'], callback_data="buy_confirm"))
    bot.send_message(message.chat.id, LANG[lang]['buy_msg'].format(cfg['buy_price']), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_confirm")
def process_buy(call):
    user_id = str(call.from_user.id)
    lang = get_user_lang(user_id)
    cfg = get_settings()
    user_ref = db.collection('users').document(user_id)
    user_data = user_ref.get().to_dict()
    
    if user_data['balance_bdt'] < cfg['buy_price']:
        bot.answer_callback_query(call.id, LANG[lang]['no_balance'], show_alert=True)
        return
        
    stock_ref = db.collection('stock_gmails').where('status', '==', 'unsold').limit(1).get()
    if not stock_ref:
        bot.answer_callback_query(call.id, LANG[lang]['out_of_stock'], show_alert=True)
        return
        
    mail_doc = stock_ref[0]
    mail_data = mail_doc.to_dict()
    
    # Update DB
    user_ref.update({'balance_bdt': firestore.Increment(-cfg['buy_price']), 'total_bought': firestore.Increment(1)})
    db.collection('stock_gmails').document(mail_doc.id).update({'status': 'sold', 'bought_by': user_id, 'buy_date': datetime.now().strftime("%Y-%m-%d")})
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    date_now = datetime.now().strftime("%d-%m-%Y")
    bot.send_message(call.message.chat.id, LANG[lang]['buy_success'].format(mail_data['email'], mail_data['password'], date_now), parse_mode="Markdown")

# ==========================================
# 9. Super Admin Panel & Controls
# ==========================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    total_users = len(list(db.collection('users').stream()))
    stock_count = len(list(db.collection('stock_gmails').where('status', '==', 'unsold').stream()))
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚙️ Change Prices", callback_data="adm_prices"),
        InlineKeyboardButton("🚫 Ban User", callback_data="adm_ban"),
        InlineKeyboardButton("✅ Unban User", callback_data="adm_unban")
    )
    
    text = f"👑 *Admin Dashboard*\n\n👥 Total Users: {total_users}\n📦 Available Stock: {stock_count}\n\n*Commands:*\n`/addstock email:pass`\n`/broadcast Message`"
    bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['addstock'])
def admin_add_stock(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        data = message.text.split()[1]
        email, password = data.split(":")
        db.collection('stock_gmails').add({'email': email, 'password': password, 'status': 'unsold'})
        bot.reply_to(message, "✅ Gmail added to stock!")
    except:
        bot.reply_to(message, "⚠️ Format error. Use: `/addstock email@gmail.com:password123`", parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast ", "")
    users = db.collection('users').stream()
    success = 0
    for u in users:
        try:
            bot.send_message(u.id, f"📢 *Admin Notice*\n\n{text}", parse_mode="Markdown")
            success += 1
        except: pass
    bot.reply_to(message, f"✅ Broadcast sent to {success} users.")

# --- Admin Inline Actions ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_inline_actions(call):
    if call.from_user.id != ADMIN_ID: return
    action = call.data.split("_")[1]
    
    if action == "prices":
        cfg = get_settings()
        text = f"Current Prices:\nBuy: {cfg['buy_price']}\nSell: {cfg['sell_price']}\nRefer: {cfg['ref_bonus']}\n\nTo change, use command:\n`/setprice buy 20`\n`/setprice sell 12`\n`/setprice ref 6`"
        bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    elif action == "ban":
        msg = bot.send_message(ADMIN_ID, "Send User ID to Ban:")
        bot.register_next_step_handler(msg, perform_ban, 'banned')
    elif action == "unban":
        msg = bot.send_message(ADMIN_ID, "Send User ID to Unban:")
        bot.register_next_step_handler(msg, perform_ban, 'active')

def perform_ban(message, status):
    target_id = message.text
    try:
        db.collection('users').document(target_id).update({'status': status})
        bot.reply_to(message, f"✅ User {target_id} is now {status}!")
    except:
        bot.reply_to(message, "❌ User not found or error occurred.")

@bot.message_handler(commands=['setprice'])
def set_price_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, p_type, amount = message.text.split()
        amount = float(amount)
        field = 'buy_price' if p_type == 'buy' else ('sell_price' if p_type == 'sell' else 'ref_bonus')
        db.collection('settings').document('config').update({field: amount})
        bot.reply_to(message, f"✅ {field} updated to {amount} BDT.")
    except:
        bot.reply_to(message, "⚠️ Use: `/setprice buy 20`")

# --- Admin Approvals ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("adep_") or call.data.startswith("awith_") or call.data.startswith("asell_"))
def admin_approvals(call):
    if call.from_user.id != ADMIN_ID: return
    parts = call.data.split("_")
    cat, action, doc_id = parts[0], parts[1], parts[2]
    
    if cat == "adep":
        doc_ref = db.collection('deposits').document(doc_id)
        if action == "app":
            doc_ref.update({'status': 'approved'})
            uid = doc_ref.get().to_dict()['user_id']
            # For simplicity assuming 100 deposit here. Admin can manual update via DB if dynamic amount needed.
            db.collection('users').document(uid).update({'balance_bdt': firestore.Increment(100)})
            bot.send_message(uid, "✅ Your deposit of 100 BDT is approved!")
            bot.edit_message_text("✅ Deposit Approved (100 BDT added)", ADMIN_ID, call.message.message_id)
        else:
            doc_ref.update({'status': 'rejected'})
            bot.edit_message_text("❌ Deposit Rejected", ADMIN_ID, call.message.message_id)

    elif cat == "asell":
        doc_ref = db.collection('pending_mails').document(doc_id)
        mail_data = doc_ref.get().to_dict()
        uid = mail_data['user_id']
        cfg = get_settings()
        
        if action == "app":
            doc_ref.update({'status': 'approved'})
            db.collection('users').document(uid).update({'balance_bdt': firestore.Increment(cfg['sell_price']), 'total_sold': firestore.Increment(1)})
            db.collection('stock_gmails').add({'email': mail_data['email'], 'password': mail_data['password'], 'status': 'unsold'})
            bot.send_message(uid, f"✅ Admin approved your Gmail `{mail_data['email']}`! {cfg['sell_price']} BDT added.", parse_mode="Markdown")
            bot.edit_message_text("✅ Sell Approved & Added to Stock", ADMIN_ID, call.message.message_id)
        else:
            doc_ref.update({'status': 'rejected'})
            bot.send_message(uid, f"❌ Admin rejected your Gmail `{mail_data['email']}`.", parse_mode="Markdown")
            bot.edit_message_text("❌ Sell Rejected", ADMIN_ID, call.message.message_id)
            
    elif cat == "awith":
        doc_ref = db.collection('withdraws').document(doc_id)
        uid = doc_ref.get().to_dict()['user_id']
        if action == "app":
            doc_ref.update({'status': 'paid'})
            bot.send_message(uid, "✅ Your withdraw request has been processed and paid!")
            bot.edit_message_text("✅ Marked as Paid", ADMIN_ID, call.message.message_id)
        else:
            doc_ref.update({'status': 'rejected'})
            bot.edit_message_text("❌ Withdraw Rejected", ADMIN_ID, call.message.message_id)

# ==========================================
# 10. Start Polling
# ==========================================
if __name__ == "__main__":
    print("🤖 Premium Gmail Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
