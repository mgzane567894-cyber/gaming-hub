import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------- CONFIGURATION ----------------
# Render ၏ Environment Variables မှ Token ကို ယူမည် (မရှိပါက ပေးထားသော Token ကို သုံးမည်)
BOT_TOKEN = os.environ.get("MOVIE_BOT_TOKEN", "9184533069:AAEP0vALVaMWRP_j_8zfa1_5vhzptyIOg2c")
ADSTERRA_DIRECT_LINK = "https://araplhn.org/4/a5cf2ac42fc3b28070b87afb456402e7"
ADMIN_ID = 7122952141

# ---------------- HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    args = context.args
    
    if not args:
        welcome_text = (
            f"🎬 **မင်္ဂလာပါ {user.first_name}!**\n\n"
            "🍿 **Movie Sharing Hub Bot မှ ကြိုဆိုပါတယ်။**\n"
            "ရုပ်ရှင်နှင့် ဇာတ်ကားများကို ရှာဖွေလိုပါက - `/search ရုပ်ရှင်နာမည်` ဟု ရိုက်ရှာပါ။"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        return

    movie_code = args[0]
    
    # ဤနေရာတွင် Adsterra Link ဖြင့် ဖွင့်ခိုင်းပြီးမှ ရုပ်ရှင်ပို့မည့် ပုံစံကို ဖန်တီးနိုင်သည်
    message_text = (
        f"🎬 **ရုပ်ရှင်ဖိုင် ရယူရန် အဆင်သင့်ဖြစ်ပါပြီ!**\n\n"
        "⚡ **အရေးကြီးသတိပေးချက်:**\n"
        "⚠️ ပို့ပေးလာမည့် ဗီဒီယိုကို **(၅) မိနစ်အတွင်း** မိမိတို့ရဲ့ Saved Messages သို့မဟုတ် အခြားချတ်သို့ **Forward လုပ်ပြီး သိမ်းထားပါ**။\n"
        "⏱️ (၅) မိနစ်ပြည့်သည်နှင့် Bot ထဲမှ ဗီဒီယိုသည် **အလိုအလျောက် ပျက်သွားမည်** ဖြစ်ပါသည်။"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔓 Unlock Movie Link (Ad)", url=ADSTERRA_DIRECT_LINK)]
    ]
    
    await update.message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def send_movie_with_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, video_file_id: str, movie_name: str):
    """ဗီဒီယိုကို ပို့မည်၊ ပြီးလျှင် ၅ မိနစ် (၃၀၀ စက္ကန့်) အကြာတွင် အလိုအလျောက် ဖျက်မည်"""
    chat_id = update.effective_chat.id
    
    caption_text = (
        f"🍿 **{movie_name}**\n\n"
        "⏳ **ဒီဗီဒီယိုဟာ (၅) မိနစ်အတွင်း အလိုအလျောက် ပျက်သွားမှာဖြစ်လို့ အမြန်ဆုံး Forward လုပ်ပြီး သိမ်းထားပါ!**"
    )
    
    # ဗီဒီယို ပို့ခြင်း
    sent_message = await context.bot.send_video(
        chat_id=chat_id,
        video=video_file_id,
        caption=caption_text,
        parse_mode="Markdown"
    )
    
    # မိနစ် ၅ မိနစ် (300 စက္ကန့်) စောင့်ရန် background task စတင်ခြင်း
    context.application.create_task(delete_message_after_delay(context, chat_id, sent_message.message_id, 300))

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int):
    """သတ်မှတ်ထားသော စက္ကန့်ပြည့်ပါက မက်ဆေ့ဂျ်ကို ဖျက်ပေးမည့် လုပ်ဆောင်ချက်"""
    await asyncio.sleep(delay_seconds)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        warning_msg = await context.bot.send_message(
            chat_id=chat_id, 
            text="⚠️ (၅) မိနစ်ပြည့်သွားပြီဖြစ်၍ ရုပ်ရှင်ဗီဒီယိုကို Bot ထဲမှ ဖျက်လိုက်ပါပြီ။ သိမ်းထားပြီးသားဖြစ်မယ်လို့ မျှော်လင့်ပါတယ်။"
        )
        await asyncio.sleep(10)
        await context.bot.delete_message(chat_id=chat_id, message_id=warning_msg.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def handle_admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
        
    if update.message.video or update.message.document:
        file_id = update.message.video.file_id if update.message.video else update.message.document.file_id
        await update.message.reply_text(
            f"✅ ဗီဒီယို ရရှိပါပြီ။ ဤ File ID ကို Database တွင် သိမ်းဆည်းနိုင်ပါသည်:\n\n`{file_id}`",
            parse_mode="Markdown"
        )

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_admin_video))

    print("Movie Bot with Auto-Delete feature is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
