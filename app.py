import logging
import os
import json
import requests as http_requests
from flask import Flask, request

logging.basicConfig(level=logging.INFO)

# === CONFIG ===
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "chernyshova_bot_verify_2024")
PDF_URL_RU = os.environ.get("PDF_URL_RU", "")
PDF_URL_UA = os.environ.get("PDF_URL_UA", "")
PDF_URL_B2B_UA = os.environ.get("PDF_URL_B2B_UA", "")
PAYMENT_URL = "https://secure.wayforpay.com/button/b1dfd9c78fe33"
CALENDLY_URL = "https://calendly.com/andreu31che/30min"

META_API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

app = Flask(__name__)

# === USER STATE ===
user_states = {}

# === TEXTS (synced with Telegram bot) ===
TEXTS = {
    "ru": {
        "welcome": "Привет! Я помощник Татьяны Чернышовой 👋\n\nВыбери что тебя интересует:",
        "b2c": "Для себя — anti-age",
        "b2b": "Я косметолог",
        "menu_b2c": "Отлично! Что хочешь узнать?",
        "menu_b2b": "Отлично! Что тебя интересует?",
        "guide": "📄 Бесплатный гайд",
        "consult": "📲 Консультация",
        "courses": "🎓 Курсы",
        "channel": "📢 Канал",
        "guide_text": "Держи гайд «5 ошибок ухода, которые старят вас каждый день» 👇",
        "consult_text": "Записаться на индивидуальный разбор:\n\n📲 {}".format(CALENDLY_URL),
        "courses_text_b2c": (
            "🌿 Программа «Молодость изнутри»\n\n"
            "7-дневный протокол от врача-невролога и косметолога.\n"
            "Одно конкретное действие в день — и результат уже через неделю.\n\n"
            "💶 Стоимость: 10 евро\n\n"
            "После оплаты Татьяна пришлёт тебе ссылку на закрытый канал с материалами.\n\n"
            "💳 Оплатить: {}".format(PAYMENT_URL)
        ),
        "courses_text_b2b": (
            "🎓 Обучение для косметологов\n\n"
            "Программы обучения скоро появятся здесь.\n\n"
            "Следи за каналом — анонс будет в ближайшее время! 📢"
        ),
        "channel_url": "https://t.me/+ReTkhlrQbDk0ZjQy",
        "channel_b2b_url": "https://t.me/+S2TiLOcy1Nk1NmNi",
        "channel_text": "📢 Подписаться на канал:\n\n{}",
        "back": "⬅️ Назад",
    },
    "ua": {
        "welcome": "Привіт! Я помічник Тетяни Чернишової 👋\n\nОбери що тебе цікавить:",
        "b2c": "Для себе — anti-age",
        "b2b": "Я косметолог",
        "menu_b2c": "Чудово! Що хочеш дізнатися?",
        "menu_b2b": "Чудово! Що тебе цікавить?",
        "guide": "📄 Безкоштовний гайд",
        "consult": "📲 Консультація",
        "courses": "🎓 Курси",
        "channel": "📢 Канал",
        "guide_text": "Тримай гайд «5 помилок догляду, які старять вас щодня» 👇",
        "consult_text": "Записатися на індивідуальний розбір:\n\n📲 {}".format(CALENDLY_URL),
        "courses_text_b2c": (
            "🌿 Програма «Молодість зсередини»\n\n"
            "7-денний протокол від лікаря-невролога і косметолога.\n"
            "Одна конкретна дія на день — і результат вже за тиждень.\n\n"
            "💶 Вартість: 10 євро\n\n"
            "Після оплати Тетяна надішле тобі посилання на закритий канал з матеріалами.\n\n"
            "💳 Оплатити: {}".format(PAYMENT_URL)
        ),
        "courses_text_b2b": (
            "🎓 Навчання для косметологів\n\n"
            "Програми навчання незабаром з'являться тут.\n\n"
            "Стеж за каналом — анонс буде найближчим часом! 📢"
        ),
        "channel_url": "https://t.me/+eV7jvuOEncJlYjli",
        "channel_b2b_url": "https://t.me/+FoY6RdWgfldhOGEy",
        "channel_text": "📢 Підписатися на канал:\n\n{}",
        "back": "⬅️ Назад",
    },
    "en": {
        "welcome": "Hi! I'm Tatiana Chernyshova's assistant 👋\n\nWhat are you interested in?",
        "b2c": "Anti-age for myself",
        "b2b": "I'm a cosmetologist",
        "menu_b2c": "Great! What would you like to know?",
        "menu_b2b": "Great! What are you interested in?",
        "guide": "📄 Free guide",
        "consult": "📲 Consultation",
        "courses": "🎓 Courses",
        "channel": "📢 Channel",
        "guide_text": "Here's the guide «5 skincare mistakes that age you every day» 👇",
        "consult_text": "Book an individual consultation:\n\n📲 {}".format(CALENDLY_URL),
        "courses_text_b2c": (
            "🌿 Programme «Youth from within»\n\n"
            "7-day protocol from a neurologist and cosmetologist.\n"
            "One specific action per day — results within a week.\n\n"
            "💶 Price: 10 euros\n\n"
            "After payment Tatiana will send you a link to the private channel with materials.\n\n"
            "💳 Pay: {}".format(PAYMENT_URL)
        ),
        "courses_text_b2b": (
            "🎓 Training for cosmetologists\n\n"
            "Training programmes coming soon.\n\n"
            "Follow the channel — announcement coming soon! 📢"
        ),
        "channel_url": "https://t.me/+ReTkhlrQbDk0ZjQy",
        "channel_b2b_url": "https://t.me/+S2TiLOcy1Nk1NmNi",
        "channel_text": "📢 Subscribe to channel:\n\n{}",
        "back": "⬅️ Back",
    },
    "es": {
        "welcome": "¡Hola! Soy el asistente de Tatiana Chernyshova 👋\n\n¿Qué te interesa?",
        "b2c": "Anti-age para mí",
        "b2b": "Soy cosmetóloga",
        "menu_b2c": "¡Genial! ¿Qué quieres saber?",
        "menu_b2b": "¡Genial! ¿Qué te interesa?",
        "guide": "📄 Guía gratuita",
        "consult": "📲 Consulta",
        "courses": "🎓 Cursos",
        "channel": "📢 Canal",
        "guide_text": "Aquí tienes la guía «5 errores de cuidado que te envejecen cada día» 👇",
        "consult_text": "Reserva una consulta individual:\n\n📲 {}".format(CALENDLY_URL),
        "courses_text_b2c": (
            "🌿 Programa «Juventud desde dentro»\n\n"
            "Protocolo de 7 días de una neuróloga y cosmetóloga.\n"
            "Una acción específica al día — resultados en una semana.\n\n"
            "💶 Precio: 10 euros\n\n"
            "Después del pago Tatiana te enviará el enlace al canal privado con materiales.\n\n"
            "💳 Pagar: {}".format(PAYMENT_URL)
        ),
        "courses_text_b2b": (
            "🎓 Formación para cosmetólogas\n\n"
            "Los programas de formación aparecerán pronto aquí.\n\n"
            "¡Sigue el canal — el anuncio llegará pronto! 📢"
        ),
        "channel_url": "https://t.me/+ReTkhlrQbDk0ZjQy",
        "channel_b2b_url": "https://t.me/+S2TiLOcy1Nk1NmNi",
        "channel_text": "📢 Suscribirse al canal:\n\n{}",
        "back": "⬅️ Atrás",
    }
}


# === META API HELPERS ===

def _headers():
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }


def send_text(to, body):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    resp = http_requests.post(META_API_URL, json=payload, headers=_headers())
    logging.info(f"send_text to={to} status={resp.status_code}")
    return resp


def send_buttons(to, body, buttons):
    """Send interactive reply buttons (max 3). buttons=[{"id":"x","title":"Y"},...]"""
    btn_list = []
    for btn in buttons[:3]:
        btn_list.append({
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"][:20]
            }
        })
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": btn_list}
        }
    }
    resp = http_requests.post(META_API_URL, json=payload, headers=_headers())
    logging.info(f"send_buttons to={to} status={resp.status_code} resp={resp.text[:300]}")

    # Fallback: if interactive buttons fail, send numbered text menu
    if resp.status_code != 200:
        logging.info(f"Buttons failed, falling back to text menu")
        menu_text = body + "\n"
        for i, btn in enumerate(buttons[:3], 1):
            menu_text += f"\n{i}. {btn['title']}"
        return send_text(to, menu_text)

    return resp


def send_document(to, url, caption="", filename="guide.pdf"):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "link": url,
            "caption": caption,
            "filename": filename
        }
    }
    resp = http_requests.post(META_API_URL, json=payload, headers=_headers())
    logging.info(f"send_document to={to} status={resp.status_code}")
    return resp


# === STATE ===

def get_state(phone):
    if phone not in user_states:
        user_states[phone] = {"lang": None, "direction": None, "step": "lang"}
    return user_states[phone]


def get_pdf_url(lang, direction):
    """Return the correct PDF URL based on language and direction."""
    if direction == "b2b" and lang == "ua" and PDF_URL_B2B_UA:
        return PDF_URL_B2B_UA, "guide_b2b_ua.pdf"
    if lang == "ua" and PDF_URL_UA:
        return PDF_URL_UA, "guide_ua.pdf"
    if PDF_URL_RU:
        return PDF_URL_RU, "guide_ru.pdf"
    return None, None


# === FLOW ===

def show_lang_menu(phone):
    """4 languages → 2 messages × 2 buttons each."""
    send_buttons(phone, "Выберите язык / Оберіть мову:", [
        {"id": "lang_ru", "title": "🇷🇺 Русский"},
        {"id": "lang_ua", "title": "🇺🇦 Українська"},
    ])
    send_buttons(phone, "Choose language / Elige idioma:", [
        {"id": "lang_en", "title": "🇬🇧 English"},
        {"id": "lang_es", "title": "🇪🇸 Español"},
    ])


def handle_lang_step(phone, user_input):
    state = get_state(phone)
    lang_map = {
        "lang_ru": "ru", "lang_ua": "ua", "lang_en": "en", "lang_es": "es",
        "1": "ru", "2": "ua", "3": "en", "4": "es",
        "русский": "ru", "ru": "ru",
        "українська": "ua", "ua": "ua",
        "english": "en", "en": "en",
        "español": "es", "es": "es",
    }
    choice = lang_map.get(user_input.lower())
    if choice:
        state["lang"] = choice
        state["step"] = "direction"
        show_direction_menu(phone)
    else:
        show_lang_menu(phone)


def show_direction_menu(phone):
    """B2C / B2B + Back = 3 buttons (fits limit)."""
    state = get_state(phone)
    t = TEXTS[state["lang"]]
    send_buttons(phone, t["welcome"], [
        {"id": "dir_b2c", "title": t["b2c"][:20]},
        {"id": "dir_b2b", "title": t["b2b"][:20]},
        {"id": "back_lang", "title": t["back"][:20]},
    ])


def handle_direction_step(phone, user_input):
    state = get_state(phone)

    if user_input in ("back_lang", "0"):
        state["step"] = "lang"
        show_lang_menu(phone)
        return

    dir_map = {
        "dir_b2c": "b2c", "dir_b2b": "b2b",
        "1": "b2c", "2": "b2b",
    }
    choice = dir_map.get(user_input.lower())
    if choice:
        state["direction"] = choice
        state["step"] = "menu"
        show_main_menu(phone)
    else:
        show_direction_menu(phone)


def show_main_menu(phone):
    """4 menu items + back → split into 2 messages."""
    state = get_state(phone)
    t = TEXTS[state["lang"]]
    direction = state["direction"]
    menu_text = t["menu_b2c"] if direction == "b2c" else t["menu_b2b"]

    # First 3: guide, consult, courses
    send_buttons(phone, menu_text, [
        {"id": "act_guide", "title": t["guide"][:20]},
        {"id": "act_consult", "title": t["consult"][:20]},
        {"id": "act_courses", "title": t["courses"][:20]},
    ])
    # Channel + Back
    send_buttons(phone, "👇", [
        {"id": "act_channel", "title": t["channel"][:20]},
        {"id": "back_dir", "title": t["back"][:20]},
    ])


def handle_menu_step(phone, user_input):
    state = get_state(phone)
    lang = state["lang"]
    t = TEXTS[lang]
    direction = state["direction"]

    if user_input in ("back_dir", "0"):
        state["step"] = "direction"
        show_direction_menu(phone)
        return

    if user_input == "back_menu":
        show_main_menu(phone)
        return

    action_map = {
        "act_guide": "guide", "act_consult": "consult",
        "act_courses": "courses", "act_channel": "channel",
        "1": "guide", "2": "consult", "3": "courses", "4": "channel",
        "гайд": "guide", "guide": "guide", "guía": "guide", "pdf": "guide",
        "консультация": "consult", "консультація": "consult", "consult": "consult",
        "курс": "courses", "courses": "courses", "cursos": "courses",
        "канал": "channel", "channel": "channel", "canal": "channel",
    }

    choice = action_map.get(user_input.lower()) if user_input else None

    if choice == "guide":
        pdf_url, filename = get_pdf_url(lang, direction)
        if direction == "b2c" and pdf_url:
            send_document(phone, pdf_url, t["guide_text"], filename)
        elif direction == "b2b" and lang == "ua" and PDF_URL_B2B_UA:
            send_document(phone, PDF_URL_B2B_UA, t["guide_text"], "guide_b2b_ua.pdf")
        else:
            send_text(phone, t["guide_text"])
        send_buttons(phone, "👇", [{"id": "back_menu", "title": t["back"][:20]}])

    elif choice == "consult":
        send_text(phone, t["consult_text"])
        send_buttons(phone, "👇", [{"id": "back_menu", "title": t["back"][:20]}])

    elif choice == "courses":
        if direction == "b2c":
            send_text(phone, t["courses_text_b2c"])
        else:
            send_text(phone, t["courses_text_b2b"])
        send_buttons(phone, "👇", [{"id": "back_menu", "title": t["back"][:20]}])

    elif choice == "channel":
        channel_url = t["channel_b2b_url"] if direction == "b2b" else t["channel_url"]
        send_text(phone, t["channel_text"].format(channel_url))
        send_buttons(phone, "👇", [{"id": "back_menu", "title": t["back"][:20]}])

    else:
        show_main_menu(phone)


# === RESET ===

RESET_WORDS = {
    "start", "начать", "розпочати", "comenzar", "inicio",
    "menu", "меню", "menú",
    "restart", "reset", "заново",
    "hi", "hello", "привет", "привіт", "hola",
}


# === WEBHOOK ===

@app.route("/webhook", methods=["GET"])
def verify():
    """Meta webhook verification."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages."""
    data = request.get_json()
    if not data:
        return "OK", 200

    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return "OK", 200

        msg = messages[0]
        phone = msg.get("from", "")
        msg_type = msg.get("type", "")

        user_input = ""
        if msg_type == "text":
            user_input = msg.get("text", {}).get("body", "").strip()
        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                user_input = interactive.get("button_reply", {}).get("id", "")
            elif interactive.get("type") == "list_reply":
                user_input = interactive.get("list_reply", {}).get("id", "")

        if not user_input:
            return "OK", 200

        logging.info(f"Message from {phone}: {user_input} (type={msg_type})")

        # Reset
        if user_input.lower() in RESET_WORDS:
            user_states.pop(phone, None)
            get_state(phone)
            show_lang_menu(phone)
            return "OK", 200

        # Handle back_menu globally
        if user_input == "back_menu":
            state = get_state(phone)
            if state.get("lang") and state.get("direction"):
                show_main_menu(phone)
                return "OK", 200

        state = get_state(phone)

        if state["step"] == "lang":
            handle_lang_step(phone, user_input)
        elif state["step"] == "direction":
            handle_direction_step(phone, user_input)
        elif state["step"] == "menu":
            handle_menu_step(phone, user_input)

    except Exception as e:
        logging.error(f"Error: {e}")

    return "OK", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
