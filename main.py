import logging
import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
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
            f"👋 **မင်္ဂလာပါ {user.first_name}!**\n\n"
            "🤖 **ကမ္ဘာ့ပြင်ပကနေ မေတ္တာနဲ့ ကြိုဆိုပါတယ်ဗျာ။**\n\n"
            "✨ ကျွန်တော်ကတော့ နိုင်ငံတကာက ရုပ်ရှင်တွေ၊ Anime တွေနဲ့ Animation ကာတွန်းကားကောင်းလေးများကို မြန်မာစာတန်းထိုးနဲ့ တစ်စုတစ်စည်းတည်း ရှာဖွေကြည့်ရှုနိုင်ဖို့ ဖန်တီးထားတဲ့ စက်ရုပ်လေး ဖြစ်ပါတယ်။\n\n"
            "🔍 ကြည့်ချင်တဲ့ ဇာတ်ကားနာမည်ကို `/search ဇာတ်ကားနာမည်` လို့ ရိုက်ပြီး ရှာဖွေကြည့်ရှုနိုင်ပါတယ်ဗျာ။"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        return

    # Deep Link ထဲက underscore (_) တွေကို Space ပြောင်းမယ်၊ Database နဲ့ တိုက်စစ်ဖို့ အဆင်ပြေအောင် လုပ်မယ်
    raw_query = args[0].replace("_", " ")
    query = raw_query.replace(".", "").strip()
    
    try:
        # Supabase မှာ နာမည်တူတာကို ilike နဲ့ ရှာမည်
        response = supabase.table("movies").select("*").ilike("title", f"%{query}%").execute()
        movies_data = response.data
        
        # အကယ်၍ အတိအကျမတွေ့ရင် စာလုံးအဓိကအစွန်း (ဥပမာ - 'Ms Servant') နဲ့ ထပ်ရှာကြည့်မည်
        if not movies_data:
            sub_query = query.split()[-1] if len(query.split()) > 1 else query
            response = supabase.table("movies").select("*").ilike("title", f"%{sub_query}%").execute()
            movies_data = response.data
            
        if not movies_data:
            await update.message.reply_text(f"❌ '{raw_query}' နှင့် ကိုက်ညီသော ဇာတ်ကားများကို မတွေ့ရှိရသေးပါ။")
            return
            
        context.user_data['unlocked'] = False
        
        intro_text = (
            f"🎬 **{raw_query}** ဇာတ်ကားကို ရယူရန်...\n\n"
            "၁။ အောက်ပါ **'🔓 Unlock Link (Ad)'** ကို နှိပ်ပြီး ကြော်ငြာကျော်ပါ။\n"
            "၂။ ပြီးလျှင် **'📥 ဇာတ်ကားများ ရယူရန်'** ကို နှိပ်ပါ။"
        )
        
        intro_keyboard = [
            [InlineKeyboardButton("🔓 Unlock Link (Ad)", url=ADSTERRA_DIRECT_LINK)],
            [InlineKeyboardButton("📥 ဇာတ်ကားများ ရယူရန်", callback_data=f"show_vids_{query}")]
        ]
        
        await update.message.reply_text(intro_text, reply_markup=InlineKeyboardMarkup(intro_keyboard), parse_mode="Markdown")
            
    except Exception as e:
        print(f"Database error: {e}")
        await update.message.reply_text("⚠️ ဒေတာဘေ့စ် ချိတ်ဆက်ရာတွင် အမှားအယွင်း ရှိနေပါသည်။")

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("ကျေးဇူးပြု၍ ရှာလိုသော ဇာတ်ကားနာမည် ထည့်ပါ (ဥပမာ - `/search One Punch Man`)")
        return
        
    query = " ".join(context.args)
    
    try:
        response = supabase.table("movies").select("*").ilike("title", f"%{query}%").execute()
        movies = response.data
        
        if not movies:
            await update.message.reply_text(f"🔍 '{query}' နှင့် ကိုက်ညီသော ဇာတ်ကား မတွေ့ရှိပါ။")
            return
            
        context.user_data['unlocked'] = False
        
        intro_text = (
            f"🍿 **'{query}' ဇာတ်ကားများကို ရယူရန် -**\n\n"
            "၁။ **'🔓 Unlock Link (Ad)'** ကို အရင် နှိပ်ပါ။\n"
            "၂။ ပြီးလျှင် **'📥 ဇာတ်ကားများ ရယူရန်'** ကို နှိပ်ပါ။"
        )
        
        intro_keyboard = [
            [InlineKeyboardButton("🔓 Unlock Link (Ad)", url=ADSTERRA_DIRECT_LINK)],
            [InlineKeyboardButton("📥 ဇာတ်ကားများ ရယူရန်", callback_data=f"show_vids_{query}")]
        ]
        
        await update.message.reply_text(intro_text, reply_markup=InlineKeyboardMarkup(intro_keyboard), parse_mode="Markdown")
    except Exception as e:
        print(f"Search error: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    
    if data.startswith("show_vids_"):
        search_query = data.replace("show_vids_", "")
        
        if not context.user_data.get('unlocked', False):
            context.user_data['unlocked'] = True
            await query.answer(
                text="⚠️ အရင်ဆုံး အပေါ်က '🔓 Unlock Link (Ad)' ကို နှိပ်ပြီး ကြော်ငြာကြည့်ပေးပါ သားရီး!",
                show_alert=True
            )
            return
            
        await query.answer()
        try:
            response = supabase.table("movies").select("*").ilike("title", f"%{search_query}%").execute()
            movies_data = response.data
            
            if not movies_data:
                # ဒုတိယအကြိမ် ထပ်မံရှာဖွေခြင်း (ပိုမိုတိကျစေရန်)
                sub_query = search_query.split()[-1] if len(search_query.split()) > 1 else search_query
                response = supabase.table("movies").select("*").ilike("title", f"%{sub_query}%").execute()
                movies_data = response.data
                
            if not movies_data:
                await query.message.reply_text(f"❌ ဇာတ်ကားဖိုင်များကို မတွေ့ရှိရတော့ပါ။")
                return
                
            chat_id = update.effective_chat.id
            
            for movie in movies_data:
                review_text = movie.get('review', 'ဇာတ်ကားကောင်းလေးမို့ လက်မလွတ်တမ်း ကြည့်သင့်ပါတယ်။')
                
                caption_text = (
                    f"🎬 **{movie['title']} - {movie['episode']}**\n\n"
                    f"📝 **Review:**\n{review_text}\n\n"
                    "⏳ **ဒီဗီဒီယိုဟာ (၅) မိနစ်အတွင်း အလိုအလျောက် ပျက်သွားမှာဖြစ်လို့ အမြန်ဆုံး Saved Messages ထဲ Forward လုပ်ပြီး သိမ်းထားပါ!**"
                )
                
                sent_msg = await context.bot.send_video(
                    chat_id=chat_id,
                    video=movie['file_id'],
                    caption=caption_text,
                    parse_mode="Markdown"
                )
                
                # ⏱️ ၅ မိနစ် (စက္ကန့် ၃၀၀) ပြည့်ရင် ဗီဒီယိုအလိုအလျောက် ဖျက်မယ့်စနစ်
                context.application.create_task(delete_message_after_delay(context, chat_id, sent_msg.message_id, 300))
                await asyncio.sleep(0.5)
                
            await query.message.reply_text("✅ ဇာတ်ကားဖိုင်များအားလုံး ပို့ပြီးပါပြီ။ Saved Messages ထဲမှာ အမြန်ဆုံး သိမ်းထားလိုက်ပါတော့ 📥။")
            
        except Exception as e:
            print(f"Error sending videos: {e}")
            await query.message.reply_text("⚠️ ဗီဒီယိုများ ပို့ရာတွင် အမှားအယွင်း ရှိသွားပါသည်။")

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int):
    await asyncio.sleep(delay_seconds)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def handle_admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
        
    if update.message.video or update.message.document:
        file_id = update.message.video.file_id if update.message.video else update.message.document.file_id
        
        caption = update.message.caption or "Movie | Ep 1"
        parts = caption.split("|")
        title = parts[0].strip() if len(parts) > 0 else "Movie"
        episode = parts[1].strip() if len(parts) > 1 else "Ep 1"
        
        try:
            data = {"title": title, "episode": episode, "file_id": file_id}
            supabase.table("movies").insert(data).execute()
            
            await update.message.reply_text(
                f"✅ **Database သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!**\n\n"
                f"🎬 နာမည်: `{title}`\n"
                f"📌 အပိုင်း: `{episode}`",
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
    application.add_handler(CallbackQueryHandler(button_callback))

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Movie Bot is fully running and active...")
    application.run_polling()

if __name__ == '__main__':
    main()
