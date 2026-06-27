import os
import time
import requests
import telebot
import threading
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from flask import Flask

# =====================================================================
# 🪖 CONFIGURATION DU RANGER
# =====================================================================
API_SPORTS_KEY = "4eda851ae21c8246a93fe0032bdbb36a"
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
CHALLENGER_CHAT_ID = "7492611827"

BANKROLL_TOTALE = 20000  
POURCENTAGE_MISE = 0.05  

bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {"x-apisports-key": API_SPORTS_KEY}

app = Flask('')

@app.route('/')
def home():
    return "Bot du Ranger est en ligne 24h/24 avec IA !"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def calculer_mise(cote_estimee=1.80):
    return int(BANKROLL_TOTALE * POURCENTAGE_MISE)

# =====================================================================
# 🧠 ENTRAÎNEMENT DE L'IA (Au démarrage du serveur)
# =====================================================================
print("⚙️ Démarrage de l'entraînement de l'IA...")
# Historique des entraînements : [Buts marqués, Buts encaissés]
X_train = np.array([
    [2.8, 2.4], [0.6, 0.8], [3.0, 0.5], [1.0, 2.2], 
    [2.1, 0.6], [0.5, 1.5]
])
# Résultats réels : 1 = Victoire, 0 = Nul/Défaite
y_train = np.array([1, 0, 1, 0, 1, 0])

modele_ia = RandomForestClassifier(random_state=42)
modele_ia.fit(X_train, y_train)
print("✅ Entraînement terminé ! L'IA est opérationnelle.")

# =====================================================================
# 🤖 NOUVELLE FONCTION : ANALYSE PAR L'IA
# =====================================================================
def analyser_avec_ia():
    print("🧠 Analyse IA lancée...")
    date_aujourdhui = time.strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={date_aujourdhui}"

    try:
        response = requests.get(url, headers=HEADERS).json()
        matchs = response.get("response", [])

        if not matchs:
            bot.send_message(CHALLENGER_CHAT_ID, "📡 Calendrier vide pour l'IA aujourd'hui.")
            return

        compteur_ia = 0
        for match in matchs:
            if compteur_ia >= 3: # On limite à 3 matchs pour le test IA
                break

            status = match["fixture"]["status"]["short"]
            if status != "NS":
                continue

            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]

            # ⚠️ SIMULATION DES STATS POUR LE TEST
            # Plus tard, nous extrairons ces stats directement de l'API
            buts_marques_estimes = round(np.random.uniform(0.5, 3.0), 1)
            buts_encaisses_estimes = round(np.random.uniform(0.5, 2.5), 1)

            # L'IA fait sa prédiction
            match_stats = np.array([[buts_marques_estimes, buts_encaisses_estimes]])
            prediction = modele_ia.predict(match_stats)

            if prediction[0] == 1:
                msg_ia = f"🤖 **PRÉDICTION IA (Ranger V2)** 🤖\n\n⚽ `{home}` vs `{away}`\n🎯 **Verdict IA :** Victoire Domicile détectée\n📊 Stats analysées : {buts_marques_estimes} BM / {buts_encaisses_estimes} BE\n💰 **Mise :** {calculer_mise()} CFA"
                bot.send_message(CHALLENGER_CHAT_ID, msg_ia, parse_mode="Markdown")
                compteur_ia += 1
                time.sleep(2) # Pause radio pour Telegram

        if compteur_ia == 0:
            bot.send_message(CHALLENGER_CHAT_ID, "🛑 L'IA n'a trouvé aucune victoire sûre pour le moment.")

    except Exception as e:
        bot.send_message(CHALLENGER_CHAT_ID, f"❌ Erreur IA : {e}")

# =====================================================================
# 📊 ANALYSE COMPLÈTE (AVANT-MATCH) : STRATÉGIE API CLASSIQUE
# =====================================================================
def analyser_matchs_du_jour():
    print("📊 Analyse multi-stratégies lancée...")
    date_aujourdhui = time.strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={date_aujourdhui}"

    try:
        response = requests.get(url, headers=HEADERS).json()
        matchs = response.get("response", [])

        if not matchs:
            bot.send_message(CHALLENGER_CHAT_ID, "📡 Le calendrier de l'API n'est pas encore synchronisé pour aujourd'hui. Réessaie d'ici 1 ou 2 heures ! ⏳")
            return

        compteur_analyses = 0
        for match in matchs:
            if compteur_analyses >= 10:
                break

            status = match["fixture"]["status"]["short"]
            if status != "NS":
                continue

            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]
            match_id = match["fixture"]["id"]

            pred_url = f"https://v3.football.api-sports.io/predictions?fixture={match_id}"
            pred_res = requests.get(pred_url, headers=HEADERS).json()

            if pred_res.get("response"):
                data = pred_res["response"][0]
                distrib = data["predictions"]["percent"]
                home_pct = int(distrib["home"].replace("%", "")) if distrib["home"] else 0
                away_pct = int(distrib["away"].replace("%", "")) if distrib["away"] else 0
                
                # 1. STRATÉGIE VICTOIRE
                if home_pct > 70:
                    bot.send_message(CHALLENGER_CHAT_ID, f"🏆 **PROSPECT VICTOIRE** 🏆\n\n⚽ `{home}` vs `{away}`\n🎯 **Option :** Victoire de {home}\n📈 **Confiance API :** {home_pct}%\n💰 **Mise :** {calculer_mise()} CFA", parse_mode="Markdown")
                    compteur_analyses += 1
                elif away_pct > 70:
                    bot.send_message(CHALLENGER_CHAT_ID, f"🏆 **PROSPECT VICTOIRE** 🏆\n\n⚽ `{home}` vs `{away}`\n🎯 **Option :** Victoire de {away}\n📈 **Confiance API :** {away_pct}%\n💰 **Mise :** {calculer_mise()} CFA", parse_mode="Markdown")
                    compteur_analyses += 1

                # 2. STRATÉGIE LES DEUX ÉQUIPES MARQUENT (BTTS)
                btts_advice = data["predictions"]["advice"]
                if btts_advice and ("GG" in btts_advice or "both teams to score" in btts_advice.lower()):
                    bot.send_message(CHALLENGER_CHAT_ID, f"🔥 **PROSPECT LES 2 MARQUENT** 🔥\n\n⚽ `{home}` vs `{away}`\n🎯 **Option :** Les deux équipes vont marquer (Oui)\n💡 **Indicateur :** Attaques performantes.\n💰 **Mise :** {calculer_mise()} CFA", parse_mode="Markdown")
                    compteur_analyses += 1

        if compteur_analyses == 0:
            bot.send_message(CHALLENGER_CHAT_ID, "📋 Aucun match ne coche nos critères stricts de confiance (>70%) dans les premières lignes du calendrier pour le moment.")

    except Exception as e:
        bot.send_message(CHALLENGER_CHAT_ID, f"❌ Erreur technique lors de l'analyse : {e}")

# =====================================================================
# 🚨 SURVEILLANCE LIVE
# =====================================================================
def scanner_les_matchs_live():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    try:
        response = requests.get(url, headers=HEADERS).json()
        matchs_live = response.get("response", [])

        for match in matchs_live:
            temps = match["fixture"]["status"]["elapsed"]
            score_home = match["goals"]["home"]
            score_away = match["goals"]["away"]
            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]

            if temps >= 70 and score_home == 0 and score_away == 0:
                msg_live = f"🚨 **RADAR LIVE : BUT IMMINENT** 🚨\n\n⚽ `{home}` 0 - 0 `{away}`\n⏱️ **Minute :** {temps}'\n🔥 **Option :** Plus de 0,5 buts d'ici la fin\n💸 **Mise :** {calculer_mise()} CFA"
                bot.send_message(CHALLENGER_CHAT_ID, msg_live, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Erreur Scan Live : {e}")

# =====================================================================
# 🗣️ COMMANDES RECEPTION TELEGRAM
# =====================================================================
@bot.message_handler(commands=['matchs'])
def repondre_demande_matchs(message):
    bot.reply_to(message, "🪖 Reçu ! Le Ranger interroge le calendrier (Stratégie API)... 🔍")
    threading.Thread(target=analyser_matchs_du_jour).start()

@bot.message_handler(commands=['ia'])
def repondre_demande_ia(message):
    bot.reply_to(message, "🧠 Le Cerveau IA du Ranger prend le relais. Analyse en cours... ⚡")
    threading.Thread(target=analyser_avec_ia).start()

# =====================================================================
# 🚀 DEMARRAGE
# =====================================================================
if __name__ == "__main__":
    bot.remove_webhook()
    t_web = threading.Thread(target=run_web_server)
    t_web.daemon = True
    t_web.start()

    bot_thread = threading.Thread(target=bot.infinity_polling)
    bot_thread.daemon = True
    bot_thread.start()

    while True:
        scanner_les_matchs_live()
        time.sleep(300)
