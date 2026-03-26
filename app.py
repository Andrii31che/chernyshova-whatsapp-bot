import logging
import os
from flask import Flask, request
from twilio.rest import Client

logging.basicConfig(level=logging.INFO)

# === CONFIG ===
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")  # "whatsapp:+14155238886"
PDF_URL_RU = os.environ.get("PDF_URL_RU", "")  # Direct URL to RU PDF guide
PDF_URL_UA = os.environ.get("PDF_URL_UA", "")  # Direct URL to UA PDF guide
PAYMENT_URL = "https://secure.wayforpay.com/button/b1dfd9c78fe33"
CALENDLY_URL = "https://calendly.com/andreu31che/30min"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

# === USER STATE (in-memory, per phone number) ===
user_states = {}

# === TEXTS (synced with Telegram bot v2) ===
TEXTS = {
    "ru": {
        "welcome": "Привет! Я помощник Татьяны Чернышовой 👋\n\nВыбери что тебя интересует:",
        "b2c": "Для себя — anti-age",
        "b2b": "Я косметолог",
        "menu_b2c": "Отлично! Что хочешь узнать?",
        "menu_b2b": "Отлично! Что тебя интересует?",
        "guide": "Получить бесплатный гайд",
        "consult": "Записаться на консультацию",
        "courses": "Узнать о курсах",
        "channel": "Подписаться на канал",
        "guide_text": "Держи гайд «Скрытые триггеры старения» 👇",
        "consult_text": (
            "Записаться на индивидуальный разбор:\n\n"
            "📲 {}".format(CALENDLY_URL)
        ),
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
        "back_to_menu": "\n\nНапиши *меню* чтобы вернуться в главное меню.",
    },
    "ua": {
        "welcome": "Привіт! Я помічник Тетяни Чернишової 👋\n\nОбери що тебе цікавить:",
        "b2c": "Для себе — anti-age",
        "b2b": "Я косметолог",
        "menu_b2c": "Чудово! Що хочеш дізнатися?",
        "menu_b2b": "Чудово! Що тебе цікавить?",
        "guide": "Отримати безкоштовний гайд",
        "consult": "Записатися на консультацію",
        "courses": "Дізнатися про курси",
        "channel": "Підписатися на канал",
        "guide_text": "Тримай гайд «Приховані тригери старіння» 👇",
        "consult_text": (
            "Записатися на індивідуальний розбір:\n\n"
            "📲 {}".format(CALENDLY_URL)
        ),
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
        "channel_b2b_url": "https://t.me/chernyshova_b2b_ua",
        "channel_text": "📢 Підписатися на канал:\n\n{}",
        "back_to_menu": "\n\nНапиши *меню* щоб повернутися до головного меню.",
    },
    "en": {
        "welcome": "Hi! I'm Tatiana Chernyshova's assistant 👋\n\nWhat are you interested in?",
        "b2c": "Anti-age for myself",
        "b2b": "I'm a cosmetologist",
        "menu_b2c": "Great! What would you like to know?",
        "menu_b2b": "Great! What are you interested in?",
        "guide": "Get free guide",
        "consult": "Book a consultation",
        "courses": "Learn about courses",
        "channel": "Subscribe to channel",
        "guide_text": "Here's the guide «Hidden triggers of ageing» 👇",
        "consult_text": (
            "Book an individual consultation:\n\n"
            "📲 {}".format(CALENDLY_URL)
        ),
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
        "back_to_menu": "\n\nType *menu* to return to the main menu.",
    },
    "es": {
        "welcome": "¡Hola! Soy el asistente de Tatiana Chernyshova 👋\n\n¿Qué te interesa?",
        "b2c": "Anti-age para mí",
        "b2b": "Soy cosmetóloga",
        "menu_b2c": "¡Genial! ¿Qué quieres saber?",
        "menu_b2b": "¡Genial! ¿Qué te interesa?",
        "guide": "Obtener guía gratuita",
        "consult": "Reservar consulta",
        "courses": "Ver cursos",
        "channel": "Suscribirse al canal",
        "guide_text": "Aquí tienes la guía «Desencadenantes ocultos del envejecimiento» 👇",
        "consult_text": (
            "Reserva una consulta individual:\n\n"
            "📲 {}".format(CALENDLY_URL)
        ),
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
        "back_to_menu": "\n\nEscribe *menú* para volver al menú principal.",
    }
}


# === HELPERS ===

def get_state(phone):
    """Get or create user state."""
    if phone not in user_states:
        user_states[phone] = {"lang": None, "direction": None, "step": "lang"}
    return user_states[phone]


def send_message(to, body):
    """Send a plain text WhatsApp message."""
    client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=to,
        body=body
    )


def send_numbered_menu(to, body, options):
    """
    Send a menu as numbered text options.
    Most reliable approach — works immediately without Content API.
    Users reply with the number.
    """
    menu_text = body + "\n\n"
    for i, opt in enumerate(options, 1):
        menu_text += f"{i}. {opt['label']}\n"
    send_message(to, menu_text)


def send_pdf(to, pdf_url, caption=""):
    """Send a PDF document via WhatsApp."""
    client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=to,
        body=caption or "📄",
        media_url=[pdf_url]
    )


def get_pdf_url(lang):
    """Return the correct PDF URL based on language (UA gets Ukrainian, all others get RU)."""
    if lang == "ua" and PDF_URL_UA:
        return PDF_URL_UA
    return PDF_URL_RU


# === FLOW HANDLERS ===

def handle_lang_step(phone, user_input):
    """Process language choice."""
    state = get_state(phone)

    lang_map = {"1": "ru", "2": "ua", "3": "en", "4": "es"}
    text_map = {
        "русский": "ru", "ru": "ru", "рус": "ru",
        "українська": "ua", "ua": "ua", "укр": "ua",
        "english": "en", "en": "en", "eng": "en",
        "español": "es", "es": "es", "esp": "es",
    }

    choice = lang_map.get(user_input) or text_map.get(user_input.lower())

    if choice:
        state["lang"] = choice
        state["step"] = "direction"
        show_direction_menu(phone)
    else:
        show_lang_menu(phone)


def show_lang_menu(phone):
    """Send language selection menu."""
    send_numbered_menu(
        to=f"whatsapp:{phone}",
        body="Выберите язык / Оберіть мову / Choose language / Elige idioma:",
        options=[
            {"id": "ru", "label": "🇷🇺 Русский"},
            {"id": "ua", "label": "🇺🇦 Українська"},
            {"id": "en", "label": "🇬🇧 English"},
            {"id": "es", "label": "🇪🇸 Español"},
        ]
    )


def show_direction_menu(phone):
    """Send B2C/B2B direction menu."""
    state = get_state(phone)
    t = TEXTS[state["lang"]]
    send_numbered_menu(
        to=f"whatsapp:{phone}",
        body=t["welcome"],
        options=[
            {"id": "b2c", "label": f"💆‍♀️ {t['b2c']}"},
            {"id": "b2b", "label": f"💼 {t['b2b']}"},
        ]
    )


def handle_direction_step(phone, user_input):
    """Process direction choice."""
    state = get_state(phone)

    dir_map = {"1": "b2c", "2": "b2b"}
    text_map_b2c = {"b2c", "anti-age", "для себя", "для себе", "for myself", "para mí"}
    text_map_b2b = {"b2b", "косметолог", "cosmetologist", "cosmetóloga"}

    choice = dir_map.get(user_input)
    if not choice:
        lower = user_input.lower()
        if lower in text_map_b2c:
            choice = "b2c"
        elif lower in text_map_b2b:
            choice = "b2b"

    if choice:
        state["direction"] = choice
        state["step"] = "menu"
        show_main_menu(phone)
    else:
        show_direction_menu(phone)


def show_main_menu(phone):
    """Send the main action menu (4 options as numbered list)."""
    state = get_state(phone)
    t = TEXTS[state["lang"]]
    direction = state["direction"]
    menu_text = t["menu_b2c"] if direction == "b2c" else t["menu_b2b"]

    send_numbered_menu(
        to=f"whatsapp:{phone}",
        body=menu_text,
        options=[
            {"id": "guide",   "label": f"📄 {t['guide']}"},
            {"id": "consult", "label": f"📲 {t['consult']}"},
            {"id": "courses", "label": f"🎓 {t['courses']}"},
            {"id": "channel", "label": f"📢 {t['channel']}"},
        ]
    )


def handle_menu_step(phone, user_input):
    """Process main menu choice."""
    state = get_state(phone)
    lang = state["lang"]
    t = TEXTS[lang]
    direction = state["direction"]
    to = f"whatsapp:{phone}"

    action_map = {"1": "guide", "2": "consult", "3": "courses", "4": "channel"}
    text_map = {
        "гайд": "guide", "guide": "guide", "guía": "guide", "pdf": "guide",
        "консультация": "consult", "консультація": "consult",
        "consult": "consult", "consultation": "consult", "consulta": "consult",
        "курс": "courses", "courses": "courses", "cursos": "courses",
        "канал": "channel", "channel": "channel", "canal": "channel",
    }

    choice = action_map.get(user_input)
    if not choice:
        choice = text_map.get(user_input.lower())

    if choice == "guide":
        if direction == "b2c":
            pdf_url = get_pdf_url(lang)
            if pdf_url:
                send_pdf(to, pdf_url, t["guide_text"])
            else:
                send_message(to, t["guide_text"] + "\n\n⚠️ PDF временно недоступен / PDF temporarily unavailable.")
        else:
            send_message(to, t["guide_text"])
        send_message(to, t["back_to_menu"])

    elif choice == "consult":
        send_message(to, t["consult_text"] + t["back_to_menu"])

    elif choice == "courses":
        if direction == "b2c":
            send_message(to, t["courses_text_b2c"] + t["back_to_menu"])
        else:
            send_message(to, t["courses_text_b2b"] + t["back_to_menu"])

    elif choice == "channel":
        channel_url = t["channel_b2b_url"] if direction == "b2b" else t["channel_url"]
        send_message(to, t["channel_text"].format(channel_url) + t["back_to_menu"])

    else:
        show_main_menu(phone)


# === RESET / MENU COMMANDS ===

RESET_WORDS = {
    "start", "начать", "розпочати", "comenzar", "inicio",
    "menu", "меню", "menú",
    "restart", "reset", "заново",
    "hi", "hello", "привет", "привіт", "hola",
}


# === MAIN WEBHOOK ===

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages from Twilio."""
    from_number = request.values.get("From", "")       # "whatsapp:+34612345678"
    body = request.values.get("Body", "").strip()
    button_payload = request.values.get("ButtonPayload", "")

    phone = from_number.replace("whatsapp:", "")
    user_input = button_payload or body

    logging.info(f"Message from {phone}: {user_input}")

    # Check for reset/menu commands
    if user_input.lower() in RESET_WORDS:
        user_states.pop(phone, None)
        get_state(phone)
        show_lang_menu(phone)
        return "", 200

    state = get_state(phone)

    if state["step"] == "lang":
        handle_lang_step(phone, user_input)
    elif state["step"] == "direction":
        handle_direction_step(phone, user_input)
    elif state["step"] == "menu":
        handle_menu_step(phone, user_input)

    return "", 200


@app.route("/health", methods=["GET"])
def health():
    """Health check for Railway."""
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
