import math


import requests
from datetime import datetime

class PricingService:
    _rates_cache = {}
    _last_fetch_date = None

    @classmethod
    def update_exchange_rates(cls):
        today = datetime.now().date()
        if cls._rates_cache and cls._last_fetch_date == today:
            return

        try:
            url = "https://open.er-api.com/v6/latest/USD"
            headers = {"User-Agent": "MyMTGApp/1.0"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                
                cls._rates_cache = {
                    "EUR": rates.get("EUR", 0.92),
                    "RSD": rates.get("RSD", 117.0)
                }
                cls._last_fetch_date = today
                print(f"Uspešno učitani kursevi valuta: {cls._rates_cache}")
            else:
                print(f"Greška pri preuzimanju kurseva, status: {response.status_code}")
        except Exception as e:
            print(f"Izuzetak pri povezivanju sa API-jem za kurseve: {e}")
            if not cls._rates_cache:
                cls._rates_cache = {"EUR": 0.92, "RSD": 117.0}

    @classmethod
    def convert_price(cls, price_usd: float) -> tuple[float, float]:
       
        cls.update_exchange_rates()
        
        eur_rate = cls._rates_cache.get("EUR", 0.92)  # 1 USD prema EUR
        rsd_rate = cls._rates_cache.get("RSD", 117.0) # 1 USD prema RSD

        if not price_usd or price_usd <= 0:
            return 0.0, 0.0


        price_eur = price_usd * eur_rate

        eur_to_rsd_rate = rsd_rate / eur_rate if eur_rate > 0 else 117.0
        price_rsd = price_eur * eur_to_rsd_rate

        return round(price_eur, 2), round(price_rsd, 2)



import math
from services.pricing import PricingService

def calculate_card_price_rsd(price_eur: float) -> int:
    if price_eur is None or price_eur <= 0:
        return 0

    PricingService.update_exchange_rates()
    eur_rate = PricingService._rates_cache.get("EUR", 0.92)
    rsd_rate = PricingService._rates_cache.get("RSD", 117.0)
    
    effective_exchange_rate = rsd_rate / eur_rate if eur_rate > 0 else 117.0

    if price_eur < 0.35:
        return 50
    elif price_eur < 2.00:
        raw_price = price_eur * effective_exchange_rate + 15
    elif price_eur < 5.00:
        raw_price = price_eur * effective_exchange_rate + 30
    elif price_eur < 10.00:
        raw_price = price_eur * effective_exchange_rate + 60
    elif price_eur < 25.00:
        raw_price = price_eur * effective_exchange_rate * 1.10
    elif price_eur < 50.00:
        raw_price = price_eur * effective_exchange_rate * 1.07
    elif price_eur < 100.00:
        raw_price = price_eur * effective_exchange_rate * 1.05
    else:
        raw_price = price_eur * effective_exchange_rate * 1.03

    return math.ceil(raw_price / 10.0) * 10