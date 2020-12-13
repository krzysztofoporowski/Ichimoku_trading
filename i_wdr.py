# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 19:48:17 2019

@author: krzysztof.oporowski
"""

from datetime import timedelta, datetime
import sys
sys.path.append('/home/krzys/python/SimTradeSim')
sys.path.append('/home/krzys/python/WSEDataReader')
sys.path.append('/home/krzys/python/misctradingtools')
import warnings
import pandas as pd
from talib import ATR
from SimTradeSim import Budget, Transaction, define_gl
from wsedatareader import get_date_only, get_data_from_bossa, create_directory
from wsedatareader import get_bossa_date
from misctradingtools import get_prev_workday_datestring, plot_ichimoku
from misctradingtools import get_date_from_past, return_data_path

def kumo_brekaut_01_02(row):
    '''
    To jest dopiero prawdziwy Kumo breakout, clear stop loss 
    1.
    total: 45383.67,  prct: 41.64%,  years: 10,  prct/year: 4.16%, nr -: 55,
    sum -: -18812.82, nr +: 54, sum +: 64196.49, ATR_RAIO: 0.5
    2. 

    '''
    global BUDZET
    global TRANS_ID
    global TRANS
    global COUNT
    global STOCK
    global data
    global BOSSA_DATE
    # global BE_VERBOSE
    # if (get_date_only(row) > get_date_from_past(past=3) and
    #    (get_date_only(row) <= BOSSA_DATE)):
    if (get_date_only(row) == BOSSA_DATE) :
        BE_VERBOSE = True
    else:
        BE_VERBOSE = False
    if not TRANS.in_transaction:
        if ((row['kumo'] == 1) and (row['close'] > row['senkou_span_a']) and
                (row['close'] > row['c26']) and (row['kumo26'] == 1)):
            stock_number = TRANS.how_many_stocks(row['open'],
                                                    BUDZET.equity)
            temp_sl = row['senkou_span_b'] - row['atr_sl']
            # print('+++ Buy {}: on: {} nr: {}, set SL: {}')
            TRANS.open_transaction(stock_number, row['open'],
                                    get_date_only(row),
                                    be_verbose=False)
            TRANS.curr_value(price=row['close'],
                                date=get_date_only(row),
                                be_verbose=False)
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
            temp_sl = row['senkou_span_b'] - row['atr_sl']
            curr_sl = TRANS.stop_loss
            TRANS.set_sl(sl_type='fixed',
                         sl_factor=temp_sl,
                         date_sl=get_date_only(row),
                         be_verbose=False)
            new_sl = TRANS.stop_loss
            if new_sl > curr_sl and BE_VERBOSE:
                print('^^^ {} UP SL {}, {}'.format(get_date_only(row), STOCK,
                                                   TRANS.stop_loss))
            TRANS.register_transaction(verbose=False)


#****************************************************************************
# paths


WIG20 = ['ALIOR', 'CCC', 'CDPROJEKT', 'CYFRPLSAT', 'DINOPL', 'JSW', 'KGHM',
         'LPP', 'LOTOS', 'MBANK', 'ORANGEPL', 'PEKAO', 'PGE', 'PGNIG',
         'PKNORLEN', 'PKOBP', 'PLAY', 'PZU', 'SANPL', 'TAURONPE']
ETF = ['ETFSP500', 'ETFDAX', 'ETFW20L']
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
# STOCKS = ['WIELTON']
TECH_EXCEPTIONS = ['BAHOLDING'] # 'BAHOLDING' has duplicated index
FUND_EXCEPTIONS = ['ORANGEPL'] # ORANGPL ROE 0,51% 23.08.2020
EXCEPTIONS = TECH_EXCEPTIONS + FUND_EXCEPTIONS
#EXCEPTIONS = []
DATA_PATH = str(return_data_path())
HISTORY = []
YEARS = 3
SAMPLES = 240 * YEARS
ALL_TRADES = pd.DataFrame()
# BE_VERBOSE = False
SHOW_GRAPH = False
SAVE_SINGLE_STOCK = False
SAVE_RESULTS = False
ALGO = [kumo_brekaut_01_02]
MULT_RISK = 2
ATR_RATIO = 0.50 # 33 dla 10 lat
BOSSA_DATE = get_bossa_date(mode='datetime')
warnings.filterwarnings('ignore')
# Creating directory to store results
create_directory('Signals')

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
        DATA['c_3'] = DATA.close.shift(3)
        #DATA['o_1'] = DATA.open.shift(1)
        #DATA['l_1'] = DATA.low.shift(1)
        #DATA['h_1'] = DATA.high.shift(1)
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
        '''
        kolumny = ['close', 'kijun_sen', 'tenkan_sen', 'senkou_span_a',
                    'senkou_span_b', 'chikou_span']#, 'sygnal']
        '''
        data['signal'] = data.apply(ALGO[0], axis=1)
        man_close_date = get_prev_workday_datestring()
        """
        if TRANS.in_transaction:
            try:
                TRANS.close_transaction(data['close'].loc[man_close_date],
                                        date_close=man_close_date,
                                        be_verbose=BE_VERBOSE)
            except KeyError:
                print('przy tej spolce {} KeyError'.format(STOCK))
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
        if SAVE_SINGLE_STOCK:
            FILE = 'Results/' + STOCK + '-' + str(ALGO[0]).split(' ')[1]
            FILE = FILE + '-atr-' + str(ATR_RATIO) + '.csv'
            trades.to_csv(FILE)
        # print('{} trades sum: {:.2f}'.format(STOCK,
        #                                     trades['trans_result'].sum()))
        temp = [STOCK, trades.trans_result.sum()]
        HISTORY.append(temp)
        if buy.signal.sum() > 0 or sell.signal.sum() < 0:
            if SHOW_GRAPH:
                plot_ichimoku(data, STOCK, buy, sell)
        ALL_TRADES = pd.concat([trades, ALL_TRADES])
        """
'''
HIST = pd.DataFrame(HISTORY, columns=['stock', 'result'])
A_T = HIST.result.sum()
T_PERC = 100 * HIST.result.sum()
T_PERC = T_PERC/(HIST[HIST.result != 0].stock.count()*INITIAL_BUDGET)
PERC_Y = 100 * HIST.result.sum()
PERC_Y = PERC_Y/YEARS
PERC_Y = PERC_Y/(HIST[HIST.result != 0].stock.count()*INITIAL_BUDGET)
"""
print('all trades: {:.2f}, \
       percent: {:.2f}%, \
       years: {}, \
       percent/year: {:.2f}%,\
       multiplier of risk: {},\
       muliplier do ATR ratio: {}'.format(A_T, T_PERC, YEARS, PERC_Y, MULT_RISK,
                                          ATR_RATIO))
"""
HIST.sort_values(by=['result'], ascending=True, inplace=True)
NOW = datetime.now()
print('total: {:.2f}, \
       prct: {:.2f}%, \
       years: {}, \
       prct/year: {:.2f}%,\
       nr -: {},\
       sum -: {:.2f},\
       nr +: {},\
       sum +: {:.2f},\
       ATR_RAIO: {}'.format(A_T, T_PERC, YEARS, PERC_Y,
                            HIST['result'].loc[HIST.result < 0].count(),
                            HIST['result'].loc[HIST.result < 0].sum(),
                            HIST['result'].loc[HIST.result > 0].count(),
                            HIST['result'].loc[HIST.result > 0].sum(),
                            ATR_RATIO))
'''
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
