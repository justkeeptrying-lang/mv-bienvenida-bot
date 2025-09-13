import os
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# Variables de entorno (debes poner TOKEN en Settings → Environment Variables de Vercel)
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise RuntimeError("Falta la variable de entorno TOKEN")

CHANNEL_URL  = os.environ.get("CHANNEL_URL", "https://t.me/+jS_YKiiHgcw3OTRh")
GROUP_URL    = os.environ.get("GROUP_URL", "https://t.me/+kL7eSPE27805ZGRh")
SORTEO_URL   = os.environ.get("SORTEO_URL", "https://www.mundovapo.cl")
FORM_URL     = os.environ.get("FORM_URL", "https://docs.google.com/forms/d/e/1FAIpQLSct9QIex5u95sdnaJdXDC4LeB-WBlcdhE7GXoUVh3YvTh_MlQ/viewform")
WHATSAPP_URL = os.environ.get("WHATSAPP_URL", "https://www.mundovapo.cl")
WHATSAPP_TXT = os.environ.get("WHATSAPP_TXT", "+56 9 9324 5860")

# Inicializar FastAPI y el bot
app = FastAPI()
application: Application = ApplicationBuilder().token(TOKEN).build()

# --- Teclados ---
def kb_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 Canal", url=CHANNEL_URL),
         InlineKeyboardButton("💬 Chat", url=GROUP_URL)],
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

# --- Texto bienvenida ---
def texto_bienvenida(nombre: str):
    return (
        f"👋 ¡Bienvenid@, {nombre}!\\n\\n"
        "Nos alegra mucho tenerte por aquí 🌿\\n"
        "En Instagram es difícil llevar una cuenta de vaporizadores, "
        "por eso creamos esta comunidad para quienes confían en nosotros 💚\\n\\n"
        "📣 <b>En el canal</b>:\\n— Nuevos lanzamientos\\n— Descuentos especiales\\n— Sorteos mensuales\\n— Y más\\n\\n"
        "💬 <b>En el chat</b>:\\nResuelve dudas y participa en una comunidad respetuosa (+18, sin spam).\\n\\n"
        "Gracias por tu compra 🤝 Ya estás participando en el sorteo mensual.\\n"
        "Revisa las bases y formulario en el enlace 👇"
    )

# --- Handlers del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name or "amig@"
    await update.message.reply_text(
        texto_bienvenida(nombre),
        reply_markup=kb_principal(),
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )

async def faq_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    data = cq.data or "faq_menu"
    nombre = cq.from_user.first_name or "amig@"

    if data == "faq_home":
        await cq.edit_message_text(texto_bienvenida(nombre),
                                   reply_markup=kb_principal(),
                                   parse_mode=ParseMode.HTML)
        return

    if data == "faq_menu":
        await cq.edit_message_text("❓ <b>Preguntas frecuentes</b>\\n\\nSelecciona una categoría:",
                                   reply_markup=kb_faq_menu(),
                                   parse_mode=ParseMode.HTML)
        return

    if data == "faq_envios":
        await cq.edit_message_text(
            "✈️ <b>Envíos</b>\\n\\n"
            "Envíos a todo Chile por courier. Despacho en máx. 48 h hábiles.\\n"
            "Al enviar, te llegará el tracking por correo.\\n\\n"
            f"📩 ¿No recibiste el tracking? Escríbenos por WhatsApp: {WHATSAPP_TXT}",
            reply_markup=kb_faq_menu(),
            parse_mode=ParseMode.HTML
        )
        return

    if data == "faq_garantias":
        await cq.edit_message_text(
            "🛠️ <b>Garantías</b>\\n\\n"
            "Cada artículo tiene garantía original del fabricante (ver descripción del producto).\\n\\n"
            "No cubre daños por mal uso. Para evaluación, completa el formulario (≤ 48 h hábiles):\\n"
            f"🔗 <a href=\\"{FORM_URL}\\">Formulario de garantía</a>\\n\\n"
            "📬 Soporte: soporte@mundovapo.cl o WhatsApp.",
            reply_markup=kb_faq_menu(),
            parse_mode=ParseMode.HTML
        )
        return

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(faq_router, pattern="^faq"))

# --- Rutas HTTP de FastAPI ---
@app.get("/")
async def root():
    return {"ok": True, "service": "mundovapo-bot (webhook vercel)"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)

    if not application.running:
        await application.initialize()

    await application.process_update(update)
    return {"ok": True}
