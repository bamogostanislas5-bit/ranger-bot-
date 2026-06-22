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
# 🗣️ COMMANDE RECEPTION TELEGRAM
# =====================================================================
@bot.message_handler(commands=['matchs'])
def repondre_demande_matchs(message):
    bot.reply_to(message, "🪖 Reçu ! Le Ranger interroge le calendrier du jour... 🔍")
    threading.Thread(target=analyser_matchs_du_jour).start()

# =====================================================================
# 🚀 DEMARRAGE
# =====================================================================
if __name__ == "__main__":
    t_web = threading.Thread(target=run_web_server)
    t_web.daemon = True
    t_web.start()

    bot_thread = threading.Thread(target=bot.infinity_polling)
    bot_thread.daemon = True
    bot_thread.start()

    while True:
        scanner_les_matchs_live()
        time.sleep(300)    
