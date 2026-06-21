import time
import requests
import telebot
import threading
from flask import Flask

# =====================================================================
# 🪖 CONFIGURATION DU RANGER
# =====================================================================
API_SPORTS_KEY = "4eda851ae21c8246a93fe0032bdbb36a"
TELEGRAM_TOKEN = "8504686138:AAEfn0qkyfipB7tYhndv9cvjKn-NkGIb4Ms"
CHALLENGER_CHAT_ID = "7492611827"

BANKROLL_TOTALE = 20000  
POURCENTAGE_MISE = 0.05  

bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {"x-apisports-key": API_SPORTS_KEY}

# Mini serveur Web pour maintenir Render éveillé
app = Flask('')

@app.route('/')
def home():
    return "Bot du Ranger est en ligne 24h/24 !"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def calculer_mise(cote_estimee=1.80):
    return int(BANKROLL_TOTALE * POURCENTAGE_MISE)

# =====================================================================
# 📊 ANALYSE COMPLÈTE (AVANT-MATCH) : MULTI-OPTIONS
# =====================================================================
def analyser_matchs_du_jour():
    print("📊 Analyse multi-stratégies du calendrier...")
    date_aujourdhui = time.strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={date_aujourdhui}"

    try:
        response = requests.get(url, headers=HEADERS).json()
        matchs = response.get("response", [])

        if not matchs:
            bot.send_message(CHALLENGER_CHAT_ID, "📡 Aucun match majeur aujourd'hui.")
            return

        for match in matchs[:8]:
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
                elif away_pct > 70:
                    bot.send_message(CHALLENGER_CHAT_ID, f"🏆 **PROSPECT VICTOIRE** 🏆\n\n⚽ `{home}` vs `{away}`\n🎯 **Option :** Victoire de {away}\n📈 **Confiance API :** {away_pct}%\n💰 **Mise :** {calculer_mise()} CFA", parse_mode="Markdown")

                # 2. STRATÉGIE LES DEUX ÉQUIPES MARQUENT (BTTS)
                btts_advice = data["predictions"]["advice"]
                if btts_advice and ("GG" in btts_advice or "both teams to score" in btts_advice.lower()):
                    bot.send_message(CHALLENGER_CHAT_ID, f"🔥 **PROSPECT LES 2 MARQUENT** 🔥\n\n⚽ `{home}` vs `{away}`\n🎯 **Option :** Les deux équipes vont marquer (Oui)\n💡 **Indicateur :** Attaques performantes.\n💰 **Mise :** {calculer_mise()} CFA", parse_mode="Markdown")

                # 3. STRATÉGIE CORNERS
                if data["teams"]["home"]["league"] and "goals" in data["teams"]["home"]:
                    if btts_advice and "over 2.5" in btts_advice.lower():
                        bot.send_message(CHALLENGER_CHAT_ID, f"📐 **PROSPECT CORNERS** 📐\n\n⚽ `{home}` vs `{away}`\n🎯 **Option :** Plus de 8,5 Corners\n📊 **Style :** Équipes offensives\n💰 **Mise :** {calculer_mise()} CFA", parse_mode="Markdown")

                # 4. STRATÉGIE CARTONS
                if btts_advice and ("derby" in btts_advice.lower() or home_pct == away_pct):
                    bot.send_message(CHALLENGER_CHAT_ID, f"🟨 **PROSPECT CARTONS** 🟨\n\n⚽ `{home}` vs `{away}`\n🎯 **Option :** Plus de 3,5 Cartons Jaunes\n⚠️ **Contexte :** Match tendu / Équilibres serrés\n💰 **Mise :** {calculer_mise()} CFA", parse_mode="Markdown")
                
                time.sleep(1)
    except Exception as e:
        print(f"❌ Erreur analyse : {e}")

# =====================================================================
# 🚨 SURVEILLANCE LIVE
# =====================================================================
def scanner_les_matchs_live():
    print("📡 Patrouille Live en cours...")
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

            # Stratégie 70ème minute à 0-0
            if temps >= 70 and score_home == 0 and score_away == 0:
                msg_live = f"🚨 **RADAR LIVE : BUT IMMINENT** 🚨\n\n⚽ `{home}` 0 - 0 `{away}`\n⏱️ **Minute :** {temps}'\n🔥 **Option :** Plus de 0,5 buts d'ici la fin\n💸 **Mise :** {calculer_mise()} CFA"
                bot.send_message(CHALLENGER_CHAT_ID, msg_live, parse_mode="Markdown")

    except Exception as e:
        print(f"❌ Erreur Scan Live : {e}")

# =====================================================================
# 🗣️ COMMANDE RECEPTION TELEGRAM
# =====================================================================
@bot.message_handler(commands=['matchs'])
def repondre_demande_matchs(message):
    bot.reply_to(message, "🪖 Reçu ! Analyse générale lancée (Victoires, Les 2 marquent, Corners, Cartons)... 🔍")
    analyser_matchs_du_jour()

# =====================================================================
# 🚀 DEMARRAGE
# =====================================================================
if __name__ == "__main__":
    print("🪖 Bot Multi-Stratégies en cours de déploiement Web...")
    
    # 1. Lancer le mini-serveur Web pour Render
    t_web = threading.Thread(target=run_web_server)
    t_web.daemon = True
    t_web.start()

    # 2. Lancer l'écoute Telegram
    bot_thread = threading.Thread(target=bot.infinity_polling)
    bot_thread.daemon = True
    bot_thread.start()

    # 3. Boucle Patrouille Live (Toutes les 5 minutes)
    while True:
        scanner_les_matchs_live()
        time.sleep(300)
