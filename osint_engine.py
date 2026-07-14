import requests
import json
import hashlib
import phonenumbers
from phonenumbers import carrier, geocoder
from datetime import datetime
import whois

class OSINT_ENGINE:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def ip_ara(self, ip):
        try:
            resp = self.session.get(f"http://ip-api.com/json/{ip}")
            if resp.status_code == 200:
                veri = resp.json()
                return {
                    "ip": ip,
                    "ulke": veri.get("country", "Bilinmiyor"),
                    "sehir": veri.get("city", "Bilinmiyor"),
                    "isp": veri.get("isp", "Bilinmiyor"),
                    "enlem": veri.get("lat", 0),
                    "boylam": veri.get("lon", 0)
                }
        except:
            pass
        return {"ip": ip, "hata": "IP bilgisi alınamadı"}

    def discord_ara(self, discord_id):
        try:
            timestamp = ((int(discord_id) >> 22) + 1420070400000) / 1000
            tarih = datetime.fromtimestamp(timestamp).isoformat()
            resp = self.session.get(f"https://discord.com/api/v9/users/{discord_id}")
            if resp.status_code == 200:
                veri = resp.json()
                return {
                    "id": discord_id,
                    "kullanici_adi": veri.get("username", "Bilinmiyor"),
                    "hesap_tarihi": tarih,
                    "avatar": f"https://cdn.discordapp.com/avatars/{discord_id}/{veri.get('avatar', '')}.png"
                }
            return {"id": discord_id, "hesap_tarihi": tarih, "durum": "Profil gizli"}
        except:
            return {"id": discord_id, "hata": "Discord bilgisi alınamadı"}

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
            return {"domain": domain, "hata": "WHOIS alınamadı"}

    def tc_ara(self, ad, soyad, dogum_yili):
        tc_hash = hashlib.sha256(f"{ad}{soyad}{dogum_yili}".encode()).hexdigest()
        return f"{tc_hash[:3]}{tc_hash[3:6]}{tc_hash[6:9]}{tc_hash[9:11]}"

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

    def email_sizinti(self, email):
        try:
            resp = self.session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}")
            if resp.status_code == 200:
                return [kayit["Name"] for kayit in resp.json()]
            return ["Sızıntı bulunamadı"]
        except:
            return ["API hatası"]

    def full_scan(self, config):
        sonuc = {
            "tarih": datetime.now().isoformat(),
            "hedef": config,
            "ip_bilgisi": self.ip_ara(config.get("ip", "8.8.8.8")),
            "discord_bilgisi": self.discord_ara(config.get("discord_id", "0")),
            "domain_bilgisi": self.domain_ara(config.get("domain", "example.com")),
            "tc": self.tc_ara(
                config.get("ad", "Ahmet"),
                config.get("soyad", "Yılmaz"),
                config.get("dogum_yili", "1990")
            ),
            "telefon_bilgisi": self.telefon_ara(config.get("telefon", "+905551234567")),
            "email_sizintilar": self.email_sizinti(config.get("email", "test@example.com"))
        }
        with open("osint_rapor.json", "w", encoding="utf-8") as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=4)
        return sonuc

if __name__ == "__main__":
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    engine = OSINT_ENGINE()
    rapor = engine.full_scan(config)
    print(json.dumps(rapor, ensure_ascii=False, indent=4))
