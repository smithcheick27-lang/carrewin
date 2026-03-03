import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Ton TOKEN Telegram (mettre en variable d'environnement)
TOKEN = os.getenv("TOKEN")
DATA_FILE = "stats.json"

sequence_active = False
observed_cards = []
signal_active = False
tentatives = 0

# Charger les stats
def load_stats():
    if not os.path.exists(DATA_FILE):
        return {"wins": 0, "losses": 0, "month": datetime.now().month}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Sauvegarder les stats
def save_stats(stats):
    with open(DATA_FILE, "w") as f:
        json.dump(stats, f)

# Fonction principale
async def analyser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sequence_active, observed_cards, signal_active, tentatives
    
    message = update.message.text
    stats = load_stats()
    current_month = datetime.now().month
    
    # Nouveau mois ?
    if stats["month"] != current_month:
        total = stats["wins"] + stats["losses"]
        rate = (stats["wins"] / total * 100) if total > 0 else 0
        
        await update.message.reply_text(
            f"📊 BILAN MENSUEL VIP\n\n"
            f"TOTAL SIGNAUX : {total}\n"
            f"GAGNÉS : {stats['wins']}\n"
            f"PERDUS : {stats['losses']}\n"
            f"TAUX DE RÉUSSITE : {rate:.2f} %"
        )
        
        stats = {"wins": 0, "losses": 0, "month": current_month}
        save_stats(stats)

    # Début de séquence si numéro finissant par 0
    if message.isdigit() and message.endswith("0"):
        sequence_active = True
        observed_cards = []
        return

    # Observation des 5 coups
    if sequence_active and not signal_active:
        observed_cards.append(message)
        if len(observed_cards) == 5:
            if "♦" not in "".join(observed_cards):
                await update.message.reply_text(
                    "💎 SNIPER SIGNAL 💎\n"
                    "PRÉDICTION : ♦ CARREAU\n"
                    "STRATÉGIE : Série Absence x5\n"
                    "COUP : ENTRÉE IMMÉDIATE\n"
                    "⚠️ 1 RATTRAPAGE AUTORISÉ"
                )
                signal_active = True
                tentatives = 0
            sequence_active = False

    # Gestion du signal + rattrapage
    if signal_active:
        tentatives += 1
        if "♦" in message:
            stats["wins"] += 1
            save_stats(stats)
            await update.message.reply_text("✅ SIGNAL VALIDÉ : GAGNÉ ✔️")
            signal_active = False
        elif tentatives == 2:
            stats["losses"] += 1
            save_stats(stats)
            await update.message.reply_text("❌ SIGNAL CLÔTURÉ : PERDU")
            signal_active = False

# Lancer le bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, analyser))
app.run_polling()
