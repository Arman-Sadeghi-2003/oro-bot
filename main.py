import os
import sqlite3
import time
import logging
from flask import Flask, request
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler, InlineQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# تنظیم لاگ‌گذاری
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ایجاد اپلیکیشن Flask
app = Flask(__name__)

# تنظیمات اولیه
print("Fetching BOT_TOKEN from environment...")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please set it in Render Environment Variables.")

PRODUCT, SIZE, PHOTO, EDIT, DISCOUNT, CONTACT, SUPPORT, FAQ_STATE = range(8)
OPERATOR_ID = "6636775869"

DISCOUNT_CODES = {
    "oro1": "علی", "art2": "سارا", "fac3": "محمد", "nxt4": "نگار", "por5": "رضا",
    "skc6": "مهسا", "drw7": "بهزاد", "pix8": "لیلا", "cus9": "پویا", "orox": "شیما"
}

PRODUCTS = {
    "تابلو نخی چهره دلخواه": {"price": "۲,۱۰۰,۰۰۰ تا ۳,۲۰۰,۰۰۰ تومان"},
    "تابلو نخی کودکانه": {"price": "بزودی"},
    "تابلو نخی عاشقانه": {"price": "بزودی"}
}

SIZES = {
    "70×70": {"price": "۲,۴۵۰,۰۰۰ تومان"},
    "45×45": {"price": "بزودی"},
    "60×60": {"price": "بزودی"},
    "90×90": {"price": "بزودی"}
}

FAQ = {
    "مجموعه oro چیه؟": "یه گروه از جوون های باحال اردبیل که دارن از هنرشون استفاده میکنن. یه تیم خفن که عاشق کارشونه 😎",
    "به شهر منم ارسال میکنین؟": "فعلا فقط تو شهر اردبیلیم! 🏠 ولی داریم نقشه میکشیم و برنامه ریزی میکنیم تا به تمام نقاط ایران ارسال داشته باشیم. قول میدم خیلی زود با خبر میشی ⏰",
    "تابلو نخی چهره دلخواه چیه؟": "بچه های هنرمند مون چهره ت رو میگیرن و با ظرافت تبدیلش میکنن به یه تابلو نخی جذاب و بی نظیر. یه اثر هنری همراه با خاطره ش فقط برای تو 🎨❤️",
    "عکسم باید چه فرمتی باشه؟": "فقط میتونم عکس ساده تلگرام رو قبول کنم. بهتره که نسبت 1:1 باشه و چهره ت کامل بیوفته. اگر فرمت دیگه ای داری، بهتره با پشتیبانمون صحبت کنی 📲",
    "ادیت عکس چجوریه؟": "اگه عکست چیز اضافی داره یا مثلا یه تیکه عکست خراب شده یا هر چیز دیگه ای... فتوشاپ کارای ماهرمون انجام میدن برات. خیالت تخت 🖼️",
    "میتونم مشخصات سفارشم رو عوض کنم؟": "اگه فرآیند ثبت نام کامل شده، با پشتیبانی صحبت کن. وگرنه خیلی ساده رو این دکمه بزن و از اول شروع کن /start 🔄",
    "چقدر طول میکشه تا آماده بشه؟": "از وقتی که سفارشت رو اپراتور تایید کرد، حداکثر 3 روز بعد دستته. سریع و آسون ⚡",
    "میتونم چند تا تابلو سفارش بدم؟": "آره رفیق! 😍 هر چند تا که بخوای میشه. گزینه 'سفارش مجدد' رو بزن و دوباره سفارش بده. فقط حواست باشه که سفارشاتت رو تا انتها تکمیل کنی! 🛒"
}

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🛍️ محصولات", "❓ سوالات پرتکرار"],
        ["💬 ارتباط با پشتیبانی", "🎨 شروع دوباره"],
        ["ℹ️ درباره ما", "📷 اینستاگرام"]
    ],
    one_time_keyboard=False,
    resize_keyboard=True
)

ORDER_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🛍️ محصولات", "❓ سوالات پرتکرار"],
        ["💬 ارتباط با پشتیبانی", "🎨 شروع دوباره"],
        ["ℹ️ درباره ما", "📷 اینستاگرام"]
    ],
    one_time_keyboard=False,
    resize_keyboard=True
)

# دیتابیس برای سفارش‌های نیمه‌کاره
def init_db():
    conn = sqlite3.connect('pending_orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pending_orders
                 (user_id TEXT PRIMARY KEY, product TEXT, size TEXT, last_state TEXT, timestamp INTEGER, reminder_count INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def save_pending_order(user_id, product, size, last_state):
    conn = sqlite3.connect('pending_orders.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO pending_orders (user_id, product, size, last_state, timestamp, reminder_count) VALUES (?, ?, ?, ?, ?, 0)",
              (user_id, product, size, last_state, int(time.time())))
    conn.commit()
    conn.close()

def update_reminder_count(user_id, count):
    conn = sqlite3.connect('pending_orders.db')
    c = conn.cursor()
    c.execute("UPDATE pending_orders SET reminder_count = ? WHERE user_id = ?", (count, user_id))
    conn.commit()
    conn.close()

def remove_pending_order(user_id):
    conn = sqlite3.connect('pending_orders.db')
    c = conn.cursor()
    c.execute("DELETE FROM pending_orders WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_pending_orders():
    conn = sqlite3.connect('pending_orders.db')
    c = conn.cursor()
    c.execute("SELECT user_id, product, size, last_state, timestamp, reminder_count FROM pending_orders")
    orders = c.fetchall()
    conn.close()
    return orders

# تابع ارسال یادآوری پویا
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    current_time = int(time.time())
    pending_orders = get_pending_orders()
    for order in pending_orders:
        user_id, product, size, last_state, timestamp, reminder_count = order
        time_diff = current_time - timestamp

        # بعد از 1 ساعت: یادآوری ساده
        if reminder_count == 0 and time_diff >= 3600:  # 3600 ثانیه = 1 ساعت
            message = (
                f"سلام رفیق! 😊\n"
                f"دیدم سفارش {product} (سایز: {size or 'انتخاب نشده'}) رو نیمه‌کاره گذاشتی.\n"
                f"بیا سفارش رو کامل کن، منتظرتیم! ✨"
            )
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ادامه سفارش 📦", callback_data="resume_order")]
                    ])
                )
                update_reminder_count(user_id, 1)
            except Exception as e:
                logging.error(f"Error sending 1-hour reminder to {user_id}: {e}")

        # بعد از 1 روز: یادآوری با تخفیف 100 تومن
        elif reminder_count == 1 and time_diff >= 86400:  # 86400 ثانیه = 1 روز
            message = (
                f"سلام! ⏳\n"
                f"هنوز سفارش {product} (سایز: {size or 'انتخاب نشده'}) رو کامل نکردی.\n"
                f"اگه الان سفارش رو کامل کنی، 100 تومن تخفیف بیشتر می‌دی! 🎁\n"
                f"این تخفیف فقط تا 24 ساعت دیگه معتبره، پس عجله کن!"
            )
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ادامه سفارش 📦", callback_data="resume_order")]
                    ])
                )
                update_reminder_count(user_id, 2)
            except Exception as e:
                logging.error(f"Error sending 1-day reminder to {user_id}: {e}")

        # بعد از 2 روز: هشدار نهایی
        elif reminder_count == 2 and time_diff >= 172800:  # 172800 ثانیه = 2 روز
            message = (
                f"سلام! ⚠️\n"
                f"این آخرین یادآوریه برای سفارش {product} (سایز: {size or 'انتخاب نشده'}).\n"
                f"موجودی در حال اتمامه و اطلاعات سفارشت به‌زودی پاک می‌شه.\n"
                f"اگه الان سفارش رو کامل نکنی، باید مراحل رو از اول طی کنی! 😔\n"
                f"بیا همین الان تمومش کن!"
            )
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ادامه سفارش 📦", callback_data="resume_order")]
                    ])
                )
                # حذف سفارش بعد از هشدار نهایی
                remove_pending_order(user_id)
            except Exception as e:
                logging.error(f"Error sending 2-day reminder to {user_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"Received /start command from user: {update.message.from_user.id}")
    context.user_data.clear()
    await update.message.reply_text("سلام! 😊 به oro خوش اومدی")
    await update.message.reply_text(
        "بیا یه نگاهی به محصولاتمون بنداز 👀",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")],
            [
                InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
            ]
        ])
    )
    return PRODUCT

async def inlinequery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"Received inline query: {update.inline_query.query}")
    query = update.inline_query.query.lower()
    results = []

    if query in ["", "محصولات"]:
        for product, info in PRODUCTS.items():
            results.append(
                InlineQueryResultArticle(
                    id=product,
                    title=product,
                    description=f"💰 رنج قیمت: {info['price']}",
                    input_message_content=InputTextMessageContent(f"{product}")
                )
            )
    elif query == "سایز":
        for size, info in SIZES.items():
            results.append(
                InlineQueryResultArticle(
                    id=size,
                    title=size,
                    description=f"💰 رنج قیمت: {info['price']}",
                    input_message_content=InputTextMessageContent(f"{size}")
                )
            )
    elif query in ["سوالات", "سوال"]:
        for question in FAQ.keys():
            results.append(
                InlineQueryResultArticle(
                    id=question,
                    title=question,
                    description="❓ یه سوال پرتکرار",
                    input_message_content=InputTextMessageContent(f"{question}")
                )
            )

    await update.inline_query.answer(results)

async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"Handling product selection: {update.message.text}")
    message_text = update.message.text
    if message_text in FAQ:
        await update.message.reply_text(FAQ[message_text])
        return PRODUCT
    if message_text not in PRODUCTS:
        await update.message.reply_text("لطفاً یه محصول از منو انتخاب کن! 😊")
        return PRODUCT

    selected_product = message_text
    product_price = PRODUCTS[selected_product]["price"]

    if product_price == "بزودی":
        await update.message.reply_text(
            "متأسفیم، این محصول هنوز آماده نیست! 😔\n"
            "یه محصول دیگه انتخاب کن یا با پشتیبانی حرف بزن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")],
                [
                    InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                    InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
                ]
            ])
        )
        return PRODUCT

    context.user_data['product'] = selected_product
    user_id = str(update.message.from_user.id)
    save_pending_order(user_id, selected_product, None, "PRODUCT")

    await update.message.reply_text(
        f"{selected_product} انتخاب شد! حالا یه سایز انتخاب کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("انتخاب سایز 📏", switch_inline_query_current_chat="سایز")]
        ])
    )
    return SIZE

async def handle_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"Handling size selection: {update.message.text}")
    message_text = update.message.text
    if message_text not in SIZES:
        await update.message.reply_text("لطفاً یه سایز از منو انتخاب کن! 😊")
        return SIZE

    selected_size = message_text
    size_price = SIZES[selected_size]["price"]

    if size_price == "بزودی":
        await update.message.reply_text(
            "متأسفیم، این سایز هنوز آماده نیست! 😔\n"
            "یه سایز دیگه انتخاب کن یا با پشتیبانی حرف بزن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("انتخاب سایز 📐", switch_inline_query_current_chat="سایز")],
                [
                    InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                    InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
                ]
            ])
        )
        return SIZE

    context.user_data['size'] = selected_size
    context.user_data['username'] = update.message.from_user.username
    context.user_data['user_id'] = update.message.from_user.id
    save_pending_order(str(context.user_data['user_id']), context.user_data['product'], selected_size, "SIZE")

    await update.message.reply_text(
        f"عالیه. 👏\nانتخابت حرف نداره ✨\nپس انتخابت شد: {context.user_data['product']} {selected_size}"
    )
    await update.message.reply_text(
        "یه نکته بگم: ℹ️\nفعلا مجموعه oro فقط در شهر اردبیل فعالیت میکنه 🏙️\nاما داریم برنامه ریزی میکنیم که به زودی همه جا باشیم. 🚀",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ متوجه شدم", callback_data="understood")]])
    )
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Entering photo state...")
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "حله رفیق! حالا وقتشه بترکونیم 💥\n"
            "عکسی که دوست داری به این تابلو نخی تبدیل بشه رو برامون بفرست 📸\n"
            "اگه نسبت 1:1 باشه، نتیجه بهتر میشه! 👍",
            reply_markup=None
        )
        await query.message.reply_text(
            "عکست رو بفرست!",
            reply_markup=ORDER_KEYBOARD
        )
        return PHOTO

    if not update.message.photo:
        await update.message.reply_text(
            "متاسفم. 😔 من نمیتونم فایل دریافت کنم. یه عکس ساده بفرست 📸\n"
            "از همین پایین 📎 رو بزن و انتخاب کن!",
            reply_markup=ORDER_KEYBOARD
        )
        return PHOTO

    context.user_data['photo'] = update.message.photo[-1].file_id
    save_pending_order(str(context.user_data['user_id']), context.user_data['product'], context.user_data['size'], "PHOTO")

    await update.message.reply_text(
        "عجب عکس باحالی! 😍\nنیاز به ادیت داره؟ ✂️\nیعنی میخوای چیزی توش عوض کنی؟\n"
        "فتوشاپ کارای ماهری داریم. رایگان هم انجام میدن. 🖌️",
        reply_markup=ReplyKeyboardMarkup([["بله", "خیر"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return EDIT

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"Handling edit selection: {update.message.text}")
    context.user_data['edit'] = update.message.text
    if context.user_data['edit'] not in ["بله", "خیر"]:
        await update.message.reply_text("لطفاً فقط 'بله' یا 'خیر' رو بگو! 😊")
        return EDIT

    if context.user_data['edit'] == "خیر":
        await update.message.reply_text("باشه! ✅")
    else:
        await update.message.reply_text("حله! فتوشاپ‌کارامون زودی دست به کار می‌شن! ✂️")

    save_pending_order(str(context.user_data['user_id']), context.user_data['product'], context.user_data['size'], "EDIT")

    await update.message.reply_text(
        "کد تخفیف داری؟ 🎁\nهمینجا برامون بنویس، وگرنه دکمه زیر رو بزن:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 کد تخفیف ندارم", callback_data="no_discount")]])
    )
    return DISCOUNT

async def discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Entering discount state...")
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "no_discount":
            context.user_data['discount'] = "ندارد"
            marketer = ""
    else:
        discount_code = update.message.text.lower()
        if discount_code in DISCOUNT_CODES:
            context.user_data['discount'] = discount_code
            await update.message.reply_text("درسته. کد تخفیفت اعمال شد ✅")
            marketer = f" (بازاریاب: {DISCOUNT_CODES[discount_code]})"
        else:
            await update.message.reply_text(
                "این کد تخفیف درست نیست! ❌\nیه کد ۴ حرفی درست بزن یا 'کد تخفیف ندارم' رو انتخاب کن! 😜"
            )
            return DISCOUNT

    save_pending_order(str(context.user_data['user_id']), context.user_data['product'], context.user_data['size'], "DISCOUNT")

    # چک کردن تخفیف یادآوری
    user_id = str(context.user_data['user_id'])
    conn = sqlite3.connect('pending_orders.db')
    c = conn.cursor()
    c.execute("SELECT reminder_count, timestamp FROM pending_orders WHERE user_id = ?", (user_id,))
    order = c.fetchone()
    conn.close()

    extra_discount = 0
    if order:
        reminder_count, timestamp = order
        time_diff = int(time.time()) - timestamp
        if reminder_count >= 1 and time_diff >= 86400 and time_diff <= 172800:  # بین 1 تا 2 روز
            extra_discount = 100
            context.user_data['extra_discount'] = extra_discount
            await (update.callback_query.message if update.callback_query else update.message).reply_text(
                f"تبریک! 🎉 چون سفارش رو به موقع کامل کردی، 100 تومن تخفیف اضافی گرفتی!"
            )

    if not context.user_data.get('username'):
        await (update.callback_query.message if update.callback_query else update.message).reply_text(
            "برای اینکه بتونیم باهاتون تماس بگیریم، لطفاً شماره تلفنتون رو به اشتراک بذارید 📞\n"
            "کافیه دکمه زیر رو بزنید:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("ارسال شماره تلفن 📱", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return CONTACT

    await (update.callback_query.message if update.callback_query else update.message).reply_text(
        "سفارشت ثبت شد. 🎉\nمنتظر پیاممون باش. زودی باهات تماس میگیریم و هماهنگ میشیم! 📞\n"
        "مرسی که با oro همراه شدی. 🙏",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")],
            [
                InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
            ]
        ])
    )

    await (update.callback_query.message if update.callback_query else update.message).reply_text(
        "راستی اینم پیج اینستامونه. به دوستات هم معرفی کن 📷\nhttps://instagram.com/example"
    )

    marketer = f" (بازاریاب: {DISCOUNT_CODES[context.user_data['discount']]})" if context.user_data['discount'] in DISCOUNT_CODES else ""
    extra_discount_info = f"\n- تخفیف اضافی: {extra_discount} تومن" if extra_discount > 0 else ""
    message_to_operator = (
        "سفارش جدید:\n"
        f"- محصول: {context.user_data['product']}\n"
        f"- ابعاد: {context.user_data['size']}\n"
        f"- آیدی: @{context.user_data['username']}\n"
        f"- ادیت عکس: {context.user_data['edit']}\n"
        f"- کد تخفیف: {context.user_data['discount']}{marketer}"
        f"{extra_discount_info}"
    )
    try:
        await context.bot.send_message(chat_id=OPERATOR_ID, text=message_to_operator)
        await context.bot.send_photo(chat_id=OPERATOR_ID, photo=context.user_data['photo'])
    except Exception as e:
        await context.bot.send_message(chat_id=OPERATOR_ID, text=f"خطا در ارسال به اپراتور: {e}")

    remove_pending_order(str(context.user_data['user_id']))
    context.user_data.clear()
    return ConversationHandler.END

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Entering contact state...")
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        context.user_data['contact'] = phone_number

        await update.message.reply_text(
            "ممنون که شماره‌ت رو به اشتراک گذاشتی! 🙏",
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text(
            "سفارشت ثبت شد. 🎉\nمنتظر پیاممون باش. زودی باهات تماس میگیریم و هماهنگ میشیم! 📞\n"
            "مرسی که با oro همراه شدی. 🙏",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")],
                [
                    InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                    InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
                ]
            ])
        )

        await update.message.reply_text(
            "راستی اینم پیج اینستامونه. به دوستات هم معرفی کن 📷\nhttps://instagram.com/example"
        )

        marketer = f" (بازاریاب: {DISCOUNT_CODES[context.user_data['discount']]})" if context.user_data['discount'] in DISCOUNT_CODES else ""
        extra_discount = context.user_data.get('extra_discount', 0)
        extra_discount_info = f"\n- تخفیف اضافی: {extra_discount} تومن" if extra_discount > 0 else ""
        message_to_operator = (
            "سفارش جدید:\n"
            f"- محصول: {context.user_data['product']}\n"
            f"- ابعاد: {context.user_data['size']}\n"
            f"- شماره تماس: {context.user_data['contact']}\n"
            f"- ادیت عکس: {context.user_data['edit']}\n"
            f"- کد تخفیف: {context.user_data['discount']}{marketer}"
            f"{extra_discount_info}"
        )
        try:
            await context.bot.send_message(chat_id=OPERATOR_ID, text=message_to_operator)
            await context.bot.send_photo(chat_id=OPERATOR_ID, photo=context.user_data['photo'])
        except Exception as e:
            await context.bot.send_message(chat_id=OPERATOR_ID, text=f"خطا در ارسال به اپراتور: {e}")

        remove_pending_order(str(context.user_data['user_id']))
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "لطفاً فقط دکمه 'ارسال شماره تلفن 📱' رو بزن تا شماره‌ت رو به اشتراک بذاری! 😊",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("ارسال شماره تلفن 📱", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return CONTACT

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Entering support state...")
    if update.callback_query:
        query = update.callback_query
        logging.info(f"Support called via callback query with data: {query.data}")
        await query.answer()
    else:
        logging.info("Support called via keyboard button")
    context.user_data['support_message'] = ""
    await (update.callback_query.message if update.callback_query else update.message).reply_text(
        "سلام رفیق! 😊 مشکلی داری؟ سوالی داری؟ هر چی هست برامون بنویس! 📩\nپشتیبانای خفنمون زودی جوابت رو می‌دن! 💪",
        reply_markup=MAIN_KEYBOARD
    )
    return SUPPORT

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Handling support message...")
    if update.callback_query:
        query = update.callback_query
        logging.info(f"Callback query received with data: {query.data}")
        await query.answer()
        if query.data == "send_to_operator":
            logging.info("Sending message to operator...")
            username = query.from_user.username
            user_id = query.from_user.id
            contact_info = f"آیدی: @{username}" if username else f"لینک چت: https://t.me/+{user_id}"
            message_to_operator = (
                "پیام پشتیبانی جدید:\n"
                f"- {contact_info}\n"
                f"- متن: {context.user_data['support_message']}"
            )
            await context.bot.send_message(chat_id=OPERATOR_ID, text=message_to_operator)
            await query.message.reply_text(
                "پیامت رسید رفیق! 🙌 زودی باهات تماس می‌کنیم. دمت گرم که صبور هستی! 😎",
                reply_markup=MAIN_KEYBOARD
            )
            context.user_data.clear()
            return ConversationHandler.END
    else:
        logging.info(f"Support message received: {update.message.text}")

    new_message = update.message.text
    if context.user_data['support_message']:
        context.user_data['support_message'] += f"\n{new_message}"
    else:
        context.user_data['support_message'] = new_message

    await update.message.reply_text(
        f"مشکلی که نوشتی:\n{context.user_data['support_message']}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال به اپراتور", callback_data="send_to_operator")]])
    )
    return SUPPORT

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Entering FAQ state...")
    await update.message.reply_text(
        "سوالتو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("سوالات ❓", switch_inline_query_current_chat="سوالات")]
        ])
    )
    return FAQ_STATE

async def handle_faq_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"Handling FAQ selection: {update.message.text}")
    message_text = update.message.text
    if message_text not in FAQ:
        await update.message.reply_text("لطفاً یه سوال درست انتخاب کن رفیق! 😜")
        return FAQ_STATE

    await update.message.reply_text(FAQ[message_text])
    return ConversationHandler.END

async def faq_during_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("FAQ during order state...")
    await update.message.reply_text(
        "لطفاً مراحل ثبت سفارش رو کامل کن یا 'شروع دوباره' رو بزن! 😊",
        reply_markup=ORDER_KEYBOARD
    )
    return None

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Restarting conversation...")
    return await start(update, context)

async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Handling about_us command...")
    await update.message.reply_text(
        "ما یه تیم جوون و خلاق از اردبیل هستیم که عاشق هنر و خلاقیتیم! 🎨\n"
        "با تابلوهای نخی دست‌سازمون، خاطراتت رو به یه اثر هنری تبدیل می‌کنیم. ❤️",
        reply_markup=MAIN_KEYBOARD
    )

async def instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Handling instagram command...")
    await update.message.reply_text(
        "اینم پیج اینستامون! 📷\nhttps://instagram.com/example\n"
        "حتماً فالو کن و به دوستات معرفی کن! 😊",
        reply_markup=MAIN_KEYBOARD
    )

async def resume_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Resuming order...")
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    conn = sqlite3.connect('pending_orders.db')
    c = conn.cursor()
    c.execute("SELECT product, size, last_state FROM pending_orders WHERE user_id = ?", (user_id,))
    order = c.fetchone()
    conn.close()

    if not order:
        await query.message.reply_text(
            "متأسفم، سفارش نیمه‌کاره‌ای پیدا نشد. 😔\nبیا از اول شروع کنیم:",
            reply_markup=MAIN_KEYBOARD
        )
        return await start(update, context)

    product, size, last_state = order
    context.user_data['product'] = product
    context.user_data['size'] = size
    context.user_data['user_id'] = user_id
    context.user_data['username'] = query.from_user.username

    if last_state == "PRODUCT":
        await query.message.reply_text(
            f"آخرین بار محصول {product} رو انتخاب کرده بودی. حالا یه سایز انتخاب کن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("انتخاب سایز 📏", switch_inline_query_current_chat="سایز")]
            ])
        )
        return SIZE
    elif last_state == "SIZE":
        await query.message.reply_text(
            f"عالیه. 👏\nانتخابت حرف نداره ✨\nپس انتخابت شد: {product} {size}\n"
            "یه نکته بگم: ℹ️\nفعلا مجموعه oro فقط در شهر اردبیل فعالیت میکنه 🏙️\nاما داریم برنامه ریزی میکنیم که به زودی همه جا باشیم. 🚀",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ متوجه شدم", callback_data="understood")]])
        )
        return PHOTO
    elif last_state == "PHOTO":
        await query.message.reply_text(
            "آخرین بار به این مرحله رسیدی. عکست رو بفرست! 📸\n"
            "اگه نسبت 1:1 باشه، نتیجه بهتر میشه! 👍",
            reply_markup=ORDER_KEYBOARD
        )
        return PHOTO
    elif last_state == "EDIT":
        await query.message.reply_text(
            "آخرین بار به این مرحله رسیدی. نیاز به ادیت داره؟ ✂️\n"
            "فتوشاپ کارای ماهری داریم. رایگان هم انجام میدن. 🖌️",
            reply_markup=ReplyKeyboardMarkup([["بله", "خیر"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return EDIT
    elif last_state == "DISCOUNT":
        await query.message.reply_text(
            "آخرین بار به این مرحله رسیدی. کد تخفیف داری؟ 🎁\n"
            "همینجا برامون بنویس، وگرنه دکمه زیر رو بزن:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 کد تخفیف ندارم", callback_data="no_discount")]])
        )
        return DISCOUNT
    else:
        return await start(update, context)

# تعریف اپلیکیشن تلگرام به صورت گلوبال
application = None

# تعریف endpoint برای Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK', 200

# یه endpoint ساده برای تست سرور
@app.route('/')
def health_check():
    return "Bot is running!", 200

def main():
    global application
    print("Building Telegram application...")
    application = Application.builder().token(BOT_TOKEN).build()

    # مقداردهی اولیه دیتابیس
    init_db()

    # اضافه کردن هندلرها
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^🎨 شروع دوباره$'), restart),
            MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
            MessageHandler(filters.Regex('^🛍️ محصولات$'), start),
            MessageHandler(filters.Regex('^❓ سوالات پرتکرار$'), faq),
            MessageHandler(filters.Regex('^ℹ️ درباره ما$'), about_us),
            MessageHandler(filters.Regex('^📷 اینستاگرام$'), instagram),
            CallbackQueryHandler(support, pattern="^support$"),
            CallbackQueryHandler(resume_order, pattern="^resume_order$"),
        ],
        states={
            PRODUCT: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(support, pattern="^support$"),
                MessageHandler(filters.Text() & ~filters.Command(), handle_product_selection)
            ],
            SIZE: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                MessageHandler(filters.Text() & ~filters.Command(), handle_size_selection)
            ],
            PHOTO: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(photo, pattern="^understood$"),
                MessageHandler(filters.ALL & ~filters.Command(), photo)
            ],
            EDIT: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                MessageHandler(filters.Regex('^(بله|خیر)$'), edit)
            ],
            DISCOUNT: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(discount, pattern="^no_discount$"),
                MessageHandler(filters.Text() & ~filters.Command(), discount)
            ],
            CONTACT: [
                MessageHandler(filters.CONTACT, contact),
                MessageHandler(filters.ALL & ~filters.Command(), contact)
            ],
            SUPPORT: [
                CallbackQueryHandler(handle_support, pattern="^send_to_operator$"),
                MessageHandler(filters.Text() & ~filters.Command(), handle_support)
            ],
            FAQ_STATE: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                MessageHandler(filters.Text() & ~filters.Command(), handle_faq_selection)
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^🎨 شروع دوباره$'), restart),
            MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support)
        ],
        per_chat=True,
        per_user=True,
        per_message=False
    )
    print("Adding handlers to application...")
    application.add_handler(conv_handler)
    application.add_handler(InlineQueryHandler(inlinequery))

    # تنظیم زمان‌بندی برای ارسال یادآوری
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminder, 'interval', minutes=30, args=[application])
    scheduler.start()

    print("Setting up webhook...")
    webhook_url = "https://orobot.onrender.com/webhook"  # آدرس سرورت رو اینجا بذار
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),  # پورت از متغیر محیطی گرفته می‌شه
        url_path="/webhook",
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    print("Starting main function...")
    main()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8443)))
