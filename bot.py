from flask import Flask, request
import telegram
import json
import os
import re

# === НАСТРОЙКИ ===
TOKEN = os.environ.get('TELEGRAM_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')  # Например: https://your-bot.onrender.com/webhook
PRODUCTS_URL = 'https://ugol.store/products.json'

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# Загружаем каталог
def load_products():
    import urllib.request
    try:
        with urllib.request.urlopen(PRODUCTS_URL) as f:
            return json.load(f)
    except:
        return []

# Поиск товаров
def search_products(query, products):
    query = query.lower()
    return [p for p in products if 
            query in p.get('name', '').lower() or
            query in p.get('description', '').lower() or
            query == p.get('sku', '').lower()]

# Главное меню
def send_main_menu(chat_id):
    keyboard = [
        [telegram.KeyboardButton("/search — поиск")],
        [telegram.KeyboardButton("/product — по артикулу")],
        [telegram.KeyboardButton("/callback — перезвоните мне")],
        [telegram.KeyboardButton("/help — помощь")]
    ]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=reply_markup)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text

    if text == '/start':
        bot.send_message(chat_id=chat_id, text="👋 Добро пожаловать в «Угол чемпионов»!\nИщите экипировку для бокса и единоборств.")
        send_main_menu(chat_id)

    elif text.startswith('/search '):
        query = text.replace('/search ', '').strip()
        products = load_products()
        results = search_products(query, products)[:10]  # максимум 10
        if results:
            reply = "Найдено:\n\n"
            for p in results:
                url = f"https://ugol.store#sku-{p['sku']}"  # можно добавить якорь
                reply += f"• {p['name']} — {p.get('price', 0):,} ₽\n  Артикул: {p['sku']}\n  Наличие: {p.get('availability', '—')}\n  👉 {url}\n\n"
            bot.send_message(chat_id=chat_id, text=reply, disable_web_page_preview=True)
        else:
            bot.send_message(chat_id=chat_id, text="Товары не найдены. Попробуйте изменить запрос.")

    elif text.startswith('/product '):
        sku = text.replace('/product ', '').strip()
        products = load_products()
        product = next((p for p in products if p.get('sku') == sku), None)
        if product:
            old_price = f"~~{product['oldPrice']:,} ₽~~ " if 'oldPrice' in product else ""
            price = f"{product['price']:,} ₽"
            msg = f"""
📦 *{product['name']}*
Артикул: `{product['sku']}`
Цвет: {product.get('color', '—')}
Размер: {product.get('size', '—')}
Цена: {old_price}{price}
Наличие: {product.get('availability', '—')}

🌐 [Открыть на сайте](https://ugol.store#sku-{sku})
            """
            bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(chat_id=chat_id, text="Товар не найден. Проверьте артикул.")

    elif text == '/callback' or text == 'перезвоните мне':
        bot.send_message(chat_id=chat_id, text="📞 Оставьте свой номер телефона в формате:\n+7 (969) 600-25-85")

    elif re.match(r'^\+7\s?\(\d{3}\)\s?\d{3}-\d{2}-\d{2}$', text.replace(' ', '')):
        # Формат: +7 (969) 600-25-85
        bot.send_message(chat_id=chat_id, text="✅ Спасибо! Менеджер перезвонит вам в ближайшее время.")
        # Здесь можно отправить уведомление вам (например, в другой Telegram)
        bot.send_message(chat_id=YOUR_MANAGER_CHAT_ID, text=f"🔔 Запрос на звонок: {text}")

    elif text == '/help':
        bot.send_message(chat_id=chat_id, text="""
/start — меню  
/search <запрос> — найти товар  
/product <артикул> — карточка  
/callback — перезвоните мне  
/help — эта справка

Примеры:
`/search перчатки`
`/product C161RT`
        """, parse_mode='Markdown')

    else:
        bot.send_message(chat_id=chat_id, text="Неизвестная команда. Нажмите /help")

    return 'OK'


@app.route('/')
def index():
    return 'Telegram bot for Угол чемпионов is running!'


if __name__ == '__main__':
    # Установка webhook (делается один раз!)
    # bot.setWebhook(WEBHOOK_URL + '/webhook')
    app.run()
