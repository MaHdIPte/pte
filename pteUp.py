from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
from telegram.utils.request import Request
from telegram import Bot
from telegram.ext import Application, CommandHandler
import requests
import logging

# تنظیمات اولیه برای ثبت وقایع
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# توکن ربات تلگرام
TOKEN = "7672987512:AAHO_oaU8ibBIwVAGwyNsreRQgZCpbZ7V90"

# تنظیمات پروکسی MTProto
MTPROTO_PROXY = {
    'proxy_url': 'https://t.me/proxy?server=Golden.itbt.ir&port=1380&secret=7oWAaHReHFTX5f9eK08wNaBzMy5hbWF6b25hd3MuY29t',  # آدرس پروکسی و پورت
    'urllib3_proxy_kwargs': {
        'username': '',  # اگر پروکسی نیاز به احراز هویت دارد، نام کاربری را وارد کنید
        'password': '',  # اگر پروکسی نیاز به احراز هویت دارد، رمز عبور را وارد کنید
    }
}

# آدرس صف برای مانیتورینگ
QUEUE_URL = 'https://vpanel.pishgaman.net/pcc/user/'
LOGIN_URL = f'{QUEUE_URL}/login'
GROUP_CHAT_ID = '4660090165'  # آیدی گروه تلگرام

# نمونه‌گیری از کاربران و کارشناسان
queue = []
agents = {"Agent 1": "busy", "Agent 2": "busy", "Agent 3": "busy"}

def login():
    login_data = {
        'username': 'support',  # جایگزین کنید
        'password': 'Pte1577$'   # جایگزین کنید
    }
    with requests.Session() as session:
        response = session.post(LOGIN_URL, data=login_data)
        if response.status_code == 200:
            logging.info('Successfully logged in')
        else:
            logging.error('Login failed')
        return session

session = login()

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('سلام! به ربات مرکز تماس پشتیبانی خوش آمدید.')

def add_to_queue(update: Update, context: CallbackContext) -> None:
    customer = ' '.join(context.args)
    queue.append(customer)
    update.message.reply_text(f'مشتری {customer} به صف اضافه شد.')
    logging.info(f'Customer {customer} added to queue.')

    # درخواست به آدرس صف برای اضافه کردن مشتری
    try:
        response = session.post(f'{QUEUE_URL}/add', json={'customer': customer})
        if response.status_code == 200:
            update.message.reply_text(f'مشتری {customer} با موفقیت به صف در vpanel.pishgaman.net اضافه شد.')
        else:
            update.message.reply_text(f'خطایی در اضافه کردن مشتری به صف در vpanel.pishgaman.net رخ داد.')
    except Exception as e:
        logging.error(f'Error adding customer to queue: {e}')

def remove_from_queue(update: Update, context: CallbackContext) -> None:
    customer = queue.pop(0)
    update.message.reply_text(f'مشتری {customer} از صف خارج شد.')
    logging.info(f'Customer {customer} removed from queue.')

    # درخواست به آدرس صف برای حذف مشتری
    try:
        response = session.post(f'{QUEUE_URL}/remove', json={'customer': customer})
        if response.status_code == 200:
            update.message.reply_text(f'مشتری {customer} با موفقیت از صف در vpanel.pishgaman.net حذف شد.')
        else:
            update.message.reply_text(f'خطایی در حذف مشتری از صف در vpanel.pishgaman.net رخ داد.')
    except Exception as e:
        logging.error(f'Error removing customer from queue: {e}')

def change_agent_status(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        update.message.reply_text('لطفاً نام کارشناس و وضعیت جدید را وارد کنید.')
        return
    
    agent = context.args[0]
    status = context.args[1]
    if agent in agents:
        agents[agent] = status
        update.message.reply_text(f'وضعیت {agent} به {status} تغییر یافت.')
        logging.info(f'{agent} status changed to {status}.')
    else:
        update.message.reply_text('کارشناس یافت نشد.')

def monitor_site(context: CallbackContext) -> None:
    # مانیتورینگ سایت برای تغییرات در صف و وضعیت کارشناسان
    try:
        response = session.get(f'{QUEUE_URL}/status')
        if response.status_code == 200:
            data = response.json()
            current_queue = data['queue']
            current_agents = data['agents']

            # بررسی تغییرات در صف
            if current_queue != queue:
                for customer in current_queue:
                    if customer not in queue:
                        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f'مشتری {customer} به صف اضافه شد.')
                        logging.info(f'Customer {customer} added to queue.')
                for customer in queue:
                    if customer not in current_queue:
                        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f'مشتری {customer} از صف خارج شد.')
                        logging.info(f'Customer {customer} removed from queue.')
                queue.clear()
                queue.extend(current_queue)
            for agent, status in current_agents.items():
                if agents.get(agent) != status:
                    logging.info(f'{agent} status changed to {status}.')
                    agents[agent] = status
        else:
            logging.error('Error fetching status from site.')
    except Exception as e:
        logging.error(f'Error monitoring site: {e}')

def main() -> None:
    # ایجاد ربات تلگرام با تنظیم پروکسی MTProto
    request = Request(con_pool_size=8, proxy_url=MTPROTO_PROXY['proxy_url'])
    bot = Bot(token=TOKEN, request=request)

    updater = Updater(bot=bot)
    dispatcher = updater.dispatcher

    # دستورهای ربات
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("add_to_queue", add_to_queue))
    dispatcher.add_handler(CommandHandler("remove_from_queue", remove_from_queue))
    dispatcher.add_handler(CommandHandler("change_agent_status", change_agent_status))

    # ایجاد JobQueue برای مانیتورینگ دوره‌ای سایت
    job_queue = updater.job_queue
    job_queue.run_repeating(monitor_site, interval=60, first=0)  # مانیتورینگ هر 60 ثانیه

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
