import os
import json
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# تحميل متغيرات البيئة
load_dotenv('config.env')

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DATA_FILE = "user_data.json"

user_clients = {}
scheduling_status = {}
scheduled_tasks = {}

# ----------------------------------------------------------------------
# إدارة البيانات
# ----------------------------------------------------------------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_user_accounts(user_id):
    data = load_data()
    return data.get(str(user_id), {}).get("accounts", {})

def add_account_to_user(user_id, account_id, session_string):
    data = load_data()
    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {"accounts": {}}

    data[user_id_str]["accounts"][str(account_id)] = {
        "session_string": session_string,
        "is_active": True
    }
    save_data(data)

def remove_account_from_user(user_id, account_id):
    data = load_data()
    user_id_str = str(user_id)
    account_id_str = str(account_id)

    if user_id_str in data and account_id_str in data[user_id_str]["accounts"]:
        del data[user_id_str]["accounts"][account_id_str]
        save_data(data)
        return True
    return False

# ----------------------------------------------------------------------
# الجدولة
# ----------------------------------------------------------------------

async def schedule_group_creation(user_id, account_id, user_client):
    SCHEDULE_INTERVAL = 1200

    while True:
        is_scheduled = scheduling_status.get(user_id, {}).get(account_id, False)
        if not is_scheduled:
            if account_id in scheduled_tasks:
                del scheduled_tasks[account_id]
            break

        await asyncio.sleep(SCHEDULE_INTERVAL)

        is_scheduled = scheduling_status.get(user_id, {}).get(account_id, False)
        if not is_scheduled:
            continue

        try:
            group_title = f"مجموعة تلقائية - {account_id}"
            new_group = await user_client.create_supergroup(group_title)
            group_id = new_group.id

            for i in range(1, 11):
                await user_client.send_message(group_id, f"رسالة تلقائية رقم {i}")
                await asyncio.sleep(1)

        except Exception as e:
            print(f"خطأ في الجدولة: {e}")

# ----------------------------------------------------------------------
# عملاء المستخدمين
# ----------------------------------------------------------------------

async def start_user_client(user_id, account_id, session_string):
    try:
        client = Client(
            name=f"user_{user_id}_{account_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True
        )
        await client.start()
        user_clients[account_id] = client
        return True
    except Exception as e:
        print(e)
        return False

async def stop_user_client(account_id):
    if account_id in scheduled_tasks:
        scheduled_tasks[account_id].cancel()
        del scheduled_tasks[account_id]

    if account_id in user_clients:
        await user_clients[account_id].stop()
        del user_clients[account_id]

async def initialize_clients():
    data = load_data()
    for user_id_str, user_data in data.items():
        user_id = int(user_id_str)
        for account_id_str, acc in user_data.get("accounts", {}).items():
            await start_user_client(
                user_id,
                int(account_id_str),
                acc["session_string"]
            )

# ----------------------------------------------------------------------
# البوت
# ----------------------------------------------------------------------

bot = Client(
    "telegram_manager_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply_text("مرحباً بك 👋")

@bot.on_message(filters.command("add_account") & filters.private)
async def add_account_command(client, message):
    await message.reply_text("أرسل Session String")

# ✅✅✅ السطر المصحح هنا
@bot.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def handle_session_string(client, message):
    user_id = message.from_user.id
    session_string = message.text.strip()

    if len(session_string) < 100:
        return

    temp_client = Client(
        name=f"temp_{user_id}",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True
    )

    try:
        await temp_client.start()
        me = await temp_client.get_me()
        await temp_client.stop()

        add_account_to_user(user_id, me.id, session_string)
        await start_user_client(user_id, me.id, session_string)

        await message.reply_text(f"تم إضافة الحساب @{me.username}")

    except Exception as e:
        await message.reply_text(f"خطأ: {e}")

@bot.on_message(filters.command("my_accounts") & filters.private)
async def my_accounts_command(client, message):
    accounts = get_user_accounts(message.from_user.id)
    if not accounts:
        await message.reply_text("لا يوجد حسابات")
        return

    text = "حساباتك:\n"
    for acc in accounts:
        text += f"- {acc}\n"

    await message.reply_text(text)

# ----------------------------------------------------------------------
# التشغيل
# ----------------------------------------------------------------------

async def main():
    if not os.path.exists(DATA_FILE):
        save_data({})
    await initialize_clients()
    await bot.start()
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())        # التحقق مرة أخرى بعد الانتظار
        is_scheduled = scheduling_status.get(user_id, {}).get(account_id, False)
        if not is_scheduled:
            print(f"Scheduling for account {account_id} was turned off during sleep. Skipping creation.")
            continue
        
        try:
            # 1. إنشاء مجموعة
            group_title = f"مجموعة تلقائية - {account_id} - {asyncio.get_event_loop().time()}"
            new_group = await user_client.create_supergroup(group_title)
            group_id = new_group.id
            
            # 2. إرسال 10 رسائل
            for i in range(1, 11):
                await user_client.send_message(group_id, f"رسالة تلقائية رقم {i} من الحساب.")
                await asyncio.sleep(1)
                
            print(f"Account {account_id}: Successfully created group '{group_title}' and sent 10 messages.")
            
        except Exception as e:
            print(f"Account {account_id}: Error during scheduled group creation: {e}")
            # يمكن إرسال رسالة خطأ للمستخدم هنا إذا أردنا

# ----------------------------------------------------------------------
# وظائف Pyrogram
# ----------------------------------------------------------------------

async def start_user_client(user_id, account_id, session_string):
    """بدء تشغيل عميل المستخدم (الحساب) باستخدام سلسلة الجلسة."""
    try:
        client = Client(
            name=f"user_{user_id}_account_{account_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True
        )
        await client.start()
        user_clients[account_id] = client
        print(f"Client for account {account_id} started successfully.")
        return True
    except Exception as e:
        print(f"Error starting client for account {account_id}: {e}")
        return False

async def stop_user_client(account_id):
    """إيقاف عميل المستخدم (الحساب)."""
    # إلغاء مهمة الجدولة إذا كانت نشطة
    if account_id in scheduled_tasks:
        scheduled_tasks[account_id].cancel()
        del scheduled_tasks[account_id]
        print(f"Scheduled task for account {account_id} cancelled.")
        
    if account_id in user_clients:
        await user_clients[account_id].stop()
        del user_clients[account_id]
        print(f"Client for account {account_id} stopped.")

async def initialize_clients():
    """تهيئة وبدء تشغيل جميع العملاء المخزنين عند بدء البوت."""
    data = load_data()
    for user_id_str, user_data in data.items():
        user_id = int(user_id_str)
        for account_id_str, account_data in user_data.get("accounts", {}).items():
            account_id = int(account_id_str)
            session_string = account_data["session_string"]
            await start_user_client(user_id, account_id, session_string)

# ----------------------------------------------------------------------
# منطق البوت (Client Bot)
# ----------------------------------------------------------------------

bot = Client(
    "telegram_manager_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    """الرد على أمر /start."""
    await message.reply_text(
        "مرحباً بك في بوت إدارة حسابات التليجرام.\n"
        "يمكنك إضافة حساباتك والتحكم بها بشكل فردي.\n\n"
        "الأوامر المتاحة:\n"
        "/add_account - لإضافة حساب جديد.\n"
        "/my_accounts - لعرض وإدارة حساباتك الحالية.\n"
        "/help - لعرض هذه الرسالة مرة أخرى."
    )

@bot.on_message(filters.command("add_account") & filters.private)
async def add_account_command(client, message):
    """بدء عملية إضافة حساب جديد."""
    await message.reply_text(
        "لإضافة حساب جديد، يرجى إرسال سلسلة الجلسة (Session String) الخاصة بحسابك.\n"
        "يمكنك الحصول على سلسلة الجلسة باستخدام مكتبة Pyrogram.\n\n"
        "**تحذير:** لا تشارك سلسلة الجلسة مع أي شخص غير موثوق به."
    )

@bot.on_message(filters.text & filters.private & ~filters.command)
async def handle_session_string(client, message):
    """معالجة سلسلة الجلسة المرسلة من المستخدم."""
    user_id = message.from_user.id
    session_string = message.text.strip()
    
    # تحقق بسيط من شكل سلسلة الجلسة (يمكن تحسينه)
    if len(session_string) < 100:
        return  # تجاهل الرسائل النصية القصيرة التي ليست أوامر

    # محاولة بدء العميل للتحقق من صحة سلسلة الجلسة والحصول على معلومات الحساب
    temp_client = Client(
        name=f"temp_client_{user_id}",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True
    )
    
    try:
        await temp_client.start()
        account_info = await temp_client.get_me()
        account_id = account_info.id
        account_username = account_info.username or "N/A"
        
        # إيقاف العميل المؤقت
        await temp_client.stop()
        
        # إضافة الحساب إلى قاعدة البيانات وبدء تشغيله بشكل دائم
        add_account_to_user(user_id, account_id, session_string)
        await start_user_client(user_id, account_id, session_string)
        
        await message.reply_text(
            f"تم إضافة الحساب بنجاح!\n"
            f"معرف الحساب: `{account_id}`\n"
            f"اسم المستخدم: @{account_username}\n\n"
            "يمكنك الآن إدارة هذا الحساب باستخدام الأمر /my_accounts."
        )
        
    except Exception as e:
        await message.reply_text(
            f"حدث خطأ أثناء محاولة إضافة الحساب. يرجى التأكد من صحة سلسلة الجلسة.\n"
            f"الخطأ: {e}"
        )

@bot.on_message(filters.command("my_accounts") & filters.private)
async def my_accounts_command(client, message):
    """عرض وإدارة حسابات المستخدم."""
    user_id = message.from_user.id
    accounts = get_user_accounts(user_id)
    
    if not accounts:
        await message.reply_text(
            "ليس لديك أي حسابات مضافة حالياً.\n"
            "استخدم الأمر /add_account لإضافة حساب جديد."
        )
        return

    text = "قائمة حساباتك المضافة:\n\n"
    keyboard = []
    
    for account_id_str, account_data in accounts.items():
        account_id = int(account_id_str)
        
        # محاولة الحصول على اسم المستخدم من العميل النشط
        username = "جاري التحميل..."
        if account_id in user_clients:
            try:
                me = await user_clients[account_id].get_me()
                username = me.username or "N/A"
            except Exception:
                username = "غير متصل"
        
        # التحقق من حالة الجدولة
        is_scheduled = scheduling_status.get(user_id, {}).get(account_id, False)
        schedule_status_text = "✅ (مجدول)" if is_scheduled else "❌ (غير مجدول)"
        
        text += f"**ID:** `{account_id}`\n"
        text += f"**Username:** @{username}\n"
        text += f"**الحالة:** {'✅ متصل' if account_id in user_clients else '❌ غير متصل'} {schedule_status_text}\n\n"
        
        # زر إدارة الحساب
        keyboard.append([
            InlineKeyboardButton(f"⚙️ إدارة حساب @{username}", callback_data=f"manage_account_{account_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text, reply_markup=reply_markup)

@bot.on_callback_query(filters.regex("^manage_account_"))
async def manage_account_callback(client, callback_query):
    """معالجة زر إدارة الحساب."""
    user_id = callback_query.from_user.id
    account_id = int(callback_query.data.split("_")[-1])
    
    accounts = get_user_accounts(user_id)
    if str(account_id) not in accounts:
        await callback_query.answer("هذا الحساب لم يعد موجوداً.", show_alert=True)
        await callback_query.message.delete()
        return

    # التحقق من حالة الجدولة
    is_scheduled = scheduling_status.get(user_id, {}).get(account_id, False)
    schedule_text = "✅ إيقاف الجدولة التلقائية" if is_scheduled else "❌ تشغيل الجدولة التلقائية"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إنشاء مجموعة وإرسال 10 رسائل", callback_data=f"create_group_{account_id}")],
        [InlineKeyboardButton(schedule_text, callback_data=f"toggle_schedule_{account_id}")],
        [InlineKeyboardButton("🗑️ حذف الحساب", callback_data=f"remove_account_{account_id}")],
        [InlineKeyboardButton("🔙 العودة", callback_data="my_accounts_back")]
    ])
    
    await callback_query.message.edit_text(
        f"خيارات إدارة الحساب ذو المعرف `{account_id}`:",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex("^remove_account_"))
async def remove_account_callback(client, callback_query):
    """معالجة زر حذف الحساب."""
    user_id = callback_query.from_user.id
    account_id = int(callback_query.data.split("_")[-1])
    
    # إيقاف العميل ومهمة الجدولة
    await stop_user_client(account_id)
    
    # إزالة من قاعدة البيانات
    if remove_account_from_user(user_id, account_id):
        await callback_query.answer("تم حذف الحساب بنجاح.", show_alert=True)
        await callback_query.message.edit_text(f"تم حذف الحساب ذو المعرف `{account_id}`.")
    else:
        await callback_query.answer("فشل في حذف الحساب.", show_alert=True)

@bot.on_callback_query(filters.regex("^my_accounts_back"))
async def my_accounts_back_callback(client, callback_query):
    """العودة إلى قائمة الحسابات."""
    # يجب إعادة استدعاء my_accounts_command مع رسالة جديدة لتجنب مشاكل التحرير
    await callback_query.message.delete()
    await my_accounts_command(client, callback_query.message)

@bot.on_callback_query(filters.regex("^create_group_"))
async def create_group_callback(client, callback_query):
    """معالجة زر إنشاء مجموعة وإرسال رسائل."""
    user_id = callback_query.from_user.id
    account_id = int(callback_query.data.split("_")[-1])
    
    if account_id not in user_clients:
        await callback_query.answer("الحساب غير متصل حالياً.", show_alert=True)
        return

    await callback_query.answer("جاري إنشاء المجموعة وإرسال الرسائل...", show_alert=False)
    
    user_client = user_clients[account_id]
    
    try:
        # 1. إنشاء مجموعة
        group_title = f"مجموعة يدوية - {account_id} - {asyncio.get_event_loop().time()}"
        new_group = await user_client.create_supergroup(group_title)
        group_id = new_group.id
        
        # 2. إرسال 10 رسائل
        for i in range(1, 11):
            await user_client.send_message(group_id, f"رسالة يدوية رقم {i} من الحساب.")
            await asyncio.sleep(0.5) # تأخير بسيط بين الرسائل
            
        await callback_query.message.reply_text(
            f"تم إنشاء المجموعة بنجاح: **{group_title}**\n"
            f"وتم إرسال 10 رسائل فيها."
        )
        
    except Exception as e:
        await callback_query.message.reply_text(
            f"حدث خطأ أثناء إنشاء المجموعة أو إرسال الرسائل:\n`{e}`"
        )

@bot.on_callback_query(filters.regex("^toggle_schedule_"))
async def toggle_schedule_callback(client, callback_query):
    """معالجة زر تشغيل/إيقاف الجدولة التلقائية."""
    user_id = callback_query.from_user.id
    account_id = int(callback_query.data.split("_")[-1])
    
    if account_id not in user_clients:
        await callback_query.answer("الحساب غير متصل حالياً. لا يمكن تشغيل الجدولة.", show_alert=True)
        return

    user_client = user_clients[account_id]
    
    # تحديث حالة الجدولة
    current_status = scheduling_status.get(user_id, {}).get(account_id, False)
    new_status = not current_status
    
    if user_id not in scheduling_status:
        scheduling_status[user_id] = {}
    scheduling_status[user_id][account_id] = new_status
    
    if new_status:
        # تشغيل الجدولة
        if account_id not in scheduled_tasks:
            task = asyncio.create_task(schedule_group_creation(user_id, account_id, user_client))
            scheduled_tasks[account_id] = task
            await callback_query.answer("تم تشغيل الجدولة التلقائية. سيتم إنشاء مجموعة كل 20 دقيقة.", show_alert=True)
        else:
            await callback_query.answer("الجدولة تعمل بالفعل.", show_alert=True)
    else:
        # إيقاف الجدولة
        if account_id in scheduled_tasks:
            scheduled_tasks[account_id].cancel()
            del scheduled_tasks[account_id]
            await callback_query.answer("تم إيقاف الجدولة التلقائية.", show_alert=True)
        else:
            await callback_query.answer("الجدولة متوقفة بالفعل.", show_alert=True)
    
    # إعادة عرض قائمة الإدارة لتحديث الزر
    await manage_account_callback(client, callback_query)


# ----------------------------------------------------------------------
# وظيفة التشغيل الرئيسية
# ----------------------------------------------------------------------

async def main():
    # التأكد من وجود ملف البيانات
    if not os.path.exists(DATA_FILE):
        save_data({})
        
    # تهيئة العملاء المخزنين
    await initialize_clients()
    
    # بدء تشغيل البوت
    await bot.start()
    
    # تشغيل البوت إلى الأبد
    await asyncio.Future()

if __name__ == "__main__":
    # تشغيل الدالة الرئيسية
    asyncio.run(main())
