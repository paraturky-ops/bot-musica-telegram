import os
import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
import threading
import asyncio


TOKEN = os.getenv("TOKEN")

FILE = "pedidos.csv"

if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["usuario", "pedido", "fecha"])
    df.to_csv(FILE, index=False)


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


async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = pd.read_csv(FILE)

    ranking = df["usuario"].value_counts()

    texto = "Ranking de solicitantes:\n\n"

    for i, (user, cantidad) in enumerate(ranking.items(), 1):
        texto += f"{i}. {user} – {cantidad}\n"

    await update.message.reply_text(texto)


# =============================
# FLASK KEEP ALIVE SERVER
# =============================

web = Flask(__name__)


@web.route("/")
def home():
    return "Bot activo 24/7"


def run_flask():
    web.run(host="0.0.0.0", port=10000)


# =============================
# TELEGRAM BOT START
# =============================

async def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("pedido", pedido))
    app.add_handler(CommandHandler("ranking", ranking))

    print("Bot iniciado correctamente")
    print("Polling updates...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


# =============================
# START BOTH SERVICES
# =============================

if __name__ == "__main__":

    # iniciar flask en segundo plano
    threading.Thread(target=run_flask).start()

    # iniciar telegram en hilo principal
    asyncio.run(main())
