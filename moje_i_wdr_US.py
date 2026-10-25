# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 19:48:17 2019

@author: krzysztof.oporowski
"""

from cmath import nan
from datetime import timedelta, datetime, date
import sys

#from WSEDataReader.wsedatareader import get_yahoo_date
sys.path.append('c:/Users/krzysiu/python/SimTradeSim')
sys.path.append('c:/Users/krzysiu/python/WSEDataReader')
sys.path.append('c:/Users/krzysiu/python/misctradingtools')
import warnings
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from bs4 import BeautifulSoup
from talib import ATR
from cachetools import cached, TTLCache
from SimTradeSim import Budget, Transaction, define_gl
from wsedatareader import get_date_only, get_data_from_bossa, create_directory
from wsedatareader import get_yahoo_date, get_data_yahoo
from misctradingtools import get_prev_workday_datestring, plot_ichimoku
from misctradingtools import get_date_from_past, return_data_path, return_indexes

cache = TTLCache(maxsize=600, ttl=12*3600)


def kumo_brekaut_01_02(row):
    '''
    To jest dopiero prawdziwy Kumo breakout, clear stop loss
    1.
    total: 45383.67,  prct: 41.64%,  years: 10,  prct/year: 4.16%, nr -: 55,
    sum -: -18812.82, nr +: 54, sum +: 64196.49, ATR_RAIO: 0.5
    '''
    global BUDZET
    global TRANS_ID
    global TRANS
    global COUNT
    global STOCK
    global data
    global BOSSA_DATE
    LOCAL_VERBOSE = False
    # global BE_VERBOSE
    #if (get_date_only(row) > get_date_from_past(past=10) and
    #    (get_date_only(row) <= BOSSA_DATE)):
    if (get_date_only(row) == BOSSA_DATE) :
        BE_VERBOSE = True
    else:
        BE_VERBOSE = False
    if get_date_only(row) <= BOSSA_DATE:
        if not TRANS.in_transaction:
            #if ((row['close'] > row['senkou_span_a']) and
            #if ((row['kumo'] == 1) and (row['close'] > row['senkou_span_a']) and
            if ((row['close'] > row['senkou_span_b']) and (row['close'] > row['senkou_span_a'])):# and
                    #(row['close'] > row['c26']) and #(row['kumo26'] == 1) and
                    #(row['tenkan_sen'] > row['kijun_sen'])):
                stock_number = TRANS.how_many_stocks(row['close'],
                                                    BUDZET.equity)
                temp_sl = row['senkou_span_b'] - row['atr_sl']
                TRANS.open_transaction(stock_number, row['close'],
                                    get_date_only(row),
                                    be_verbose=LOCAL_VERBOSE)
                TRANS.curr_value(price=row['close'],
                                date=get_date_only(row),
                                be_verbose=LOCAL_VERBOSE)
                temp_sl = row['senkou_span_b'] - row['atr_sl']
                if BE_VERBOSE:
                    print('+++ {} KUPUJE {}'.format(get_date_only(row), STOCK))
                TRANS.set_sl(sl_type='fixed',
                            sl_factor=temp_sl,
                            date_sl=get_date_only(row),
                            be_verbose=BE_VERBOSE)
                TRANS.define_risk(verbose=BE_VERBOSE)
                BUDZET.manage_amount(-TRANS.open_total)
                return 1
        else:
            if row['close'] < TRANS.stop_loss:
                if BE_VERBOSE:
                    print('--- {} ZAMYKAM {}'.format(get_date_only(row), STOCK))
                TRANS.close_transaction(row['close'],
                                        get_date_only(row),
                                        be_verbose=BE_VERBOSE)
                BUDZET.manage_amount(TRANS.close_total)
                TRANS.reset_values()
                return -1
            else:
                TRANS.curr_value(row['close'],
                                date=get_date_only(row),
                                be_verbose=False)
                #added on 21.08.2022
                new_method = False 
                                  # True - checking which span is higher
                                  # False - initial version, every checks was
                                  #         done this way
                if new_method:
                    if row['senkou_span_b'] > row['senkou_span_a']:
                        temp_sl = row['senkou_span_b'] - row['atr_sl']
                    else:
                        temp_sl = row['senkou_span_a'] - row['atr_sl']
                else:
                    temp_sl = row['senkou_span_b'] - row['atr_sl']
                # end added on 21.08.2022, next line commented out
                curr_sl = TRANS.stop_loss
                TRANS.set_sl(sl_type='fixed',
                            sl_factor=temp_sl,
                            date_sl=get_date_only(row),
                            be_verbose=False)
                new_sl = TRANS.stop_loss
                if new_sl > curr_sl and BE_VERBOSE:
                    print('''
                            ^^^ {} UP SL {}, SL {:.2f}, bought {}, curr value: {:.2f}, curr result {:.2f}%
                        '''.format(get_date_only(row),
                                    STOCK,
                                    TRANS.stop_loss,
                                    TRANS.open_date,
                                    TRANS.current_value,
                                    100*(TRANS.current_value - TRANS.open_total)/TRANS.open_total))
                elif new_sl <= curr_sl and BE_VERBOSE:
                    print('''
                            --- {} DO NOTHING {}, SL {:.2f}, bought {}, curr value: {:.2f} curr result {:.2f}%
                        '''.format(get_date_only(row),
                                    STOCK,
                                    TRANS.stop_loss,
                                    TRANS.open_date,
                                    TRANS.current_value,
                                    100*(TRANS.current_value - TRANS.open_total)/TRANS.open_total))
                TRANS.register_transaction(verbose=LOCAL_VERBOSE)


def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.strip()
        tickers.append(ticker)
    return tickers

def download_data(ticker, start, end):
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        #print(ticker)
        return data
    except Exception as e:
        print(f'Błąd podczas pobierania danych dla spółki {ticker}: {e}')
        return None

@cached(cache)
def calculate_sma(ticker, window):
    try:
        data = download_data(ticker, start='2022-05-19', end='2023-05-19')
        if data is not None:
            data['SMA'] = data['Close'].rolling(window=window).mean()
        return data
    except Exception as e:
        print(f'Błąd podczas pobierania danych dla spółki {ticker}: {e}')

@cached(cache)
def calculate_price_change(ticker):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    data = download_data(ticker, start=start_date_str, end=end_date_str)
    if data is not None and len(data) > 0:
        start_price = data.iloc[0]['Close']
        end_price = data.iloc[-1]['Close']
        price_change = (end_price - start_price) / start_price * 100
        return price_change
    else:
        return None

def calculate_sma200_above_sp500(tickers):
    sma200_above_sp500 = []
    #licznik = 0
    for ticker in tickers:
        #licznik = licznik +1
        #print('calculate_sma200_above_sp500 ', licznik)
        try:
            data = calculate_sma(ticker, 200)
            if data is not None and len(data) > 0:
                latest_sma200 = data.iloc[-1]['SMA']
                latest_close = data.iloc[-1]['Close']
                if latest_close > latest_sma200:
                    sma200_above_sp500.append(ticker)
        except Exception as e:
            print("Błąd podczas obliczania SMA200 dla", ticker, ":", e)
    return sma200_above_sp500


def find_outperforming_stocks(tickers):
    results = []
    sp500_price_change = calculate_price_change('^GSPC')
    #licznik = 0
    for ticker in tickers:
        #licznik = licznik + 1
        #print('find_outperforming_stocks ', licznik)
        try:
            price_change = calculate_price_change(ticker)
            #print('PC SP500 ', sp500_price_change, ' PC ', ticker, ' ', price_change)
            if price_change > sp500_price_change:
                data = calculate_sma(ticker, 50)
                current_price = data['Close'][-1]
                sma50 = data['SMA'][-1]
                sma200 = data['SMA'][-1]
                volume = data['Volume'][-20:].mean()
                if current_price > sma50 and current_price > sma200 and volume > 100000:
                    #print("ticker: ", ticker)
                    #sector = get_sector(ticker)
                    #print("sector: ", sector)
                    #results.append((ticker, sector, price_change))
                    results.append(ticker)
        except Exception as e:
            print(f'Błąd podczas pobierania danych dla spółki {ticker}: {e}')
    return results

#****************************************************************************
# paths
'''
STOCKS = ['XD9U.DE', 'AAPL', 'ANET', 'CNDX.L', 'IQQH.DE','SGLN.L', 'SWDA.L',
          'VWRA.L', 'IS3N.DE', 'TROW', 'OI', 'NFLX', 'SHOP', 'ETSY', 'POOL',
          'PYPL', 'PAYC', 'COST', 'ARKK', 'VEEV', 'RGEN', 'ADBE',
          'EXPD', 'CHTR', 'AMD', 'NVDA', 'QLYS', 'BRO', 'SBUX',
          'PPG', 'MMM', 'NEE', 'AON', 'ACN', 'ALGN', 'GOOG', 'MO', 'AMZN',
          'AMT', 'AWK', 'APH', 'ASME.DE', 'TEAM', 'ATRI', 'ADSK',
          'AXON', 'BC8.DE', 'BLK', 'SQ', 'BA', 'BKNG', 'AVGO', 'BRO', 'CABO',
          'CSL', 'CWST', 'CDNS', 'CVNA', 'CBZ', 'CBOE', 'CELH', 'FVRR', 'CRNC',
          'CHE', 'ZTS', 'CHD', 'CTAS', 'CSCO', 'NET', 'CGNX', 'STZ',
          'CPRT', 'CSGP', 'COUP', 'D6H.DE', 'DHR', 'DXCM', 'DLR', 'APPS',
          'DOCU', 'DG', 'EW', 'ENPH', 'EPAM', 'EQIX', 'EXPO', 'EXR',
          'FDS', 'FICO', 'FIVN', 'FVRR', 'FTNT', 'GAW.L', 'GRMN', 'GNRC',
          'GPN', 'GRWG', 'HEI', 'HD', 'HRL', 'HUBS', 'HUM', 'HYQ.DE', 'IAC',
          'IDXX', 'ILMN', 'INMD', 'PODD', 'JNJ', 'KEYS', 'KNSL', 'KC4.DE',
          'MKTX', 'MASI', 'MA', 'MTCH', 'MCD', 'MLAB', 'META', 'MTD', 'MSFT',
          'MDB', 'MPWR', 'MNST', 'MSCI', 'NEM.DE', 'NTES', 'NICE', 'NKE', 'NVR',
          'OKTA', 'ODFL', 'ORLY', 'PAYX', 'PDD', 'PG', 'QLYS', 'RMD', 'RNG',
          'ROKU', 'ROP', 'SRT3.DE', 'SE', 'NOW', 'SHOP', 'SI', 'SLP', 'SPGI',
          'SPSC', 'TSM', 'TAL', 'TGT', 'TDOC', 'DSGX', 'EL', 'PGR', 'SHW',
          'TTD', 'DIS', 'TMO', 'TSCO', 'TYL', 'UFPI', 'UNH', 'V', 'WAT', 'WSO',
          'WEC', 'WST', 'XPEL', 'ZTS']
'''
'''
STOCKS = ['^SPX', 'AAPL', 'ACN', 'ADBE', 'ADSK', 'AJG', 'ALGN', 'AMD', 'AMT', 'AMZN',
          'AON', 'APH', 'APPS', 'ARKK', 'ASME.DE', 'ATRI', 'AVGO', 'AWK',
          'AXON', 'BA', 'BC8.DE', 'BLK', 'BRO', 'CBOE',
          'CBZ', 'CDNS', 'CELH', 'CGNX', 'CHD', 'CHE', 'CHTR', 'CNDX.L',
          'COST', 'CPNG', 'CPRT', 'CRNC', 'CSCO', 'CSGP', 'CSL', 'CTAS',
          'CVNA', 'CWST', 'D6H.DE', 'DG', 'DHR', 'DIS', 'DLR', 'DOCU',
          'DSGX', 'DXCM', 'EL', 'ENPH', 'EPAM', 'EQIX', 'ETSY', 'EW', 'EXPD',
          'EXPO', 'EXR', 'FDS', 'FICO', 'FIVN', 'FTNT', 'FVRR',
          'GAW.L', 'GNRC', 'GOOG', 'GPN', 'GRMN', 'GRWG', 'HD', 'HEI', 'HRL',
          'HUBS', 'HUM', 'HYQ.DE', 'IAC', 'IDXX', 'ILMN', 'INMD', 'IQQH.DE',
          'IS3N.DE', 'JNJ', 'KC4.DE', 'KEYS', 'MA', 'MASI', 'MCD',
          'MDB', 'META', 'MKTX', 'MLAB', 'MMM', 'MNST', 'MO', 'MPW', 'MPWR',
          'MSCI', 'MSFT', 'MSI', 'MTCH', 'MTD', 'NEE', 'NEM.DE', 'NET', 'NFLX',
          'NICE', 'NKE', 'NOW', 'NTES', 'NVDA', 'NVR', 'ODFL', 'OI', 'OKTA',
          'ORLY', 'PANW', 'PAYC', 'PAYX', 'PDD', 'PG', 'PGR', 'PODD', 'POOL', 'PPG',
          'PYPL', 'QLYS', 'RGEN', 'RMD', 'RNG', 'ROKU', 'ROP', 'SBUX','SGLN.L',
          'SE', 'SHOP', 'SHW', 'SI', 'SLP', 'SPGI', 'SPSC', 'SQ', 'SRT3.DE',
          'STZ', 'SWDA.L', 'TAL', 'TDOC', 'TEAM', 'TGT', 'TMO', 'TROW', 'TSCO',
          'TSM', 'TTD', 'TYL', 'UFPI', 'UNH', 'V', 'VEEV', 'VWRA.L', 'WAT',
          'WEC', 'WSO', 'WST', 'XPEL', 'ZTS', 'XD9U.DE']
'''
#STOCKS = ['AMD']
STOCKS = ['ACGL', 'ADBE', 'AMD', 'BLK', 'CABO', 'CDNS', 'CTAS', 'CGNX', 'GWW',
          'IDXX', 'FDX', 'MCD', 'MSI', 'MSFT', 'NFLX', 'NVDA', 'ORCL', 'ORLY', 'PANW', 'PYPL',
          'SHOP', 'SBUX', 'TROW', 'TSCO', 'V', 'AVGO', 'MSFT', 'HSY',
          'IQQH.DE', 'VEEV']

'''
STOCKS = ['ABT','AAL', 'AAPL', 'ABC', 'ADSK', 'AFL', 'AJG', 'ALK', 'AMZN',
              'AON', 'BA', 'BR', 'BRO', 'CAH', 'CBOE', 'CCL', 'CE', 'CHD',
              'CMCSA','CRM','CSGP','CTSH','DAL','DVA','DXCM','ETN','FAST',
              'FDX','FI','FICO','FLT','FTNT','GE','GOOG','GOOGL','GRMN','GWW',
              'HIG','HPQ','HWM','ICE','IDXX','INTU','INVH','IRM','IT','JCI',
              'KMX','L','LOW','LYV','MAR','MCD','META','MMC','MSFT','MSI',
              'NCLH','NFLX','NTAP','NVDA','NWS','NWSA','PWR','RCL','ROK','ROL',
              'ROP','RSG','SNPS','SPGI','STE','TAP','UAL','V','VRSK','VRSN',
              'WM','ZBH']
'''
TECH_EXCEPTIONS = [] 
EXCEPTIONS = TECH_EXCEPTIONS
'''
EXCEPTIONS = ['ABT','AAL', 'AAPL', 'ABC', 'ADSK', 'AFL', 'AJG', 'ALK', 'AMZN',
              'AON', 'BA', 'BR', 'BRO', 'CAH', 'CBOE', 'CCL', 'CE', 'CHD',
              'CMCSA','CRM','CSGP','CTSH','DAL','DVA','DXCM','ETN','FAST',
              'FDX','FI','FICO','FLT','FTNT','GE','GOOG','GOOGL','GRMN','GWW',
              'HIG','HPQ','HWM','ICE','IDXX','INTU','INVH','IRM','IT','JCI',
              'KMX','L','LOW','LYV','MAR','MCD','META','MMC','MSFT','MSI',
              'NCLH','NFLX','NTAP','NVDA','NWS','NWSA','PWR','RCL','ROK','ROL',
              'ROP','RSG','SNPS','SPGI','STE','TAP','UAL','V','VRSK','VRSN',
              'WM','ZBH']
'''
#'''
DATA_PATH = str(return_data_path())
HISTORY = []
try:
    BOSSA_DATE = get_yahoo_date()
except:
    print('nie udało się pobrać daty z Yahoo')
    BOSSA_DATE = date.today()
END_DATE = BOSSA_DATE + timedelta(days=1)
print(END_DATE)
YEARS = 1
BE_VERBOSE = True
SAMPLES = 240 * YEARS
YEAR_T, MM_T, DAY_T = END_DATE.year, END_DATE.month, END_DATE.day
START_DATE = date(YEAR_T-YEARS, MM_T, DAY_T)
EXPECTED_COLUMNS = ['high', 'low', 'open', 'close', 'volume', 'adjclose']
ALL_TRADES = pd.DataFrame()
SHOW_GRAPH = False
SAVE_SINGLE_STOCK = False
SAVE_RESULTS = False
ALGO = [kumo_brekaut_01_02]
MULT_RISK = 2
ATR_RATIO = 0.50 # 33 dla 10 lat
#BOSSA_DATE = get_bossa_date(mode='datetime') # date.today()
#print(BOSSA_DATE)
warnings.filterwarnings('ignore')
# Creating directory to store results
create_directory('Signals')
print('********************* US ******************************')
for STOCK in STOCKS:
    if STOCK not in EXCEPTIONS:
        temp = []
        INITIAL_BUDGET = 4900
        BUDZET = Budget(amount=INITIAL_BUDGET)
        GeneralLedger = []
        TRANS_ID = 0
        COUNT = 0
        TRANS = Transaction(TRANS_ID, GeneralLedger)
        #DATA = get_data_from_bossa(stooq_name=STOCK, path_to_data=DATA_PATH)
        try:
            DATA = get_data_yahoo(STOCK, START_DATE, END_DATE)
            DATA.columns = EXPECTED_COLUMNS
            DATA['c_1'] = DATA.close.shift(1)
            DATA['c_3'] = DATA.close.shift(3)
            high_9 = DATA['high'].rolling(window=9).max()
            low_9 = DATA['low'].rolling(window=9).min()
            DATA['tenkan_sen'] = (high_9 + low_9) /2
            high_26 = DATA['high'].rolling(window=26).max()
            low_26 = DATA['low'].rolling(window=26).min()
            DATA['kijun_sen'] = (high_26 + low_26) /2
            last_index = DATA.iloc[-1:].index[0]
            last_date = DATA.iloc[-1:].index[0].date()
            for i in range(26):
                DATA.loc[last_index+timedelta(days=1) +
                        timedelta(days=i),
                        'date'] = last_date + timedelta(days=i)
            DATA['senkou_span_a'] = ((DATA['tenkan_sen'] +
                                    DATA['kijun_sen']) / 2).shift(26)
            high_52 = DATA['high'].rolling(window=52).max()
            low_52 = DATA['low'].rolling(window=52).min()
            DATA['senkou_span_b'] = ((high_52 + low_52) /2).shift(26)
            DATA['chikou_span'] = DATA['close'].shift(-26) # sometimes -22
            DATA.loc[DATA.tenkan_sen > DATA.kijun_sen, 'cross'] = 1
            DATA.loc[DATA.tenkan_sen < DATA.kijun_sen, 'cross'] = -1
            DATA.loc[DATA.tenkan_sen == DATA.kijun_sen, 'cross'] = 0
            DATA['cross_2'] = DATA.cross.shift(2)
            DATA['sygnal'] = 0
            DATA.loc[DATA.senkou_span_a > DATA.senkou_span_b, 'kumo'] = 1
            DATA.loc[DATA.senkou_span_a < DATA.senkou_span_b, 'kumo'] = -1
            DATA.loc[DATA.senkou_span_a == DATA.senkou_span_b, 'kumo'] = 0
            DATA['kumo26'] = DATA.kumo.shift(-26)
            DATA['c26'] = DATA.close.shift(26)
            DATA['atr26'] = ATR(DATA.close, DATA.low, DATA.high, timeperiod=26)
            DATA['atr_sl'] = DATA.atr26 * ATR_RATIO
            data = DATA.tail(SAMPLES)
            data['signal'] = data.apply(ALGO[0], axis=1)
            man_close_date = get_prev_workday_datestring()
        except Exception as e:
            print(f'Błąd podczas pobierania danych dla spółki {STOCK}: {e}')

if SAVE_RESULTS:
    try:
        F_N = 'Results/' + str(ALGO[0]).split(' ')[1] + '-'
        F_N = F_N + str(NOW.year) + '-' + str(NOW.month) + '-' + str(NOW.day)
        F_N = F_N + '_' + str(NOW.hour) + '_' + str(NOW.minute) + '_'
        F_N = F_N + str(NOW.second)
        ALL_TRANS_DETAILS = F_N + '-d-atr-' + str(ATR_RATIO) + '-' \
                            + str(YEARS) + '-years.xlsx'
        ALL_TRANS_SUMMARY = F_N + '-s-atr-' + str(ATR_RATIO) + '-' \
                            + str(YEARS) + '-years.xlsx'
        ALL_TRADES.to_excel(ALL_TRANS_DETAILS, sheet_name='Original')
        HIST.to_excel(ALL_TRANS_SUMMARY, sheet_name='Original')
    except:
        print('Note! results not saved due to error. Save manually!')
