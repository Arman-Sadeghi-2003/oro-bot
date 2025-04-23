import os
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler, InlineQueryHandler
import asyncio
import telegram.error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Fetching BOT_TOKEN from environment...")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please set it in Railway Environment Variables.")

PRODUCT, SIZE, PHOTO, EDIT, DISCOUNT, CONTACT, SUPPORT, FAQ_STATE = range(8)
OPERATOR_ID = "7695028053"

DISCOUNT_CODES = {
    "oro1": "مهدی", "art2": "مبین", "fac3": "محمد", "nxt4": "مریم", "por5": "نگین",
    "skc6": "مهشید", "drw7": "آیدا", "pix8": "حسین", "cus9": "پویا", "orox": "عرفان"
}

PRODUCTS = {
    "تابلو نخی پرتره (دایره)": {"price": "تومان۲,۱۰۰,۰۰۰ تا ۳,۴۰۰,۰۰۰",
    "thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_14.jpg"
    },
    "تابلو نخی پرتره (مربع)": {"price": "بزودی",
"thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_13.jpg"
},
    "تابلو نخی شبتاب": {"price": "بزودی",
"thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_13.jpg"
},
    "تابلو نخی ماندالا": {"price": "بزودی",
"thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_13.jpg"
}
}

SIZES = {
    "70×70": {"price": 2490000,
    "thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_11.jpg"
    },
    "45×45": {"price": "بزودی",
"thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_13.jpg"
},
    "60×60": {"price": "بزودی",
"thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_13.jpg"
},
    "90×90": {"price": "بزودی",
"thumbnail": "https://api.telegram.org/file/bot8086798709:AAETrPfHPj_aVM80QL_uL1LYg8cRMcSoRR0/photos/file_13.jpg"
}
}

FAQ = {
    "مجموعه oro چیه؟": "یه گروه از جوون های باحال اردبیل که دارن از هنرشون استفاده میکنن. یه تیم خفن که عاشق کارشونه 😎",
    "به شهر منم ارسال میکنین؟": "فعلا فقط تو شهر اردبیلیم! 🏠 ولی داریم نقشه میکشیم و برنامه ریزی میکنیم تا به تمام نقاط ایران ارسال داشته باشیم. قول میدم خیلی زود با خبر میشی ⏰",
    "تابلو نخی پرتره (دایره) چیه؟": "بچه های هنرمند مون چهره ت رو میگیرن و با ظرافت تبدیلش میکنن به یه تابلو نخی جذاب و بی نظیر. یه اثر هنری همراه با خاطره ش فقط برای تو 🎨❤️",
    "عکسم باید چه فرمتی باشه؟": "فقط میتونم عکس ساده تلگرام رو قبول کنم. بهتره که نسبت 1:1 باشه و چهره ت کامل بیوفته. اگر فرمت دیگه ای داری، بهتره با پشتیبانمون صحبت کنی 📲",
    "ادیت عکس چجوریه؟": "اگه عکست چیز اضافی داره یا مثلا یه تیکه عکست خراب شده یا هر چیز دیگه ای... فتوشاپ کارای ماهرمون انجام میدن برات. خیالت تخت 🖼️",
    "میتونم مشخصات سفارشم رو عوض کنم؟": "اگه فرآیند ثبت نام کامل شده، با پشتیبانی صحبت کن. وگرنه خیلی ساده رو این دکمه بزن و از اول شروع کن /start 🔄",
    "چقدر طول میکشه تا آماده بشه؟": "از وقتی که سفارشت رو اپراتور تایید کرد، حداکثر 3 روز بعد دستته. سریع و آسون ⚡",
    "میتونم چند تا تابلو سفارش بدم؟": "آره رفیق! 😍 هر چند تا که بخوای میشه. گزینه 'سفارش مجدد' رو بزن و دوباره سفارش بده. فقط حواست باشه که سفارشاتت رو تا انتها تکمیل کنی! 🛒"
}

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["🎨 شروع دوباره", "💬 ارتباط با پشتیبانی"]],
    one_time_keyboard=False,
    resize_keyboard=True
)

ORDER_KEYBOARD = ReplyKeyboardMarkup(
    [["🎨 شروع دوباره", "💬 ارتباط با پشتیبانی"]],
    one_time_keyboard=False,
    resize_keyboard=True
)

DATABASE_PATH = "reminders.db"
running = True

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reminders
                 (user_id INTEGER, chat_id INTEGER, reminder_type TEXT, remind_at TEXT)''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def add_reminder(user_id, chat_id, reminder_type, remind_at):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO reminders (user_id, chat_id, reminder_type, remind_at) VALUES (?, ?, ?, ?)",
              (user_id, chat_id, reminder_type, remind_at))
    conn.commit()
    conn.close()
    logger.info(f"Added reminder for user_id: {user_id}, type: {reminder_type}, at: {remind_at}")

def remove_reminders(user_id):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    logger.info(f"Removed all reminders for user_id: {user_id}")

def reminder_loop(application):
    logger.info("Starting reminder loop...")
    while running:
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("SELECT user_id, chat_id, reminder_type FROM reminders WHERE remind_at <= ?", (current_time,))
            reminders = c.fetchall()
            
            for user_id, chat_id, reminder_type in reminders:
                logger.info(f"Sending reminder for user_id: {user_id}, chat_id: {chat_id}, type: {reminder_type}")
                try:
                    if reminder_type == "1hour":
                        message = (
                            f"سلام دوست خوبم! 🌟\n"
                            f"ما هنوز منتظریم تا سفارشت رو کامل کنی.\n"
                            f"بیا ادامه بدیم و یه تابلو نخی فوق‌العاده برات بسازیم! 🎨\n\n"
                            f"راستی، یادت رفته عکست رو بفرستی!"
                        )
                    elif reminder_type == "1day":
                        message = (
                            f"سلام رفیق عزیز! ✨\n"
                            f"یه روزه که oro منتظرته!\n"
                            f"اگه تا آخر امروز سفارشت رو تکمیل کنی، ۱۰۰,۰۰۰ تومن تخفیف بیشتر می‌گیرید! 🎁\n"
                            f"بیا تمومش کنیم! 💪\n\n"
                            f"راستی، یادت رفته عکست رو بفرستی!"
                        )
                    elif reminder_type == "3days":
                        message = (
                            f"سلام دوست عزیز! ⚠️\n"
                            f"موجودی تابلو نخی پرتره (دایره) رو به اتمامه و ممکنه اطلاعات سفارشت پاک بشه!\n"
                            f"تا دیر نشده، همین امروز سفارشت رو کامل کن تا خیالت راحت بشه. 🖼️\n\n"
                            f"راستی، یادت رفته عکست رو بفرستی!"
                        )

                    async def send_message():
                        await application.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("ادامه سفارش 🚀", callback_data="resume_order")]
                            ])
                        )
                    
                    asyncio.run_coroutine_threadsafe(send_message(), application.loop)
                    logger.info(f"Reminder {reminder_type} sent successfully to chat_id: {chat_id}")

                    c.execute("DELETE FROM reminders WHERE user_id = ? AND reminder_type = ?", (user_id, reminder_type))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error sending reminder to chat_id {chat_id}: {e}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error in reminder loop: {e}")
        
        time.sleep(60)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Received /start command from user: {update.message.from_user.id}")
    context.user_data.clear()
    context.user_data['current_state'] = PRODUCT
    await update.message.reply_text("سلام! 😊 به oro خوش اومدی")
    await update.message.reply_text(
        "🌟بیا نگاهی به محصولاتمون بنداز👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")],
            [
                InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
            ],
            [
                InlineKeyboardButton("📖 درباره ما", callback_data="about_us"),
                InlineKeyboardButton("📷 اینستاگرام", url="https://instagram.com/oro.stringart")
            ]
        ])
    )
    return PRODUCT

async def inlinequery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Received inline query: {update.inline_query.query}")
    query = update.inline_query.query.lower()
    results = []

    if query in ["", "محصولات"]:
        for product, info in PRODUCTS.items():
            results.append(
                InlineQueryResultArticle(
                    id=product,
                    title=product,
                    description=f"💰 رنج قیمت: {info['price']}",
                    input_message_content=InputTextMessageContent(f"{product}"),
                    thumb_url=info['thumbnail'],
                    thumb_width=150,
                    thumb_height=150
                )
            )
    elif query == "سایز":
        for size, info in SIZES.items():
            price = info['price']
            price_display = price if isinstance(price, str) else f"{price:,} تومان".replace(',', '،')
            results.append(
                InlineQueryResultArticle(
                    id=size,
                    title=size,
                    description=f"💰 قیمت: {price_display}",
                    input_message_content=InputTextMessageContent(f"{size}"),
                    thumb_url=info['thumbnail'],  # اضافه کردن تصویر برای سایزها
                    thumb_width=150,
                    thumb_height=150
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
    else:
        results.append(
            InlineQueryResultArticle(
                id="no_results",
                title="نتیجه‌ای یافت نشد",
                description="لطفاً محصولات یا سوالات رو انتخاب کنید.",
                input_message_content=InputTextMessageContent("نتیجه‌ای یافت نشد")
            )
        )

    await update.inline_query.answer(results)

async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Handling product selection: {update.message.text}")
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
    context.user_data['current_state'] = SIZE

    await update.message.reply_text(
        f"{selected_product} انتخاب شد! حالا یه سایز انتخاب کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("انتخاب سایز 📏", switch_inline_query_current_chat="سایز")]
        ])
    )
    return SIZE

async def handle_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Handling size selection: {update.message.text}")
    message_text = update.message.text
    if message_text not in SIZES:
        await update.message.reply_text("لطفاً یه سایز از منو انتخاب کن! 😊")
        return SIZE

    selected_size = message_text
    size_price = SIZES[selected_size]["price"]

    if isinstance(size_price, str) and size_price == "بزودی":
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
    context.user_data['extra_discount_eligible'] = False
    context.user_data['current_state'] = PHOTO

    user_id = context.user_data['user_id']
    chat_id = update.message.chat_id

    current_time = datetime.now()
    add_reminder(user_id, chat_id, "1hour", (current_time + timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S"))
    add_reminder(user_id, chat_id, "1day", (current_time + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"))
    add_reminder(user_id, chat_id, "3days", (current_time + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"))

    await update.message.reply_text(
        f"عالیه. 👏\nانتخابت حرف نداره ✨\nپس انتخابت شد: {context.user_data['product']} {selected_size}"
    )
    await update.message.reply_text(
        "یه نکته بگم: ℹ️\nفعلا مجموعه oro فقط در شهر اردبیل فعالیت میکنه 🏙️\nاما داریم برنامه ریزی میکنیم که به زودی همه جا باشیم. 🚀",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ متوجه شدم", callback_data="understood")]])
    )
    return PHOTO

async def resume_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if not context.user_data:
        await query.message.reply_text(
            "به نظر می‌رسه سفارشت پاک شده! 😔 بیا از اول شروع کنیم:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")]
            ])
        )
        return PRODUCT
    elif 'product' not in context.user_data:
        await query.message.reply_text(
            "بیا از اول شروع کنیم! 😊",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")]
            ])
        )
        return PRODUCT
    elif 'size' not in context.user_data:
        await query.message.reply_text(
            "یه سایز انتخاب کن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("انتخاب سایز 📏", switch_inline_query_current_chat="سایز")]
            ])
        )
        return SIZE
    elif 'photo' not in context.user_data:
        await query.message.reply_text(
            "عکست رو بفرست! 📸",
            reply_markup=ORDER_KEYBOARD
        )
        return PHOTO
    elif 'edit' not in context.user_data:
        await query.message.reply_text(
            "نیاز به ادیت داره؟ ✂️",
            reply_markup=ReplyKeyboardMarkup([["بله", "خیر"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return EDIT
    elif 'discount' not in context.user_data:
        await query.message.reply_text(
            "کد تخفیف داری؟ 🎁\nهمینجا برامون بنویس، وگرنه دکمه زیر رو بزن:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 کد تخفیف ندارم", callback_data="no_discount")]])
        )
        return DISCOUNT
    elif 'contact' not in context.user_data and not context.user_data.get('username'):
        await query.message.reply_text(
            "لطفاً شماره تلفنتون رو به اشتراک بذارید 📞",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("ارسال شماره تلفن 📱", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return CONTACT
    else:
        await query.message.reply_text(
            "سفارشت تقریباً آماده‌ست! 😊 با پشتیبانی تماس بگیر یا دوباره شروع کن:",
            reply_markup=MAIN_KEYBOARD
        )
        return ConversationHandler.END

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Entering photo state...")
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
    context.user_data['current_state'] = EDIT

    await update.message.reply_text(
        "عجب عکس باحالی! 😍\nنیاز به ادیت داره؟ ✂️\nیعنی میخوای چیزی توش عوض کنی؟\n"
        "فتوشاپ کارای ماهری داریم. رایگان هم انجام میدن. 🖌️",
        reply_markup=ReplyKeyboardMarkup([["بله", "خیر"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return EDIT

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Handling edit selection: {update.message.text}")
    context.user_data['edit'] = update.message.text
    if context.user_data['edit'] not in ["بله", "خیر"]:
        await update.message.reply_text("لطفاً فقط 'بله' یا 'خیر' رو بگو! 😊")
        return EDIT

    if context.user_data['edit'] == "خیر":
        await update.message.reply_text("باشه! ✅")
    else:
        await update.message.reply_text("حله! فتوشاپ‌کارامون زودی دست به کار می‌شن! ✂️")

    context.user_data['current_state'] = DISCOUNT

    await update.message.reply_text(
        "کد تخفیف داری؟ 🎁\nهمینجا برامون بنویس، وگرنه دکمه زیر رو بزن:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 کد تخفیف ندارم", callback_data="no_discount")]])
    )
    return DISCOUNT

async def discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Entering discount state...")
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
            await update.message.reply_text("یه لحظه صبر کن بررسی کنم... ⏳")
            await asyncio.sleep(4)
            await update.message.reply_text("درسته. کد تخفیفت اعمال شد ✅")
            marketer = f" (بازاریاب: {DISCOUNT_CODES[discount_code]})"
        else:
            await update.message.reply_text(
                "این کد تخفیف درست نیست! ❌\nیه کد ۴ حرفی درست بزن یا 'کد تخفیف ندارم' رو انتخاب کن! 😜"
            )
            return DISCOUNT

    user_id = context.user_data['user_id']
    context.user_data['order_completed'] = True
    remove_reminders(user_id)

    base_price = SIZES[context.user_data['size']]['price']
    discount_amount = 240000 if context.user_data['discount'] in DISCOUNT_CODES else 0
    extra_discount = 100000 if context.user_data.get('extra_discount_eligible', False) else 0
    final_price = base_price - discount_amount - extra_discount
    final_price_str = f"{final_price:,} تومان".replace(',', '،')

    summary = (
        "خلاصه سفارشت:\n"
        f"- محصول: {context.user_data['product']}\n"
        f"- ابعاد: {context.user_data['size']}\n"
        f"- ادیت عکس: {context.user_data['edit']}\n"
        f"- کد تخفیف: {context.user_data['discount']}{marketer}\n"
        f"- قیمت نهایی: {final_price_str}\n\n"
        "آیا مطمئنی که می‌خوای سفارش رو ثبت کنی؟"
    )
    await (update.callback_query.message if update.callback_query else update.message).reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تأیید سفارش", callback_data="confirm_order")]
        ])
    )
    return DISCOUNT

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = context.user_data['user_id']
    marketer = f" (بازاریاب: {DISCOUNT_CODES[context.user_data['discount']]})" if context.user_data['discount'] in DISCOUNT_CODES else ""
    base_price = SIZES[context.user_data['size']]['price']
    discount_amount = 240000 if context.user_data['discount'] in DISCOUNT_CODES else 0
    extra_discount = 100000 if context.user_data.get('extra_discount_eligible', False) else 0
    final_price = base_price - discount_amount - extra_discount
    final_price_str = f"{final_price:,} تومان".replace(',', '،')

    if not context.user_data.get('username'):
        context.user_data['current_state'] = CONTACT
        await query.message.reply_text(
            "لطفاً شماره تلفنتون رو به اشتراک بذارید 📞",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("ارسال شماره تلفن 📱", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return CONTACT

    extra_discount_message = " و به‌خاطر تکمیل سریع سفارش، ۱۰۰,۰۰۰ تومن تخفیف بیشتر برات اعمال شد! 🎉" if extra_discount else ""
    await query.message.reply_text(
        f"سفارشت ثبت شد. 🎉\nمنتظر پیاممون باش. زودی باهات تماس می‌گیریم و هماهنگ می‌شیم! 📞\n"
        f"مرسی که با oro همراه شدی. 🙏{extra_discount_message}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 ثبت سفارش دیگر", switch_inline_query_current_chat="محصولات")],
            [
                InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support"),
                InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات")
            ]
        ])
    )

    await query.message.reply_text(
        "راستی اینم پیج اینستامونه. به دوستات هم معرفی کن 📷\nhttps://instagram.com/oro.stringart"
    )

    extra_discount_operator = " (تخفیف بیشتر ۱۰۰,۰۰۰ تومانی اعمال شد)" if extra_discount else ""
    message_to_operator = (
        "سفارش جدید:\n"
        f"- محصول: {context.user_data['product']}\n"
        f"- ابعاد: {context.user_data['size']}\n"
        f"- آیدی: @{context.user_data['username']}\n"
        f"- ادیت عکس: {context.user_data['edit']}\n"
        f"- کد تخفیف: {context.user_data['discount']}{marketer}{extra_discount_operator}\n"
        f"- قیمت نهایی: {final_price_str}"
    )
    try:
        await context.bot.send_message(chat_id=OPERATOR_ID, text=message_to_operator)
        await context.bot.send_photo(chat_id=OPERATOR_ID, photo=context.user_data['photo'])
    except Exception as e:
        logger.error(f"Error sending to operator: {e}")
        await context.bot.send_message(chat_id=OPERATOR_ID, text=f"خطا در ارسال به اپراتور: {e}")

    context.user_data.clear()
    return ConversationHandler.END

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Entering contact state...")
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        context.user_data['contact'] = phone_number

        user_id = context.user_data['user_id']
        context.user_data['order_completed'] = True
        remove_reminders(user_id)

        base_price = SIZES[context.user_data['size']]['price']
        discount_amount = 240000 if context.user_data['discount'] in DISCOUNT_CODES else 0
        extra_discount = 100000 if context.user_data.get('extra_discount_eligible', False) else 0
        final_price = base_price - discount_amount - extra_discount
        final_price_str = f"{final_price:,} تومان".replace(',', '،')

        extra_discount_message = " و به‌خاطر تکمیل سریع سفارش، ۱۰۰,۰۰۰ تومن تخفیف بیشتر برات اعمال شد! 🎉" if extra_discount else ""
        await update.message.reply_text(
            f"ممنون که شماره‌ت رو به اشتراک گذاشتی! 🙏{extra_discount_message}",
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text(
            f"سفارشت ثبت شد. 🎉\nمنتظر پیاممون باش. زودی باهات تماس می‌گیریم و هماهنگ می‌شیم! 📞\n"
            f"مرسی که با oro همراه شدی. 🙏",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 ثبت سفارش دیگر", switch_inline_query_current_chat="محصولات")],
                [
                    InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support"),
                    InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات")
                ]
            ])
        )

        await update.message.reply_text(
            "راستی اینم پیج اینستامونه. به دوستات هم معرفی کن 📷\nhttps://instagram.com//oro.stringart"
        )

        extra_discount_operator = " (تخفیف بیشتر ۱۰۰,۰۰۰ تومانی اعمال شد)" if extra_discount else ""
        marketer = f" (بازاریاب: {DISCOUNT_CODES[context.user_data['discount']]})" if context.user_data['discount'] in DISCOUNT_CODES else ""
        message_to_operator = (
            "سفارش جدید:\n"
            f"- محصول: {context.user_data['product']}\n"
            f"- ابعاد: {context.user_data['size']}\n"
            f"- شماره تماس: {context.user_data['contact']}\n"
            f"- ادیت عکس: {context.user_data['edit']}\n"
            f"- کد تخفیف: {context.user_data['discount']}{marketer}{extra_discount_operator}\n"
            f"- قیمت نهایی: {final_price_str}"
        )
        try:
            await context.bot.send_message(chat_id=OPERATOR_ID, text=message_to_operator)
            await context.bot.send_photo(chat_id=OPERATOR_ID, photo=context.user_data['photo'])
        except Exception as e:
            logger.error(f"Error sending to operator: {e}")
            await context.bot.send_message(chat_id=OPERATOR_ID, text=f"خطا در ارسال به اپراتور: {e}")

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

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.message.from_user.id} restarted the order process")
    user_id = context.user_data.get('user_id')
    if user_id:
        remove_reminders(user_id)
    context.user_data.clear()
    await update.message.reply_text("بیا دوباره شروع کنیم! 😊")
    await update.message.reply_text(
        "برای دیدن نمونه کارهامون، پیج اینستامون رو حتماً ببین:\n 👇یک محصول انتخاب کن",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")],
            [
                InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
            ],
            [
                InlineKeyboardButton("📖 درباره ما", callback_data="about_us"),
                InlineKeyboardButton("📷 اینستاگرام", url="https://instagram.com/oro.stringart")
            ]
        ])
    )
    return PRODUCT

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.effective_user.id} requested support")
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "به پشتیبانی خوش اومدی! 😊\n"
            "اگه سؤالی داری یا به مشکلی خوردی، همینجا برامون بنویس.\n"
            "یا اگه می‌خوای با اپراتور صحبت کنی، دکمه زیر رو بزن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 صحبت با اپراتور", callback_data="send_to_operator")]
            ])
        )
    else:
        await update.message.reply_text(
            "به پشتیبانی خوش اومدی! 😊\n"
            "اگه سؤالی داری یا به مشکلی خوردی، همینجا برامون بنویس.\n"
            "یا اگه می‌خوای با اپراتور صحبت کنی، دکمه زیر رو بزن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 صحبت با اپراتور", callback_data="send_to_operator")]
            ])
        )
    return SUPPORT

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Handling support message from user: {update.effective_user.id}")
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "send_to_operator":
            await query.message.reply_text(
                "در حال انتقال به اپراتور... ⏳\nلطفاً منتظر بمون، زودی باهات تماس می‌گیرن! 📞"
            )
            try:
                await context.bot.send_message(
                    chat_id=OPERATOR_ID,
                    text=f"کاربر @{update.effective_user.username} درخواست پشتیبانی داره.\nلطفاً باهاش تماس بگیر!"
                )
            except Exception as e:
                logger.error(f"Error sending to operator: {e}")
                await query.message.reply_text("متأسفم، خطایی پیش اومد. لطفاً دوباره امتحان کن! 😔")
            return ConversationHandler.END
    else:
        user_message = update.message.text
        await update.message.reply_text(
            "پیامت رو برای اپراتور فرستادم! 📤\nزودی باهات تماس می‌گیرن. 📞"
        )
        try:
            await context.bot.send_message(
                chat_id=OPERATOR_ID,
                text=f"پیام از @{update.message.from_user.username}:\n{user_message}"
            )
        except Exception as e:
            logger.error(f"Error sending to operator: {e}")
            await update.message.reply_text("متأسفم، خطایی پیش اومد. لطفاً دوباره امتحان کن! 😔")
        return ConversationHandler.END

async def handle_faq_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Handling FAQ selection: {update.message.text}")
    message_text = update.message.text
    if message_text in FAQ:
        await update.message.reply_text(FAQ[message_text])
    else:
        await update.message.reply_text("لطفاً یه سؤال از منو انتخاب کن! 😊")
    return FAQ_STATE

async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} requested about us")
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "ما یه تیم جوون و پرانرژی از اردبیل هستیم که عاشق هنر و خلاقیتیم! 🎨\n"
        "با تابلوهای نخی دست‌سازمون، خاطراتت رو به یه اثر هنری تبدیل می‌کنیم. 🖼️\n"
        "هر تابلو با عشق و ظرافت ساخته می‌شه تا تو و عزیزانت رو خوشحال کنه! ❤️",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📷 اینستاگرام", url="https://instagram.com/oro.stringart")]
        ])
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error occurred: {context.error}")
    if isinstance(context.error, telegram.error.Conflict):
        logger.error("Conflict error: Another instance of the bot is running. Stopping this instance...")
        await context.application.stop()
    else:
        logger.error(f"Unhandled error: {context.error}")
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()} - {context.error}\n")

def main():
    logger.info("Building Telegram application...")
    application = Application.builder().token(BOT_TOKEN).build()

    init_db()

    reminder_thread = threading.Thread(target=reminder_loop, args=(application,), daemon=True)
    reminder_thread.start()
    logger.info("Reminder thread started")

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^🎨 شروع دوباره$'), restart),
            MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
            CallbackQueryHandler(support, pattern="^support$"),
            CallbackQueryHandler(about_us, pattern="^about_us$"),
            CallbackQueryHandler(resume_order, pattern="^resume_order$"),
        ],
        states={
            PRODUCT: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(support, pattern="^support$"),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
                MessageHandler(filters.Text() & ~filters.Command(), handle_product_selection)
            ],
            SIZE: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(support, pattern="^support$"),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
                MessageHandler(filters.Text() & ~filters.Command(), handle_size_selection)
            ],
            PHOTO: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(support, pattern="^support$"),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
                CallbackQueryHandler(photo, pattern="^understood$"),
                MessageHandler(filters.ALL & ~filters.Command(), photo)
            ],
            EDIT: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(support, pattern="^support$"),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
                MessageHandler(filters.Regex('^(بله|خیر)$'), edit)
            ],
            DISCOUNT: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                CallbackQueryHandler(support, pattern="^support$"),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
                CallbackQueryHandler(discount, pattern="^no_discount$"),
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                MessageHandler(filters.Text() & ~filters.Command(), discount)
            ],
            CONTACT: [
                MessageHandler(filters.CONTACT, contact),
                MessageHandler(filters.ALL & ~filters.Command(), contact),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
            ],
            SUPPORT: [
                CallbackQueryHandler(handle_support, pattern="^send_to_operator$"),
                MessageHandler(filters.Text() & ~filters.Command(), handle_support),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
            ],
            FAQ_STATE: [
                MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
                MessageHandler(filters.Text() & ~filters.Command(), handle_faq_selection),
                CallbackQueryHandler(about_us, pattern="^about_us$"),
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
    logger.info("Adding handlers to application...")
    application.add_handler(conv_handler)
    application.add_handler(InlineQueryHandler(inlinequery))
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    try:
        application.run_polling()
    finally:
        global running
        running = False
    logger.info("Polling started successfully!")

if __name__ == '__main__':
    main()
