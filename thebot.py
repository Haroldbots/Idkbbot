from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
import asyncio

TOKEN = "5367481170:AAHZic0ZO1u5zFWTYSl1PQEtW9rvfJuyRuY"
ADMIN_ID = 5763421850

# إعداد قاعدة البيانات
conn = sqlite3.connect('movies.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS movies (file_id TEXT, title TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER)''')  # جدول الأدمينة
conn.commit()

async def start(update: Update, context: CallbackContext):
    message = ("اهلا وسهلا بك في بوت الافلام، اكتب عنوان الفلم الذي تريده وسارسله لك\n"
               "المطور : @iitsharold")
    await update.message.reply_text(message)

async def add_movie(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID or is_admin(update.message.from_user.id):
        context.user_data['adding_movie'] = True
        context.user_data['adder_id'] = update.message.from_user.id
        await update.message.reply_text("أرسل عنوان الفيلم:")
    else:
        await update.message.reply_text("ليس لديك الصلاحية لاستخدام هذا الأمر.")

async def delete_movie(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID or is_admin(update.message.from_user.id):
        context.user_data['deleting_movie'] = True
        await update.message.reply_text("أرسل عنوان الفيلم الذي تريد حذفه:")
    else:
        await update.message.reply_text("ليس لديك الصلاحية لاستخدام هذا الأمر.")

async def count_movies(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID or is_admin(update.message.from_user.id):
        c.execute("SELECT COUNT(*) FROM movies")
        count = c.fetchone()[0]
        await update.message.reply_text(f"عدد الأفلام في البوت هو: {count}")
    else:
        await update.message.reply_text("ليس لديك الصلاحية لاستخدام هذا الأمر.")

async def add_admin(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID:
        if len(context.args) == 1:
            new_admin_id = int(context.args[0])
            c.execute("INSERT INTO admins (user_id) VALUES (?)", (new_admin_id,))
            conn.commit()
            await update.message.reply_text(f"تمت إضافة الأدمين: {new_admin_id}")
        else:
            await update.message.reply_text("يرجى تقديم معرّف الأدمين بعد الأمر.")
    else:
        await update.message.reply_text("ليس لديك الصلاحية لاستخدام هذا الأمر.")

async def remove_admin(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID:
        if len(context.args) == 1:
            admin_id = int(context.args[0])
            c.execute("DELETE FROM admins WHERE user_id = ?", (admin_id,))
            conn.commit()
            await update.message.reply_text(f"تمت إزالة الأدمين: {admin_id}")
        else:
            await update.message.reply_text("يرجى تقديم معرّف الأدمين بعد الأمر.")
    else:
        await update.message.reply_text("ليس لديك الصلاحية لاستخدام هذا الأمر.")

async def list_admins(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID:
        c.execute("SELECT user_id FROM admins")
        admins = c.fetchall()
        if admins:
            admin_ids = [str(admin[0]) for admin in admins]
            await update.message.reply_text("الأدمينة الحاليين:\n" + "\n".join(admin_ids))
        else:
            await update.message.reply_text("لا يوجد أدمينة في القائمة.")
    else:
        await update.message.reply_text("ليس لديك الصلاحية لاستخدام هذا الأمر.")

def is_admin(user_id):
    c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    return c.fetchone() is not None

async def notify_admin_of_new_movie(bot, title, adder_id):
    adder_chat = await bot.get_chat(adder_id)
    message = (f"تم إضافة فيلم جديد بعنوان: {title}\n"
               f"أضافه: {adder_chat.first_name}")
    await bot.send_message(chat_id=ADMIN_ID, text=message)

async def handle_message(update: Update, context: CallbackContext):
    user_data = context.user_data

    if 'adding_movie' in user_data and user_data['adding_movie']:
        if 'movie_title' not in user_data:
            user_data['movie_title'] = update.message.text
            await update.message.reply_text("أرسل الفيلم الآن:")
        else:
            file_id = update.message.video.file_id
            title = user_data['movie_title']
            adder_id = user_data['adder_id']
            c.execute("INSERT INTO movies (file_id, title) VALUES (?, ?)", (file_id, title))
            conn.commit()
            user_data.clear()
            await update.message.reply_text(f"تم حفظ الفيلم بعنوان: {title}")
            await notify_admin_of_new_movie(context.bot, title, adder_id)

    elif 'deleting_movie' in user_data and user_data['deleting_movie']:
        title = update.message.text
        c.execute("DELETE FROM movies WHERE title = ?", (title,))
        conn.commit()
        user_data.clear()
        await update.message.reply_text(f"تم حذف الفيلم بعنوان: {title}")

    else:
        title = update.message.text
        c.execute("SELECT file_id FROM movies WHERE title = ?", (title,))
        result = c.fetchone()
        if result:
            file_id = result[0]
            await context.bot.send_video(chat_id=update.message.chat_id, video=file_id)
        else:
            await update.message.reply_text("الفيلم غير موجود")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_movie", add_movie))
    application.add_handler(CommandHandler("delete_movie", delete_movie))
    application.add_handler(CommandHandler("count_movies", count_movies))
    application.add_handler(CommandHandler("add_admin", add_admin))
    application.add_handler(CommandHandler("remove_admin", remove_admin))
    application.add_handler(CommandHandler("list_admins", list_admins))
    application.add_handler(MessageHandler(filters.TEXT | filters.VIDEO, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()