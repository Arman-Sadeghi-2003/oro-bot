import os
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler, InlineQueryHandler
import asyncio

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

    await update.message.reply_text(
        f"عالیه. 👏\nانتخابت حرف نداره ✨\nپس انتخابت شد: {context.user_data['product']} {selected_size}"
    )
    await update.message.reply_text(
        "یه نکته بگم: ℹ️\nفعلا مجموعه oro فقط در شهر اردبیل فعالیت میکنه 🏙️\nاما داریم برنامه ریزی میکنیم که به زودی همه جا باشیم. 🚀",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ متوجه شدم", callback_data="understood")]])
    )
    return PHOTO

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

    if not update.message.photo:
        await update.message.reply_text(
            "متاسفم. 😔 من نمیتونم فایل دریافت کنم. یه عکس ساده بفرست 📸\n"
            "از همین پایین 📎 رو بزن و انتخاب کن!",
            reply_markup=ORDER_KEYBOARD
        )
        return PHOTO

    context.user_data['photo'] = update.message.photo[-1].file_id

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

    message_to_operator = (
        "سفارش جدید:\n"
        f"- محصول: {context.user_data['product']}\n"
        f"- ابعاد: {context.user_data['size']}\n"
        f"- آیدی: @{context.user_data['username']}\n"
        f"- ادیت عکس: {context.user_data['edit']}\n"
        f"- کد تخفیف: {context.user_data['discount']}{marketer}"
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
        message_to_operator = (
            "سفارش جدید:\n"
            f"- محصول: {context.user_data['product']}\n"
            f"- ابعاد: {context.user_data['size']}\n"
            f"- شماره تماس: {context.user_data['contact']}\n"
            f"- ادیت عکس: {context.user_data['edit']}\n"
            f"- کد تخفیف: {context.user_data['discount']}{marketer}"
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

def main():
    print("Building Telegram application...")
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^🎨 شروع دوباره$'), restart),
            MessageHandler(filters.Regex('^💬 ارتباط با پشتیبانی$'), support),
            CallbackQueryHandler(support, pattern="^support$"),
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

    print("Bot is running...")
    application.run_polling()
    print("Polling started successfully!")

if __name__ == '__main__':
    print("Starting main function...")
    main()
