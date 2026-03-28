import os
import pandas as pd
from datetime import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = os.getenv("TOKEN")

FILE = "pedidos.csv"

if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["usuario", "pedido", "fecha"])
    df.to_csv(FILE, index=False)


app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()


# ======================
# COMANDO /pedido
# ======================

async def pedido(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usuario = update.message.from_user.username or update.message.from_user.first_name
    texto = " ".join(context.args)

    if texto == "":
        await update.message.reply_text("Escribe artista o link después del comando")
        return

    df = pd.read_csv(FILE)

    coincidencias = df[df["pedido"].str.lower() == texto.lower()]

    if not coincidencias.empty:

        usuarios = coincidencias["usuario"].tolist()

        await update.message.reply_text(
            "Este pedido ya fue solicitado por:\n" +
            "\n".join(usuarios)
        )

    nueva_fila = {
        "usuario": usuario,
        "pedido": texto,
        "fecha": datetime.now()
    }

    df = pd.concat([df, pd.DataFrame([nueva_fila])])
    df.to_csv(FILE, index=False)

    await update.message.reply_text("Pedido registrado correctamente")


# ======================
# COMANDO /ranking
# ======================

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = pd.read_csv(FILE)

    ranking = df["usuario"].value_counts()

    texto = "Ranking de solicitantes:\n\n"

    for i, (user, cantidad) in enumerate(ranking.items(), 1):

        texto += f"{i}. {user} – {cantidad}\n"

    await update.message.reply_text(texto)


telegram_app.add_handler(CommandHandler("pedido", pedido))
telegram_app.add_handler(CommandHandler("ranking", ranking))


# ======================
# LOOP GLOBAL
# ======================

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


async def start_bot():
    await telegram_app.initialize()
    await telegram_app.start()


loop.run_until_complete(start_bot())


# ======================
# WEBHOOK ENDPOINT
# ======================

@app.route("/", methods=["POST"])
def webhook():

    json_data = request.get_json(force=True)

    update = Update.de_json(json_data, telegram_app.bot)

    loop.run_until_complete(
        telegram_app.process_update(update)
    )

    return "ok"


@app.route("/", methods=["GET"])
def home():
    return "Bot activo 🚀"


# ======================
# RUN SERVER
# ======================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
