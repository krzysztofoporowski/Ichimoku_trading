# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 19:48:17 2019

@author: krzysztof.oporowski
"""

from datetime import timedelta, datetime
import warnings
import pandas as pd
from simtradesim import Budget, Transaction, define_gl
from wsedatareader import get_date_only, get_data_from_bossa, create_directory
from misctradingtools import get_prev_workday_datestring, plot_ichimoku

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
                        BUDZET.manage_amount(-TRANS.open_total)
                        return 1
    else:
        if row['tenkan_sen'] < row['kijun_sen']:
            if row['open'] != 0:
                TRANS.close_transaction(row['close'],
                                        get_date_only(row),
                                        be_verbose=BE_VERBOSE)
                BUDZET.manage_amount(TRANS.close_total)
                TRANS.reset_values()
                return -1
            else:
                print('cena zamkniecia {}'.format(row['open']))

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
# 2000 budzet, z dnia 19.02.2020
EXCEPTIONS = ['PEKAO', 'PGE', 'PKOBP', 'CLNPHARMA', 'BOS', 'MEDICALG',
              'OAT']
EXCEPTIONS = ['BAHOLDING'] # 'BAHOLDING' has duplicated index
DATA_PATH = "C:/Users/krzysztof.oporowski.HWS01/Documents/Python_projects/Data/"
HISTORY = []
YEARS = 10
SAMPLES = 240 * YEARS
ALL_TRADES = pd.DataFrame()
BE_VERBOSE = False
SHOW_GRAPH = False
warnings.filterwarnings('ignore')
# Creating directories to store results
create_directory('Results')

print('-------wersja pelna-----------------')
for STOCK in STOCKS:
    if STOCK not in EXCEPTIONS:
        #print(STOCK)
        temp = []
        INITIAL_BUDGET = 1000
        BUDZET = Budget(amount=INITIAL_BUDGET)
        GeneralLedger = []
        TRANS_ID = 0
        COUNT = 0
        TRANS = Transaction(TRANS_ID, GeneralLedger)
        DATA = get_data_from_bossa(stooq_name=STOCK, path_to_data=DATA_PATH)
        DATA['c_1'] = DATA.close.shift(1)
        DATA['o_1'] = DATA.open.shift(1)
        DATA['l_1'] = DATA.low.shift(1)
        DATA['h_1'] = DATA.high.shift(1)
        high_9 = DATA['h_1'].rolling(window=9).max()
        low_9 = DATA['l_1'].rolling(window=9).min()
        DATA['tenkan_sen'] = (high_9 + low_9) /2
        high_26 = DATA['h_1'].rolling(window=26).max()
        low_26 = DATA['l_1'].rolling(window=26).min()
        DATA['kijun_sen'] = (high_26 + low_26) /2
        last_index = DATA.iloc[-1:].index[0]
        last_date = DATA.iloc[-1:].index[0].date()
        for i in range(26):
            DATA.loc[last_index+timedelta(days=1) +
                     timedelta(days=i),
                     'date'] = last_date + timedelta(days=i)
        DATA['senkou_span_a'] = ((DATA['tenkan_sen'] +
                                  DATA['kijun_sen']) / 2).shift(26)
        high_52 = DATA['h_1'].rolling(window=52).max()
        low_52 = DATA['l_1'].rolling(window=52).min()
        DATA['senkou_span_b'] = ((high_52 + low_52) /2).shift(26)
        DATA['chikou_span'] = DATA['c_1'].shift(-26) # sometimes -22
        DATA['sygnal'] = 0
        DATA['c_mean'] = DATA.c_1.rolling(window=5).mean()
        DATA['c_mean_26'] = DATA.c_mean.shift(26)
        data = DATA.tail(SAMPLES)
        '''
        kolumny = ['close', 'kijun_sen', 'tenkan_sen', 'senkou_span_a',
                    'senkou_span_b', 'chikou_span']#, 'sygnal']
        '''
        data['signal'] = data.apply(tenkan_sen_kijun_sen_cross_f_sl, axis=1)
        man_close_date = get_prev_workday_datestring()
        if TRANS.in_transaction:
            TRANS.close_transaction(data['open'].loc[man_close_date],
                                    date_close=man_close_date,
                                    be_verbose=BE_VERBOSE)
            tr_r = round((TRANS.trans_result / TRANS.open_total)*100, 2)
            if BE_VERBOSE:
                print('SELL signal on date {}, trade result: {:.2f}, \
                        percent: {}%'.format(man_close_date,
                                            TRANS.trans_result,
                                            tr_r))
            BUDZET.manage_amount(TRANS.close_total)
            TRANS.reset_values()
        buy = data[data.signal == 1]
        sell = data[data.signal == -1]
        trades = define_gl(GeneralLedger)
        trades['stock'] = STOCK
        print('{} trades sum: {:.2f}'.format(STOCK,
                                             trades['trans_result'].sum()))
        temp = [STOCK, trades.trans_result.sum()]
        HISTORY.append(temp)
        if buy.signal.sum() > 0 or sell.signal.sum() < 0:
            if SHOW_GRAPH:
                plot_ichimoku(data, STOCK, buy, sell)
        ALL_TRADES = pd.concat([trades, ALL_TRADES])
HIST = pd.DataFrame(HISTORY, columns=['stock', 'result'])
A_T = HIST.result.sum()
T_PERC = 100 * HIST.result.sum()
T_PERC = T_PERC/(HIST[HIST.result != 0].stock.count()*INITIAL_BUDGET)
PERC_Y = 100 * HIST.result.sum()
PERC_Y = PERC_Y/YEARS
PERC_Y = PERC_Y/(HIST[HIST.result != 0].stock.count()*INITIAL_BUDGET)
print('all trades: {:.2f}, \
       percent: {:.2f}%, \
       years: {}, \
       percent/year: {:.2f}%'.format(A_T, T_PERC, YEARS, PERC_Y))
HIST.sort_values(by=['result'], ascending=True, inplace=True)
NOW = datetime.now()
try:
    F_N = 'Results/'
    F_N = F_N + str(NOW.year) + '-' + str(NOW.month) + '-' + str(NOW.day)
    F_N = F_N + '_' + str(NOW.hour) + '_' + str(NOW.minute) + '_'
    F_N = F_N + str(NOW.second)
    ALL_TRANS_DETAILS = F_N + '-d-fixed-sl' + str(YEARS) + '-years.xlsx'
    ALL_TRANS_SUMMARY = F_N + '-s-fixed-sl' + str(YEARS) + '-years.xlsx'
    ALL_TRADES.to_excel(ALL_TRANS_DETAILS, sheet_name='Original')
    HIST.to_excel(ALL_TRANS_SUMMARY, sheet_name='Original')
except:
    print('Note! results not saved due to error. Save manually!')
