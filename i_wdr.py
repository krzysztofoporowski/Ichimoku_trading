# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 19:48:17 2019

@author: krzysztof.oporowski
"""

from datetime import timedelta, datetime
import warnings
import pandas as pd
from colorama import init, Fore
from simtradesim import Budget, Transaction
from wsedatareader import get_date_only, get_data_from_bossa, create_directory
from wsedatareader import get_bossa_date
from misctradingtools import plot_ichimoku

def tenkan_sen_kijun_sen_cross_no_sl(row):
    '''
    Tenkan Sen Kijun Sen cross - strong version (algo 1_1)
    '''
    global BUDZET
    global TRANS_ID
    global TRANS
    global COUNT
    global STOCK
    global data
    global BE_VERBOSE
    global BOSSA_DATE

    now_7 = datetime.now().date() - timedelta(days=7)
    if not TRANS.in_transaction:
        if ((row['tenkan_sen'] > row['kijun_sen']) and
                (row['tenkan_sen'] > row['senkou_span_a']) and
                (row['tenkan_sen'] > row['senkou_span_b']) and
                (row['c_mean'] > row['c_mean_26'])):
            TRANS.in_transaction = True
            if get_date_only(row) > now_7:
                if get_date_only(row) == BOSSA_DATE:
                    print(Fore.GREEN,
                          '+++ %s %s BUY: close: %s' % (STOCK,
                                                        get_date_only(row),
                                                        row['close']))
                else:
                    print(Fore.WHITE,
                          '+++ %s %s BUY: close: %s' % (STOCK,
                                                        get_date_only(row),
                                                        row['close']))
            return 1
    else:
        if row['tenkan_sen'] < row['kijun_sen']:
            TRANS.reset_values()
            if get_date_only(row) > now_7:
                if get_date_only(row) == BOSSA_DATE:
                    print(Fore.RED,
                          '--- %s %s SELL: close: %s' % (STOCK,
                                                         get_date_only(row),
                                                         row['close']))
                else:
                    print(Fore.WHITE,
                          '--- %s %s SELL: close: %s' %(STOCK,
                                                        get_date_only(row),
                                                        row['close']))
            return -1

def tenkan_sen_kijun_sen_cross_f_sl(row):
    '''
    Tenkan Sen Kijun Sen cross - only stron version (algo 1_1)
    Result files
     - fixed senkou_span_b - 2020-7-23_10_6_24
     - senkou_span_b o _a - 2020-7-23_10_14_10
    '''
    global BUDZET
    global TRANS_ID
    global TRANS
    global COUNT
    global STOCK
    global data
    global BE_VERBOSE
    global BOSSA_DATE
    if not TRANS.in_transaction:
        if ((row['tenkan_sen'] > row['kijun_sen']) and
                (row['tenkan_sen'] > row['senkou_span_a']) and
                (row['tenkan_sen'] > row['senkou_span_b']) and
                (row['c_mean'] > row['c_mean_26'])):
            if row['open'] != 0:
                if BUDZET.equity > 4:
                    stock_number = TRANS.how_many_stocks(row['open'],
                                                         BUDZET.equity)
                    if stock_number > 0:
                        TRANS.open_transaction(stock_number, row['open'],
                                               get_date_only(row),
                                               be_verbose=BE_VERBOSE)
                        if row['senkou_span_a'] > row['senkou_span_b']:
                            TRANS.set_sl(sl_type='fixed',
                                         sl_factor=row['senkou_span_b'],
                                         date_sl=get_date_only(row),
                                         be_verbose=BE_VERBOSE)
                        else:
                            TRANS.set_sl(sl_type='fixed',
                                         sl_factor=row['senkou_span_a'],
                                         date_sl=get_date_only(row),
                                         be_verbose=BE_VERBOSE)
                        BUDZET.manage_amount(-TRANS.open_total)
                        return 1
    else:
        if row['low'] < TRANS.stop_loss:
            # closing trade when SL is hit
            TRANS.close_transaction(TRANS.stop_loss,
                                    get_date_only(row),
                                    be_verbose=BE_VERBOSE)
            BUDZET.manage_amount(TRANS.close_total)
            TRANS.reset_values()
            return -1
        if row['tenkan_sen'] < row['kijun_sen']:
            # closing trade when close signal appears
            if row['open'] != 0:
                TRANS.close_transaction(row['close'],
                                        get_date_only(row),
                                        be_verbose=BE_VERBOSE)
                BUDZET.manage_amount(TRANS.close_total)
                TRANS.reset_values()
                return -1
            else:
                print('cena zamkniecia {}'.format(row['open']))


#****************************************************************************

WIG20 = ['ALIOR', 'CCC', 'CDPROJEKT', 'CYFRPLSAT', 'DINOPL', 'JSW', 'KGHM',
         'LPP', 'LOTOS', 'MBANK', 'ORANGEPL', 'PEKAO', 'PGE', 'PGNIG',
         'PKNORLEN', 'PKOBP', 'PLAY', 'PZU', 'SANPL', 'TAURONPE', 'ETFSP500',
         'ETFDAX', 'ETFW20L']
MWIG40 = ['11BIT', 'ASSECOPOL', 'AMICA', 'GRUPAAZOTY', 'BUDIMEX', 'BENEFIT',
          'HANDLOWY', 'BORYSZEW', 'INTERCARS', 'CIECH', 'CIGAMES',
          'CLNPHARMA', 'COMARCH',
          'AMREST', 'FORTE',
          'ECHO', 'ENEA',
          'ENERGA', 'EUROCASH', 'FAMUR', 'GPW', 'GTC', 'GETIN',
          'INGBSK', 'KERNEL', 'KRUK', 'KETY', 'LIVECHAT', 'BOGDANKA', 'MABION',
          'BNPPPL', 'DEVELIA', 'VRG',
          'MILLENNIUM', 'ORBIS', 'PKPCARGO', 'PLAYWAY', 'STALPROD', 'TSGAMES',
          'WIRTUALNA', 'MWIG40']
SWIG80 = ['ATAL', 'ABPL', 'ASSECOBS', 'ACAUTOGAZ', 'AGORA', 'ALTUSTFI',
          'AMBRA', 'ALUMETAL', 'AUTOPARTN', 'APATOR', 'ARCHICOM', 'ASBIS',
          'ASSECOSEE', 'ASTARTA', 'ATMGRUPA', 'BAHOLDING', 'BIOTON', 'PBKM',
          'BOS', 'BSCDRUK', 'COMP', 'COGNOR', 'CPGROUP', 'CORMAY',
          'DEBICA', 'DOMDEV', 'EKOEXPORT', 'ELBUDOWA', 'ELEMENTAL', 'ENTER',
          'FERRO', 'IDEABANK', 'IMCOMPANY', 'INSTALKRK', 'KOGENERA',
          'DATAWALK',
          'KRUSZWICA', 'LENTEX', 'MCI', 'MEDICALG', 'MANGATA', 'MLPGROUP',
          'MENNICA', 'MONNARI', 'NETIA', 'NEUCA', 'NEWAG', 'OAT', 'OPONEO.PL',
          'OVOSTAR', 'WIELTON']
STOCKS = WIG20 + MWIG40 + SWIG80
#STOCKS = ['PLAY', 'LENTEX']
#STOCKS = ['PLAY']
# 2000 budzet, z dnia 19.02.2020
EXCEPTIONS = ['PEKAO', 'PGE', 'PKOBP', 'CLNPHARMA', 'BOS', 'MEDICALG',
              'OAT', 'BAHOLDING']
EXCEPTIONS = ['BAHOLDING']
DATA_PATH = "C:/Users/krzysztof.oporowski.HWS01/Documents/Python_projects/Data/"
HISTORY = []
YEARS = 1
SAMPLES = 240 * YEARS
ALL_TRADES = pd.DataFrame()
BE_VERBOSE = False
SHOW_GRAPH = False
warnings.filterwarnings('ignore')
# Creating directories to store results
create_directory('Results')
# Initializing colorama
init()
# Getting current Bossa.pl data date
BOSSA_DATE = get_bossa_date(mode='datetime')

for STOCK in STOCKS:
    if STOCK not in EXCEPTIONS:
        #print('--------------------------------------------------------------')
        temp = []
        INITIAL_BUDGET = 1000
        BUDZET = Budget(amount=INITIAL_BUDGET)
        GeneralLedger = []
        TRANS_ID = 0
        COUNT = 0
        TRANS = Transaction(TRANS_ID, GeneralLedger)
        DATA = get_data_from_bossa(stooq_name=STOCK, path_to_data=DATA_PATH)
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
        DATA['sygnal'] = 0
        DATA['c_mean'] = DATA.close.rolling(window=5).mean()
        DATA['c_mean_26'] = DATA.c_mean.shift(26)
        data = DATA.tail(SAMPLES)
        '''
        kolumny = ['close', 'kijun_sen', 'tenkan_sen', 'senkou_span_a',
                    'senkou_span_b', 'chikou_span']#, 'sygnal']
        '''
        data['signal'] = data.apply(tenkan_sen_kijun_sen_cross_no_sl, axis=1)
