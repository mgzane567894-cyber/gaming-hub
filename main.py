import logging
import os
import asyncio
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

# ---------------- HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    args = context.args
    
    if not args:
        welcome_text = (
            f"🎬 **မင်္ဂလာပါ {user.first_name}!**\n\n"
            "🍿 **Movie Sharing Hub Bot မှ ကြိုဆိုပါတယ်။**\n"
            "ရုပ်ရှင်နှင့် ဇာတ်ကားများကို ရှာဖွေလိုပါက - `/search ရုပ်ရှင်နာမည် အပိုင်း` ဟု ရိုက်ရှာပါ။"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        return

    # ဥပမာ - payload က 'Naruto_Ep1' ပုံစံ လာမယ်ဆိုရင် ခွဲထုတ်လို့ရပါတယ်
    payload = args[0]
    
    # Supabase ထဲကနေ Data လှမ်းယူခြင်း (title သို့မဟုတ် id ဖြင့် ရှာရန်)
    # ဤနေရာတွင် ဇာတ်ကားအချက်အလက်ကို Database မှ လှမ်းထုတ်ပါမည်
    try:
        response = supabase.table("movies").select("*").eq("title", payload).execute()
        movies_data = response.data
        
        if not movies_data:
            await update.message.reply_text("❌ တောင်းဆိုထားသော ရုပ်ရှင်ကို မတွေ့ရှိရသေးပါ။")
            return
            
        # တွေ့ရှိပါက ပထမဆုံး တွေ့တဲ့ဖိုင်ကို ပို့ပေးမယ် (သို့မဟုတ် အပိုင်းအလိုက် ခွဲပြနိုင်သည်)
        for movie in movies_data:
            await send_movie_with_timer(update, context, movie['file_id'], f"{movie['title']} - {movie['episode']}")
            
    except Exception as e:
        print(f"Database error: {e}")
        await update.message.reply_text("⚠️ ဒေတာဘေ့စ် ချိတ်ဆက်ရာတွင် အမှားအယွင်း ရှိနေပါသည်။")

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("ကျေးဇူးပြု၍ ရှာလိုisသော ရုပ်ရှင်နာမည် ထည့်ပါ (ဥပမာ - `/search Naruto`)")
        return
        
    query = " ".join(context.args)
    
    try:
        # Supabase တွင် နာမည်တူ သို့မဟုတ် ပါဝင်သော ဇာတ်ကားများကို ရှာဖွေခြင်း
        response = supabase.table("movies").select("*").ilike("title", f"%{query}%").execute()
        movies = response.data
        
        if not movies:
            await update.message.reply_text(f"🔍 '{query}' နှင့် ကိုက်ညီသော ရုပ်ရှင်/အန်နီမေးရှင်း မတွေ့ရှိပါ။")
            return
            
        text = f"🍿 **'{query}' အတွက် ရှာတွေ့သော ရုပ်ရှင်များ:**\n\n"
        for m in movies:
            text += f"• 🎬 {m['title']} (အပိုင်း - {m['episode']})\n  ဖိုင်ရယူရန် - `/get_{m['id']}` ဟု ရိုက်ပါ သို့မဟုတ် အောက်ပါလင့်ကို နှိပ်ပါ။\n\n"
            
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        print(f"Search error: {e}")

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
        
        # Caption ထဲမှာ နာမည်နဲ့ အပိုင်း ပါလာရင် အလိုအလျောက် ခွဲထုတ်သိမ်းဆည်းရန်
        # ဥပမာ ပုံစံ - Naruto | Episode 1
        caption = update.message.caption or "Unknown Title | Ep 1"
        parts = caption.split("|")
        title = parts[0].strip() if len(parts) > 0 else "Movie"
        episode = parts[1].strip() if len(parts) > 1 else "Ep 1"
        
        try:
            # Supabase ထဲသို့ Data သွင်းခြင်း
            data = {"title": title, "episode": episode, "file_id": file_id}
            supabase.table("movies").insert(data).execute()
            
            await update.message.reply_text(
                f"✅ **Database သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!**\n\n"
                f"🎬 နာမည်: `{title}`\n"
                f"ច အပိုင်း: `{episode}`\n"
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

    print("Movie Bot with Supabase Persistence is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
