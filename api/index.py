import os, logging
from fastapi import FastAPI, Request, Header, HTTPException
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, CallbackQueryHandler
)

# ===== LOGGING =====
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s | %(message)s", level=logging.INFO)
log = logging.getLogger("mundovapo-bot")

# ===== ENV =====
TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mv-secret")

CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/+jS_YKiiHgcw3OTRh")
GROUP_URL   = os.getenv("GROUP_URL",   "https://t.me/+kL7eSPE27805ZGRh")
SORTEO_URL  = os.getenv("SORTEO_URL",  "https://www.mundovapo.cl")
FORM_URL    = os.getenv("FORM_URL",    "https://docs.google.com/forms/d/e/1FAIpQLSct9QIex5u95sdnaJdXDC4LeB-WBlcdhE7GXoUVh3YvTh_MlQ/viewform")
WHATSAPP_TXT= os.getenv("WHATSAPP_TXT","+56 9 9324 5860")
WHATSAPP_URL= os.getenv("WHATSAPP_URL","https://www.mundovapo.cl")  # cambia a wa.me cuando quieras

if not TOKEN:
    raise SystemExit("⚠️ Define BOT_TOKEN como variable de entorno.")

# ===== BOT APP (se construye una sola vez por instancia) =====
application = ApplicationBuilder().token(TOKEN).build()

# ===== TECLADOS =====
def kb_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 Canal", url=CHANNEL_URL),
         InlineKeyboardButton("💬 Chat",  url=GROUP_URL)],
        [InlineKeyboardButton("📋 Bases del sorteo", url=SORTEO_URL)],
        [InlineKeyboardButton("❓ Preguntas frecuentes", callback_data="faq_menu")],
        [InlineKeyboardButton("🟢📱 Atención por WhatsApp", url=WHATSAPP_URL)]
    ])

def kb_faq_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚚 Envíos", callback_data="faq_envios")],
        [InlineKeyboardButton("🛠️ Garantías", callback_data="faq_garantias")],
        [InlineKeyboardButton("⬅️ Volver al inicio", callback_data="faq_home")]
    ])

# ===== UTIL =====
async def safe_edit(cq, text, markup):
    try:
        await cq.edit_message_text(text, reply_markup=markup,
                                   disable_web_page_preview=True, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            await cq.answer("Ya estás en este menú.", show_alert=False)
        else:
            raise

def texto_bienvenida(nombre):
    return (
        f"👋 ¡Bienvenid@, {nombre}!\n\n"
        "Nos alegra mucho tenerte por aquí 🌿\n"
        "En plataformas como Instagram es muy difícil mantener una cuenta dedicada a vaporizadores, "
        "por eso decidimos crear esta comunidad exclusiva para quienes confían en nosotros 💚\n\n"
        "📣 <b>En el canal</b> podrás estar al tanto de:\n"
        "— Nuevos lanzamientos\n— Descuentos especiales\n— Sorteos mensuales\n— Y más\n\n"
        "💬 <b>En el chat</b> puedes resolver dudas y participar en una comunidad respetuosa (+18, sin spam).\n\n"
        "Gracias por tu compra 🤝 Ya estás participando en el sorteo mensual.\n"
        "Revisa las bases y formulario en el enlace 👇"
    )

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = (update.effective_user.first_name or "amig@") if update.effective_user else "amig@"
    await update.message.reply_text(
        texto_bienvenida(nombre),
        reply_markup=kb_principal(),
        disable_web_page_preview=True, parse_mode=ParseMode.HTML
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Aquí tienes el menú 👇",
        reply_markup=kb_principal(),
        disable_web_page_preview=True, parse_mode=ParseMode.HTML
    )

async def faq_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ <b>Preguntas frecuentes</b>\n\nSelecciona una categoría:",
        reply_markup=kb_faq_menu(),
        disable_web_page_preview=True, parse_mode=ParseMode.HTML
    )

async def faq_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    data = cq.data or "faq_menu"
    nombre = (cq.from_user.first_name or "amig@") if cq.from_user else "amig@"

    if data == "faq_home":
        await safe_edit(cq, texto_bienvenida(nombre), kb_principal()); return

    if data == "faq_menu":
        await safe_edit(cq, "❓ <b>Preguntas frecuentes</b>\n\nSelecciona una categoría:", kb_faq_menu()); return

    if data == "faq_envios":
        texto = (
            "✈️ <b>Envíos</b>\n\n"
            "Envíos a todo Chile por courier. Despacho en máximo 48 h hábiles.\n"
            "Al enviar, te llegará el tracking por correo.\n\n"
            f"📩 ¿No recibiste el tracking? Escríbenos por WhatsApp: {WHATSAPP_TXT}"
        )
        await safe_edit(cq, texto, kb_faq_menu()); return

    if data == "faq_garantias":
        texto = (
            "🛠️ <b>Garantías</b>\n\n"
            "Cada artículo tiene garantía original del fabricante (ver descripción del producto).\n\n"
            "No cubre daños por mal uso. Para evaluación, completa el formulario y espera respuesta (≤ 48 h hábiles):\n"
            f"🔗 <a href=\"{FORM_URL}\">Formulario de garantía</a>\n\n"
            "📬 Soporte: <a href=\"mailto:soporte@mundovapo.cl\">soporte@mundovapo.cl</a> o WhatsApp."
        )
        await safe_edit(cq, texto, kb_faq_menu()); return

# Registra handlers en la Application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help",  help_cmd))
application.add_handler(CommandHandler("faq",   faq_cmd))
application.add_handler(CallbackQueryHandler(faq_router, pattern="^faq"))

# ===== FASTAPI APP =====
app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/telegram")
async def telegram_update(request: Request,
                          x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    # Valida secret
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    update = Update.de_json(data, application.bot)

    # Stateless: inicializa, procesa el update, y cierra
    await application.initialize()
    try:
        await application.process_update(update)
    finally:
        await application.shutdown()

    return {"ok": True}


