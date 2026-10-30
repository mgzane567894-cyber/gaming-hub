import logging
import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client, Client

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = os.environ.get("MOVIE_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

ADSTERRA_DIRECT_LINK = "https://araplhn.org/4/a5cf2ac42fc3b28070b87afb456402e7"
ADMIN_ID = 7122952141

# Supabase Client ချိတ်ဆက်ခြင်း
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- FLASK SERVER (UptimeRobot အတွက်) ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Movie Bot is running and active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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

    # Deep Link ကနေ ဝင်လာတဲ့ ဇာတ်ကားနာမည် (ဥပမာ - Solo_Leveling သို့မဟုတ် Solo Leveling)
    query = args[0].replace("_", " ")
    
    try:
        response = supabase.table("movies").select("*").ilike("title", f"%{query}%").execute()
        movies_data = response.data
        
        if not movies_data:
            await update.message.reply_text(f"❌ '{query}' နှင့် ကိုက်ညီသော ဇာတ်ကားများကို မတွေ့ရှိရသေးပါ။")
            return
            
        # အပိုင်းတွေ အကုန်ပေါ်လာအောင် Inline Buttons တွေ တည်ဆောက်ခြင်း
        keyboard = []
        for movie in movies_data:
            # ဇာတ်ကား ID ကို Callback အနေနဲ့ သို့မဟုတ် Command အနေနဲ့ ချိတ်ပေးနိုင်ပါတယ်
            button_text = f"🎬 {movie['title']} - {movie['episode']}"
            callback_data = f"get_{movie['id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🍿 **'{query}' ဇာတ်ကားအတွက် ရရှိနိုင်သော အပိုင်းများ:**\nအောက်ပါခလုတ်များကို နှိပ်ပြီး ရယူနိုင်ပါသည် -",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
            
    except Exception as e:
        print(f"Database error: {e}")
        await update.message.reply_text("⚠️ ဒေတာဘေ့စ် ချိတ်ဆက်ရာတွင် အမှားအယွင်း ရှိနေပါသည်။")

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("ကျေးဇူးပြု၍ ရှာလိုသော ရုပ်ရှင်နာမည် ထည့်ပါ (ဥပမာ - `/search Solo Leveling`)")
        return
        
    query = " ".join(context.args)
    
    try:
        response = supabase.table("movies").select("*").ilike("title", f"%{query}%").execute()
        movies = response.data
        
        if not movies:
            await update.message.reply_text(f"🔍 '{query}' နှင့် ကိုက်ညီသော ရုပ်ရှင်/အန်နီမေးရှင်း မတွေ့ရှိပါ။")
            return
            
        keyboard = []
        for m in movies:
            button_text = f"🎬 {m['title']} ({m['episode']})"
            callback_data = f"get_{m['id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🍿 **'{query}' အတွက် ရှာတွေ့သော ရုပ်ရှင်များ:**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Search error: {e}")

# Inline Button နှိပ်လိုက်တဲ့အခါ ဗီဒီယို ပို့ပေးမယ့် Handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("get_"):
        movie_id = int(data.split("_")[1])
        
        try:
            response = supabase.table("movies").select("*").eq("id", movie_id).execute()
            if response.data:
                movie = response.data[0]
                await send_movie_with_timer(update, context, movie['file_id'], f"{movie['title']} - {movie['episode']}")
            else:
                await query.message.reply_text("❌ ဒီဖိုင်ကို မတွေ့တော့ပါ။")
        except Exception as e:
            print(f"Callback error: {e}")

async def send_movie_with_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, video_file_id: str, movie_name: str):
    chat_id = update.effective_chat.id
    
    caption_text = (
        f"🍿 **{movie_name}**\n\n"
        "⏳ **ဒီဗီဒီယိုဟာ (၅) မိနစ်အတွင်း အလိုအလျောက် ပျက်သွားမှာဖြစ်လို့ အမြန်ဆုံး Forward လုပ်ပြီး သိမ်းထားပါ!**"
    )
    
    sent_message = await context.bot.send_video(
        chat_id=chat_id,
        video=video_file_id,
        caption=caption_text,
        parse_mode="Markdown"
    )
    
    context.application.create_task(delete_message_after_delay(context, chat_id, sent_message.message_id, 300))

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int):
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
        
        caption = update.message.caption or "Unknown Title | Ep 1"
        parts = caption.split("|")
        title = parts[0].strip() if len(parts) > 0 else "Movie"
        episode = parts[1].strip() if len(parts) > 1 else "Ep 1"
        
        try:
            data = {"title": title, "episode": episode, "file_id": file_id}
            supabase.table("movies").insert(data).execute()
            
            await update.message.reply_text(
                f"✅ **Database သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!**\n\n"
                f"🎬 နာမည်: `{title}`\n"
                f"📌 အပိုင်း: `{episode}`\n"
                f"📁 File ID: `{file_id}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Database ထဲ သိမ်းရာတွင် အမှားဖြစ်သွားသည်: {e}")

def main():
    if not BOT_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Required environment variables are missing!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search_movie))
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_admin_video))
    
    # Callback Query Handler (ခလုတ်နှိပ်တာကို ဖမ်းရန်)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Flask ကို Background Thread နဲ့ စတင်ခြင်း
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Movie Bot with Supabase Persistence and Flask is running...")
    
    # Telegram Bot Polling စတင်ခြင်း
    application.run_polling()

if __name__ == '__main__':
    main()
