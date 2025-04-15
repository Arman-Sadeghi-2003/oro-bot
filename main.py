import os
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler, InlineQueryHandler
import asyncio

print("Fetching BOT_TOKEN from environment...")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Please set it in Render Environment Variables.")

PRODUCT, SIZE, PHOTO, EDIT, DISCOUNT, CONTACT, SUPPORT, FAQ_STATE = range(8)
OPERATOR_ID = "7695028053"

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
    "70×70": {"price": 2450000},
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
    [["🎨 شروع دوباره", "💬 ارتباط با پشتیبانی"]],
    one_time_keyboard=False,
    resize_keyboard=True
)

ORDER_KEYBOARD = ReplyKeyboardMarkup(
    [["🎨 شروع دوباره", "💬 ارتباط با پشتیبانی"]],
    one_time_keyboard=False,
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print(f"Received /start command from user: {update.message.from_user.id}")
    context.user_data.clear()
    context.user_data['current_state'] = PRODUCT  # تنظیم مرحله
    await update.message.reply_text("سلام! 😊 به oro خوش اومدی")
    await update.message.reply_text(
        "بیا یه نگاهی به محصولاتمون بنداز 👀",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("محصولات 🎉", switch_inline_query_current_chat="محصولات")],
            [
                InlineKeyboardButton("❓ سوالات پرتکرار", switch_inline_query_current_chat="سوالات"),
                InlineKeyboardButton("💬 ارتباط با پشتیبانی", callback_data="support")
            ],
            [
                InlineKeyboardButton("📖 درباره ما", callback_data="about_us"),
                InlineKeyboardButton("📷 اینستاگرام", url="https://instagram.com/example")
            ]
        ])
    )
    return PRODUCT

async def inlinequery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Received inline query: {update.inline_query.query}")
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
                    description=f"💰 قیمت: {info['price'] if isinstance(info['price'], str) else f'{info['price']:,} تومان'}".replace(',', '،'),
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
    print(f"Handling product selection: {update.message.text}")
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
    context.user_data['current_state'] = SIZE  # به‌روزرسانی مرحله

    await update.message.reply_text(
        f"{selected_product} انتخاب شد! حالا یه سایز انتخاب کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("انتخاب سایز 📏", switch_inline_query_current_chat="سایز")]
        ])
    )
    return SIZE

async def handle_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print(f"Handling size selection: {update.message.text}")
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
    context.user_data['current_state'] = PHOTO  # به‌روزرسانی مرحله

    # تنظیم یادآوری‌ها برای تست
    user_id = context.user_data['user_id']
    chat_id = update.message.chat_id
    job_data = {'chat_id': chat_id, 'user_id': user_id}

    context.job_queue.run_once(reminder_1hour, 60, data=job_data, name=f"reminder_1h_{user_id}")  # 1 دقیقه
    context.job_queue.run_once(reminder_1day, 180, data=job_data, name=f"reminder_1d_{user_id}")  # 3 دقیقه
    context.job_queue.run_once(reminder_3days, 300, data=job_data, name=f"reminder_3d_{user_id}")  # 5 دقیقه
    context.job_queue.run_once(clear_data, 420, data=job_data, name=f"clear_data_{user_id}")  # 7 دقیقه

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
    print("Entering photo state...")
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

   te اگر not update.message.photo:
        await update.message.reply_text(
            "متاسفم. 😔 من نمیتونم فایل دریافت کنم. یه عکس ساده بفرست 📸\n"
            "از همین پایین 📎 رو بزن و انتخاب کن!",
            reply_markup=ORDER_KEYBOARD
        )
        return PHOTO

    context.user_data['photo'] = update.message.photo[-1].file_id
    context.user_data['current_state'] = EDIT  # به‌روزرسانی مرحله

    await update.message.reply_text(
        "عجب عکس باحالی! 😍\nنیاز به ادیت داره؟ ✂️\nیعنی میخوای چیزی توش عوض کنی؟\n"
        "فتوشاپ کارای ماهری داریم. رایگان هم انجام میدن. 🖌️",
        reply_markup=ReplyKeyboardMarkup([["بله", "خیر"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return EDIT

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print(f"Handling edit selection: {update.message.text}")
    context.user_data['edit'] = update.message.text
    if context.user_data['edit'] not in ["بله", "خیر"]:
        await update.message.reply_text("لطفاً فقط 'بله' یا 'خیر' رو بگو! 😊")
        return EDIT

    if context.user_data['edit'] == "خیر":
        await update.message.reply_text("باشه! ✅")
    else:
        await update.message.reply_text("حله! فتوشاپ‌کارامون زودی دست به کار می‌شن! ✂️")

    context.user_data['current_state'] = DISCOUNT  # به‌روزرسانی مرحله

    await update.message.reply_text(
        "کد تخفیف داری؟ 🎁\nهمینجا برامون بنویس، وگرنه دکمه زیر رو بزن:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 کد تخفیف ندارم", callback_data="no_discount")]])
    )
    return DISCOUNT

async def discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("Entering discount state...")
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

    # غیرفعال کردن یادآوری‌ها
    for job in context.job_queue.jobs():
        if job.name in [f"reminder_1h_{user_id}", f"reminder_1d_{user_id}", f"reminder_3d_{user_id}", f"clear_data_{user_id}"]:
            job.schedule_removal()

    # اگر کاربر یوزرنیم نداشته باشه، نیاز به شماره تماس داره
    if not context.user_data.get('username'):
        context.user_data['current_state'] = CONTACT  # به‌روزرسانی مرحله
        await (update.callback_query.message if update.callback_query else update.message).reply_text(
            "لطفاً شماره تلفنتون رو به اشتراک بذارید 📞",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("ارسال شماره تلفن 📱", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return CONTACT

    base_price = SIZES[context.user_data['size']]['price']
    discount_amount = 240000 if context.user_data['discount'] in DISCOUNT_CODES else 0
    extra_discount = 100000 if context.user_data.get('extra_discount_eligible', False) else 0
    final_price = base_price - discount_amount - extra_discount
    final_price_str = f"{final_price:,} تومان".replace(',', '،')

    extra_discount_message = " و به‌خاطر تکمیل سریع سفارش، ۱۰۰,۰۰۰ تومن تخفیف بیشتر برات اعمال شد! 🎉" if extra_discount else ""
    await (update.callback_query.message if update.callback_query else update.message).reply_text(
        f"سفارشت ثبت شد. 🎉\nمنتظر پیاممون باش. زودی باهات تماس می‌گیریم و هماهنگ می‌شیم! 📞\n"
        f"مرسی که با oro همراه شدی. 🙏{extra_discount_message}",
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
        await context.bot.send_message(chat_id=OPERATOR_ID, text=f"خطا در ارسال به اپراتور: {e}")

    context.user_data.clear()
    return ConversationHandler.END

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("Entering contact state...")
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        context.user_data['contact'] = phone_number

        user_id = context.user_data['user_id']
        context.user_data['order_completed'] = True

        # غیرفعال کردن یادآوری‌ها
        for job in context.job_queue.jobs():
            if job.name in [f"reminder_1h_{user_id}", f"reminder_1d_{user_id}", f"reminder_3d_{user_id}", f"clear_data_{user_id}"]:
                job.schedule_removal()

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

async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "ما مجموعه oro هستیم! 🎨\n"
        "یه تیم جوون و خلاق از اردبیل که عاشق خلق آثار هنری خاص مثل تابلوهای نخی هستیم. "
        "هدفمون اینه که با هنر، خاطرات شما رو ماندگار کنیم. همراهمون باشین! 😎",
        reply_markup=MAIN_KEYBOARD
    )
    return PRODUCT

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("Entering support state...")
    if update.callback_query:
        query = update.callback_query
        print(f"Support called via callback query with data: {query.data}")
        await query.answer()
    else:
        print("Support called via keyboard button")
    context.user_data['support_message'] = ""
    await (update.callback_query.message if update.callback_query else update.message).reply_text(
        "سلام رفیق! 😊 مشکلی داری؟ سوالی داری؟ هر چی هست برامون بنویس! 📩\nپشتیبانای خفنمون زودی جوابت رو می‌دن! 💪",
        reply_markup=MAIN_KEYBOARD
    )
    return SUPPORT

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("Handling support message...")
    if update.callback_query:
        query = update.callback_query
        print(f"Callback query received with data: {query.data}")
        await query.answer()
        if query.data == "send_to_operator":
            print("Sending message to operator...")
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
        print(f"Support message received: {update.message.text}")

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
    print("Entering FAQ state...")
    await update.message.reply_text(
        "سوالتو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("سوالات ❓", switch_inline_query_current_chat="سوالات")]
        ])
    )
    return FAQ_STATE

async def handle_faq_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print(f"Handling FAQ selection: {update.message.text}")
    message_text = update.message.text
    if message_text not in FAQ:
        await update.message.reply_text("لطفاً یه سوال درست انتخاب کن رفیق! 😜")
        return FAQ_STATE

    await update.message.reply_text(FAQ[message_text])
    return ConversationHandler.END

async def faq_during_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("FAQ during order state...")
    await update.message.reply_text(
        "لطفاً مراحل ثبت سفارش رو کامل کن یا 'شروع دوباره' رو بزن! 😊",
        reply_markup=ORDER_KEYBOARD
    )
    return None

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("Restarting conversation...")
    return await start(update, context)

def get_state_message(state):
    if state == PRODUCT:
        return "یادت رفته تابلوی خودت رو انتخاب کنی"
    elif state == SIZE:
        return "یادت رفته سایز تابلو رو انتخاب کنی"
    elif state == PHOTO:
        return "یادت رفته عکست رو بفرستی"
    elif state == EDIT:
        return "یادت رفته بگی عکست نیاز به ادیت داره یا نه"
    elif state == DISCOUNT:
        return "یادت رفته کد تخفیف وارد کنی یا بگی که نداری"
    elif state == CONTACT:
        return "یادت رفته شماره تلفنت رو بفرستی"
    else:
        return "به نظر می‌رسه تو یه مرحله‌ی نامشخصی هستی، بیا از اول شروع کنیم"

async def reminder_1hour(context: ContextTypes.DEFAULT_TYPE):
    print("Sending 1-hour reminder...")
    job_data = context.job.data
    current_state = context.user_data.get('current_state', PRODUCT)
    state_message = get_state_message(current_state)
    await context.bot.send_message(
        chat_id=job_data['chat_id'],
        text=(
            f"سلام دوست خوبم! 🌟\n"
            f"ما هنوز منتظریم تا سفارشت رو کامل کنی.\n"
            f"بیا ادامه بدیم و یه تابلو نخی فوق‌العاده برات بسازیم! 🎨\n\n"
            f"راستی، {state_message}!"
        )
    )

async def reminder_1day(context: ContextTypes.DEFAULT_TYPE):
    print("Sending 1-day reminder...")
    job_data = context.job.data
    context.user_data['extra_discount_eligible'] = True  # فعال کردن تخفیف اضافی
    current_state = context.user_data.get('current_state', PRODUCT)
    state_message = get_state_message(current_state)
    await context.bot.send_message(
        chat_id=job_data['chat_id'],
        text=(
            f"سلام رفیق عزیز! ✨\n"
            f"یه روزه که oro منتظرته!\n"
            f"اگه تا آخر امروز سفارشت رو تکمیل کنی، ۱۰۰,۰۰۰ تومن تخفیف بیشتر می‌گیرید! 🎁\n"
            f"بیا تمومش کنیم! 💪\n\n"
            f"راستی، {state_message}!"
        )
    )

async def reminder_3days(context: ContextTypes.DEFAULT_TYPE):
    print("Sending 3-days reminder...")
    job_data = context.job.data
    product = context.user_data.get('product', 'محصول انتخابی')
    current_state = context.user_data.get('current_state', PRODUCT)
    state_message = get_state_message(current_state)
    await context.bot.send_message(
        chat_id=job_data['chat_id'],
        text=(
            f"سلام دوست عزیز! ⚠️\n"
            f"موجودی {product} رو به اتمامه و ممکنه اطلاعات سفارشت پاک بشه!\n"
            f"تا دیر نشده، همین امروز سفارشت رو کامل کن تا خیالت راحت بشه. 🖼️\n\n"
            f"راستی، {state_message}!"
        )
    )

async def clear_data(context: ContextTypes.DEFAULT_TYPE):
    print("Clearing user data after 7 minutes...")
    context.user_data.clear()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Error occurred: {context.error}")
    if isinstance(context.error, telegram.error.Conflict):
        print("Conflict error: Another instance of the bot is running. Stopping this instance...")
        await context.application.stop()
    else:
        print("Unhandled error:", context.error)

def main():
    print("Building Telegram application...")
    application = Application.builder().token(BOT_TOKEN).build()

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
    print("Adding handlers to application...")
    application.add_handler(conv_handler)
    application.add_handler(InlineQueryHandler(inlinequery))
    application.add_error_handler(error_handler)

    print("Bot is running...")
    application.run_polling()
    print("Polling started successfully!")

if __name__ == '__main__':
    print("Starting main function...")
    main()
