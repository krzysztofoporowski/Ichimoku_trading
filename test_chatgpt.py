import yfinance as yf
import requests
from datetime import datetime, timedelta
import cachetools
import pandas as pd

# Ustawianie lat do cofnięcia na 1
years_ago = 1

# Obliczanie daty początku okresu
end_date = datetime.now()
start_date = end_date - timedelta(days=365*years_ago)

# Tworzenie cache
cache = cachetools.TTLCache(maxsize=500, ttl=8*60*60)

# Pobranie listy tickerów z witryny internetowej
url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
response = requests.get(url)
df_list = pd.read_html(response.text)
df = df_list[0]
ticker_list = df['Symbol'].tolist()

# Pobieranie danych historycznych dla każdej spółki
licznik = 0
for ticker in ticker_list:
    try:
        if ticker in cache:
            data = cache[ticker]
        else:
            data = yf.download(ticker, start=start_date, end=end_date,
                                progress=False)
            cache[ticker] = data
        data['SMA200'] = data['Close'].rolling(window=200).mean()
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        sma200 = data['SMA200'].iloc[-1]
        sma50 = data['SMA50'].iloc[-1]
        last_close = data['Close'].iloc[-1]
        if last_close > sma50 > sma200:
            #print(f'{ticker} SMA50 powyżej SMA200')
            licznik = licznik + 1
    except Exception as e:
        print(f'Błąd podczas pobierania danych dla spółki {ticker}: {e}')
print(f'{licznik} ma SAM50 powyżej SAM200')

'''
data['SMA50'] = data['Close'].rolling(window=50).mean()
data['SMA200'] = data['Close'].rolling(window=200).mean()
data = data[(data['SMA50'] > data['SMA200']) & (data['SMA50'].shift(1) < data['SMA200'].shift(1))]
print(data)
'''
    