from flask import Flask, jsonify, render_template
import requests
import logging

# تنظیمات اولیه برای ثبت وقایع
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# صف مشتریان و وضعیت کارشناسان
queue = []  # مشتریان در صف
agents = {"Agent 1": "busy", "Agent 2": "busy", "Agent 3": "busy"}  # وضعیت کارشناسان

# آدرس سایت برای داده‌های مانیتورینگ
QUEUE_URL = 'https://vpanel.pishgaman.net/pcc/user/'
LOGIN_URL = f'{QUEUE_URL}/login'

# لاگین به سایت
def login():
    login_data = {
        'username': 'support',  # جایگزین کنید
        'password': 'Pte1577$'   # جایگزین کنید
    }
    with requests.Session() as session:
        response = session.post(LOGIN_URL, data=login_data)
        if response.status_code == 200:
            logging.info('Successfully logged in')
            return session
        else:
            logging.error('Login failed')
            return None

# تلاش برای ورود به سایت
session = login()

# مانیتورینگ سایت برای دریافت وضعیت صف و کارشناسان
def monitor_site():
    global queue, agents
    try:
        if session:
            response = session.get(f'{QUEUE_URL}/status')
            if response.status_code == 200:
                data = response.json()
                queue = data.get('queue', [])
                agents = data.get('agents', {})
                logging.info('Site status updated successfully.')
            else:
                logging.error('Error fetching status from site.')
        else:
            logging.error('Session is not initialized. Unable to fetch data.')
    except Exception as e:
        logging.error(f'Error monitoring site: {e}')

# ایجاد برنامه Flask
app = Flask(__name__)

# نمایش وضعیت صف مشتریان
@app.route('/queue', methods=['GET'])
def get_queue():
    return jsonify({
        'queue': queue,
        'agents': agents
    })

# صفحه اصلی وب برای نمایش اطلاعات صف و کارشناسان
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html', queue=queue, agents=agents)

# اجرای مانیتورینگ به صورت دوره‌ای
@app.before_first_request
def periodic_monitoring():
    import threading
    import time
    def monitor():
        while True:
            monitor_site()
            time.sleep(60)  # هر ۶۰ ثانیه مانیتورینگ انجام شود
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()

# اجرای Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
