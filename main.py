import telebot
from telebot import types
import requests
import fitz
import os
import json
import re

# === КОНФИГ ===
TELEGRAM_TOKEN = "8047539836:AAGuwECC3Ee53GI-QhBb_oACAZAneicb9Z0"
AI_API_KEY = "io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjBlMjM5MDg5LWE4MTItNGFiYS05OWI1LTMyNjI5NGVjNzQ2MyIsImV4cCI6NDkwNjc2NDEwMH0.Gm1wXrIoo53lYABUz4rHg7l6rYPRhECMp5pLNVNqrPmiz13jVq6LWnvUu1xP9A7WHToIp4AJCfDHhhW3Oa1f1g"
AI_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === УТИЛИТЫ ===
def clean_response(text: str) -> str:
    """Удаляет <think> и внутренние комментарии."""
    text = re.sub(r"</?think>", "", text)
    text = re.sub(r"\([^)]*\)", "", text)  # удаляем текст в скобках
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()

def chat_ai(prompt):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {AI_API_KEY}"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [
            {"role": "system", "content": "Ты умный Telegram-бот. Отвечай одним вариантом, без тегов <think>, без повторов и комментариев."},
            {"role": "user", "content": prompt}
        ]
        # max_tokens убрал, чтобы не резало ответ
    }
    try:
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(AI_URL, headers=headers, data=payload)
        response.encoding = 'utf-8'
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return clean_response(content)
    except Exception as e:
        return f"Ошибка LLM: {e}"

def get_pdf_pages(path):
    """Возвращает текст по страницам PDF."""
    doc = fitz.open(path)
    return [page.get_text().strip() for page in doc]

def get_pdf_summary(pdf_path):
    """Создает итоговое краткое изложение PDF."""
    pages = get_pdf_pages(pdf_path)
    summaries = []

    for i, text in enumerate(pages, 1):
        summaries.append(
            f"Страница {i}:\n" +
            chat_ai(f"Сделай краткое изложение этой страницы (не более 4 предложений):\n\n{text}")
        )

    combined = "\n".join(summaries)
    final_summary = chat_ai(f"Объедини эти краткие изложения страниц в одно резюме (5-7 предложений):\n\n{combined}")
    return final_summary

# === ОБРАБОТЧИКИ КОМАНД ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Инфо'), types.KeyboardButton('Помощь'))
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!\nОтправь PDF для краткого изложения.", reply_markup=markup)

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, f"Твой username: @{message.from_user.username}\nID: {message.from_user.id}")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Доступные команды:\n/start\n/info\n/help\nОтправь PDF — я сделаю краткое изложение.")

# === ОБРАБОТКА PDF ===
@bot.message_handler(content_types=['document'])
def handle_pdf(message):
    if not message.document.file_name.lower().endswith('.pdf'):
        bot.send_message(message.chat.id, "Пожалуйста, отправь PDF файл.")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(message.document.file_name, "wb") as f:
        f.write(downloaded_file)

    try:
        bot.send_message(message.chat.id, "Обрабатываю PDF, подожди пару секунд...")
        summary = get_pdf_summary(message.document.file_name)
        bot.send_message(message.chat.id, "Краткое изложение:\n" + summary)
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка: " + str(e))
    finally:
        os.remove(message.document.file_name)

# === ОБРАБОТКА КНОПОК ===
@bot.message_handler(func=lambda m: m.text == "Инфо")
def button_info(message):
    info(message)

@bot.message_handler(func=lambda m: m.text == "Помощь")
def button_help(message):
    help_command(message)

# === ЧАТ С LLM ===
@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    answer = chat_ai(message.text)
    bot.send_message(message.chat.id, answer)

bot.polling(non_stop=True)
