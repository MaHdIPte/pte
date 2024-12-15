from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.utils.request import Request
import requests
import logging

# تنظیمات اولیه برای ثبت وقایع
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# توکن ربات تلگرام سلام
TOKEN = "7672987512:AAHO_oaU8ibBIwVAGwyNsreRQgZCpbZ7V90"

# تنظیمات پروکسی MTProto
MTPROTO_PROXY = {
    'proxy_url': 'https://t.me/proxy?server=Golden.itbt.ir&port=1380&secret=7oWAaHReHFTX5f9eK08wNaBzMy5hbWF6b25hd3MuY29t',
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
        'username': 'support',
        'password': 'Pte1577$'
    }
    with requests.Session() as session:
        response = session.post(LOGIN_URL, data=login_data)
        if response.status_code == 200:
            logging.info('Successfully logged in')
        else:
            logging.error('Login failed')
        return session

session = login()

# تابع start
async def start(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('سلام! به ربات مرکز تماس پشتیبانی خوش آمدید.')

# تابع اضافه کردن به صف
async def add_to_queue(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    customer = ' '.join(context.args)
    queue.append(customer)
    await update.message.reply_text(f'مشتری {customer} به صف اضافه شد.')
    logging.info(f'Customer {customer} added to queue.')

    try:
        response = session.post(f'{QUEUE_URL}/add', json={'customer': customer})
        if response.status_code == 200:
            await update.message.reply_text(f'مشتری {customer} با موفقیت به صف در vpanel.pishgaman.net اضافه شد.')
        else:
            await update.message.reply_text(f'خطایی در اضافه کردن مشتری به صف رخ داد.')
    except Exception as e:
        logging.error(f'Error adding customer to queue: {e}')

# تابع حذف از صف
async def remove_from_queue(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if queue:
        customer = queue.pop(0)
        await update.message.reply_text(f'مشتری {customer} از صف خارج شد.')
        logging.info(f'Customer {customer} removed from queue.')

        try:
            response = session.post(f'{QUEUE_URL}/remove', json={'customer': customer})
            if response.status_code == 200:
                await update.message.reply_text(f'مشتری {customer} از صف حذف شد.')
            else:
                await update.message.reply_text(f'خطایی در حذف مشتری از صف رخ داد.')
        except Exception as e:
            logging.error(f'Error removing customer from queue: {e}')
    else:
        await update.message.reply_text("هیچ مشتری در صف وجود ندارد.")

# تابع تغییر وضعیت کارشناس
async def change_agent_status(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text('لطفاً نام کارشناس و وضعیت جدید را وارد کنید.')
        return
    
    agent = context.args[0]
    status = context.args[1]
    if agent in agents:
        agents[agent] = status
        await update.message.reply_text(f'وضعیت {agent} به {status} تغییر یافت.')
        logging.info(f'{agent} status changed to {status}.')
    else:
        await update.message.reply_text('کارشناس یافت نشد.')

# تابع مانیتورینگ سایت
async def monitor_site(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        response = session.get(f'{QUEUE_URL}/status')
        if response.status_code == 200:
            data = response.json()
            current_queue = data['queue']
            current_agents = data['agents']

            if current_queue != queue:
                for customer in current_queue:
                    if customer not in queue:
                        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f'مشتری {customer} به صف اضافه شد.')
                        logging.info(f'Customer {customer} added to queue.')
                for customer in queue:
                    if customer not in current_queue:
                        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f'مشتری {customer} از صف خارج شد.')
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

# تابع اصلی
async def main() -> None:
    request = Request(con_pool_size=8, proxy_url=MTPROTO_PROXY['proxy_url'])
    bot = Bot(token=TOKEN, request=request)
    
    application = Application.builder().token(TOKEN).build()

    # اضافه کردن دستورات به ربات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_to_queue", add_to_queue))
    application.add_handler(CommandHandler("remove_from_queue", remove_from_queue))
    application.add_handler(CommandHandler("change_agent_status", change_agent_status))

    # ایجاد JobQueue برای مانیتورینگ دوره‌ای
    application.job_queue.run_repeating(monitor_site, interval=60, first=0)

    # شروع ربات
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
