import telebot
from flask import Flask, request
import requests
import fitz
import os
import json
import re

# === КОНФИГ ===
TELEGRAM_TOKEN = "8047539836:AAGuwECC3Ee53GI-QhBb_oACAZAneicb9Z0"
AI_API_KEY = "io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjBlMjM5MDg5LWE4MTItNGFiYS05OWI1LTMyNjI5NGVjNzQ2MyIsImV4cCI6NDkwNjc2NDEwMH0.Gm1wXrIoo53lYABUz4rHg7l6rYPRhECMp5pLNVNqrPmiz13jVq6LWnvUu1xP9A7WHToIp4AJCfDHhhW3Oa1f1g"
AI_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
MODEL = "deepseek-ai/DeepSeek-R1-0528"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
server = Flask(__name__)

# === УТИЛИТЫ ===
def clean_response(text: str) -> str:
    """Удаляет служебные теги и лишние скобки."""
    text = re.sub(r"</?think>", "", text)
    text = re.sub(r"\([^)]*\)", "", text)
    return text.strip()

def chat_ai(prompt):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {AI_API_KEY}"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Отвечай одним абзацем, без тегов <think> и повторов."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(AI_URL, headers=headers, data=payload)
        result = response.json()

        # Если нет choices, вернем весь ответ
        if "choices" in result and len(result["choices"]) > 0:
            return clean_response(result["choices"][0]["message"]["content"])
        else:
            return f"Ошибка LLM: {result}"
    except Exception as e:
        return f"Ошибка LLM: {e}"

def get_pdf_text(path):
    """Извлекает текст из PDF."""
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text

def get_summary(text):
    """Краткое изложение текста."""
    return chat_ai(f"Сделай краткое изложение текста:\n{text[:4000]}")

# === ОБРАБОТЧИКИ ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Инфо", "Помощь")
    bot.send_message(
        message.chat.id,
        "Привет! Отправь PDF, и я сделаю краткое изложение."
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "Доступные команды:\n"
        "/start - Приветствие и клавиатура\n"
        "/help - Список команд\n"
        "/info - Информация о пользователе\n"
        "Отправь PDF — я сделаю краткое изложение.\n"
        "Также можешь написать сообщение для общения с ИИ."
    )

@bot.message_handler(commands=['info'])
def info_command(message):
    bot.send_message(
        message.chat.id,
        f"Твой username: @{message.from_user.username}\n"
        f"ID: {message.from_user.id}"
    )

@bot.message_handler(content_types=['document'])
def handle_pdf(message):
    if not message.document.file_name.lower().endswith('.pdf'):
        bot.send_message(message.chat.id, "Отправь PDF файл.")
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(message.document.file_name, "wb") as f:
        f.write(downloaded_file)
    try:
        bot.send_message(message.chat.id, "Обрабатываю PDF...")
        text = get_pdf_text(message.document.file_name)
        summary = get_summary(text)
        bot.send_message(message.chat.id, "Краткое изложение:\n" + summary)
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка: " + str(e))
    finally:
        os.remove(message.document.file_name)

@bot.message_handler(func=lambda message: message.text.lower() == "инфо")
def button_info(message):
    info_command(message)

@bot.message_handler(func=lambda message: message.text.lower() == "помощь")
def button_help(message):
    help_command(message)

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    bot.send_message(message.chat.id, chat_ai(message.text))

# === FLASK WEBHOOK ===
@server.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "ok", 200

@server.route("/")
def home():
    return "Бот работает!", 200

if __name__ == "__main__":
    # Webhook для Render
    bot.remove_webhook()
    bot.set_webhook(url=f"https://alik-telegram-bott.onrender.com/{TELEGRAM_TOKEN}")
    port = int(os.environ.get('PORT', 10000))
    server.run(host="0.0.0.0", port=port)
