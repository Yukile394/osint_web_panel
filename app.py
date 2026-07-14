from flask import Flask, request, render_template, jsonify
import requests
import json
import hashlib
import phonenumbers
from phonenumbers import carrier, geocoder
import socket
import dns.resolver
import whois
from datetime import datetime
import re

app = Flask(__name__)

class OSINT_ENGINE:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    # ========== IP BİLGİLERİ ==========
    def ip_ara(self, ip):
        try:
            # IP konum ve ISP
            resp = self.session.get(f"http://ip-api.com/json/{ip}")
            if resp.status_code == 200:
                veri = resp.json()
                return {
                    "ip": ip,
                    "ulke": veri.get("country", "Bilinmiyor"),
                    "sehir": veri.get("city", "Bilinmiyor"),
                    "isp": veri.get("isp", "Bilinmiyor"),
                    "enlem": veri.get("lat", 0),
                    "boylam": veri.get("lon", 0),
                    "zaman_dilimi": veri.get("timezone", "Bilinmiyor")
                }
        except:
            pass
        return {"ip": ip, "hata": "IP bilgisi alınamadı"}

    # ========== DISCORD ID ==========
    def discord_ara(self, discord_id):
        try:
            # Discord ID'den tarih çıkarma (snowflake)
            timestamp = ((int(discord_id) >> 22) + 1420070400000) / 1000
            tarih = datetime.fromtimestamp(timestamp).isoformat()
            
            # Discord API üzerinden bilgi (public bilgiler)
            resp = self.session.get(f"https://discord.com/api/v9/users/{discord_id}")
            if resp.status_code == 200:
                veri = resp.json()
                return {
                    "id": discord_id,
                    "kullanici_adi": veri.get("username", "Bilinmiyor"),
                    "discriminator": veri.get("discriminator", "0000"),
                    "avatar": f"https://cdn.discordapp.com/avatars/{discord_id}/{veri.get('avatar', '')}.png",
                    "hesap_tarihi": tarih,
                    "bot_mu": veri.get("bot", False)
                }
            else:
                return {
                    "id": discord_id,
                    "hesap_tarihi": tarih,
                    "durum": "Profil gizli veya kullanıcı bulunamadı"
                }
        except:
            return {"id": discord_id, "hata": "Discord bilgisi alınamadı"}

    # ========== DOMAIN / WHOIS ==========
    def domain_ara(self, domain):
        try:
            w = whois.whois(domain)
            return {
                "domain": domain,
                "kayit_tarihi": str(w.creation_date),
                "son_kullanma": str(w.expiration_date),
                "kayitci": str(w.registrar),
                "name_servers": w.name_servers[:3] if w.name_servers else []
            }
        except:
            return {"domain": domain, "hata": "WHOIS bilgisi alınamadı"}

    # ========== TC KİMLİK (Örnek) ==========
    def tc_ara(self, ad, soyad, dogum_yili):
        tc_hash = hashlib.sha256(f"{ad}{soyad}{dogum_yili}".encode()).hexdigest()
        return f"{tc_hash[:3]}{tc_hash[3:6]}{tc_hash[6:9]}{tc_hash[9:11]}"

    # ========== TELEFON ==========
    def telefon_ara(self, numara):
        try:
            parsed = phonenumbers.parse(numara, "TR")
            return {
                "telefon": numara,
                "operator": carrier.name_for_number(parsed, "tr"),
                "konum": geocoder.description_for_number(parsed, "tr")
            }
        except:
            return {"telefon": numara, "hata": "Telefon bilgisi alınamadı"}

    # ========== E-POSTA SIZINTI ==========
    def eposta_sizinti(self, email):
        try:
            resp = self.session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}")
            if resp.status_code == 200:
                return [kayit["Name"] for kayit in resp.json()]
            else:
                return ["Sızıntı bulunamadı"]
        except:
            return ["API hatası"]

# =================== WEB ROTALARI ===================
engine = OSINT_ENGINE()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ip', methods=['POST'])
def api_ip():
    data = request.json
    ip = data.get('ip', '')
    return jsonify(engine.ip_ara(ip))

@app.route('/api/discord', methods=['POST'])
def api_discord():
    data = request.json
    discord_id = data.get('discord_id', '')
    return jsonify(engine.discord_ara(discord_id))

@app.route('/api/domain', methods=['POST'])
def api_domain():
    data = request.json
    domain = data.get('domain', '')
    return jsonify(engine.domain_ara(domain))

@app.route('/api/tc', methods=['POST'])
def api_tc():
    data = request.json
    ad = data.get('ad', '')
    soyad = data.get('soyad', '')
    dogum = data.get('dogum_yili', '1990')
    tc = engine.tc_ara(ad, soyad, dogum)
    return jsonify({"tc": tc})

@app.route('/api/telefon', methods=['POST'])
def api_telefon():
    data = request.json
    numara = data.get('telefon', '')
    return jsonify(engine.telefon_ara(numara))

@app.route('/api/email', methods=['POST'])
def api_email():
    data = request.json
    email = data.get('email', '')
    return jsonify({"sizintilar": engine.eposta_sizinti(email)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
