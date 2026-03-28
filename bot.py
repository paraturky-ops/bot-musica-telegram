import os
import pandas as pd
from datetime import datetime
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(TOKEN)
app = Flask(__name__)

FILE = "pedidos.csv"

if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["usuario", "pedido", "fecha"])
    df.to_csv(FILE, index=False)


# ==========================
# COMANDO /pedido
# ==========================

async def pedido(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usuario = (
        update.message.from_user.username
        or update.message.from_user.first_name
    )

    texto = " ".join(context.args)

    if texto == "":
        await update.message.reply_text(
            "Escribe artista o link después del comando"
        )
        return

    df = pd.read_csv(FILE)

    coincidencias = df[
        df["pedido"].str.lower() == texto.lower()
    ]

    if not coincidencias.empty:

        usuarios = coincidencias["usuario"].tolist()

        await update.message.reply_text(
            "Este pedido ya fue solicitado por:\n"
            + "\n".join(usuarios)
        )

    nueva_fila = {
        "usuario": usuario,
        "pedido": texto,
        "fecha": datetime.now(),
    }

    df = pd.concat([df, pd.DataFrame([nueva_fila])])

    df.to_csv(FILE, index=False)

    await update.message.reply_text(
        "Pedido registrado correctamente"
    )


# ==========================
# COMANDO /ranking
# ==========================

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = pd.read_csv(FILE)

    ranking = df["usuario"].value_counts()

    texto = "Ranking de solicitantes:\n\n"

    for i, (user, cantidad) in enumerate(
        ranking.items(), start=1
    ):
        texto += f"{i}. {user} – {cantidad}\n"

    await update.message.reply_text(texto)


# ==========================
# TELEGRAM APP
# ==========================

telegram_app = Application.builder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("pedido", pedido))
telegram_app.add_handler(CommandHandler("ranking", ranking))


# ==========================
# WEBHOOK ENDPOINT
# ==========================

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    await telegram_app.initialize()
    await telegram_app.process_update(update)

    return "ok"


# ==========================
# HOME CHECK
# ==========================

@app.route("/")
def home():
    return "Bot activo 24/7"


# ==========================
# ARRANQUE
# ==========================

if __name__ == "__main__":

    import asyncio

    async def setup():
        await telegram_app.initialize()
        await bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

    asyncio.run(setup())

    app.run(host="0.0.0.0", port=10000)
