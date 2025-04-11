import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler

# تعریف حالت‌های ConversationHandler
PRODUCT, SIZE, PHOTO, EDIT, DISCOUNT, CONTACT, SUPPORT, FAQ_STATE = range(8)

# تابع‌های هندلر (فرض می‌کنم این‌ها رو قبلاً نوشتی)
async def start(update: Update, context):
    await update.message.reply_text("سلام! 😊 به oro خوش اومدی")
    await update.message.reply_text("بیا یه نگاهی به محصولاتمون بنداز 👀")
    return PRODUCT

async def restart(update: Update, context):
    await update.message.reply_text("شروع دوباره...")
    return await start(update, context)

async def support(update: Update, context):
    await update.message.reply_text("لطفاً پیامت رو برای پشتیبانی بنویس...")
    return SUPPORT

async def handle_product_selection(update: Update, context):
    # منطق انتخاب محصول
    await update.message.reply_text("لطفاً سایز رو انتخاب کن:")
    return SIZE

async def handle_size_selection(update: Update, context):
    # منطق انتخاب سایز
    await update.message.reply_text("لطفاً عکس رو بفرست:")
    return PHOTO

async def photo(update: Update, context):
    # منطق دریافت عکس
    await update.message.reply_text("آیا می‌خوای ویرایش کنی؟ (بله/خیر)")
    return EDIT

async def edit(update: Update, context):
    # منطق ویرایش
    await update.message.reply_text("لطفاً کد تخفیف رو وارد کن (اگه نداری بنویس 'ندارم'):")
    return DISCOUNT

async def discount(update: Update, context):
    # منطق تخفیف
    await update.message.reply_text("لطفاً شماره تماس خودت رو بفرست:")
    return CONTACT

async def contact(update: Update, context):
    # منطق دریافت شماره تماس
    await update.message.reply_text("ممنون! سفارش شما ثبت شد.")
    return ConversationHandler.END

async def handle_support(update: Update, context):
    # منطق پشتیبانی
    await update.message.reply_text("پیامت به پشتیبانی ارسال شد.")
    return ConversationHandler.END

async def handle_faq_selection(update: Update, context):
    # منطق FAQ
    await update.message.reply_text("سوالت رو انتخاب کردی.")
    return ConversationHandler.END

async def inlinequery(update: Update, context):
    # منطق اینلاین کوییری (اگه داری)
    pass

def main():
    print("Building Telegram application...")
    # دریافت توکن از متغیر محیطی
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables!")

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

if __name__ == "__main__":
    main()
