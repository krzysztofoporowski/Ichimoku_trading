# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 19:48:17 2019

@author: krzysztof.oporowski
"""

from datetime import timedelta, datetime, date
import sys
sys.path.append('c:/users/krzys/python/SimTradeSim')
sys.path.append('c:/users/krzys/python/WSEDataReader')
sys.path.append('c:/users/krzys/python/misctradingtools')
import warnings
import pandas as pd
import numpy as np
from talib import ATR
from SimTradeSim import Budget, Transaction, define_gl
from wsedatareader import get_date_only, create_directory
from wsedatareader import get_data_yahoo
from misctradingtools import get_prev_workday_datestring, plot_ichimoku
from misctradingtools import get_date_from_past, return_data_path, return_indexes

def kumo_brekaut_01_02(row):
    '''
    Kumo breakout, clear stop loss
    '''
    global BUDZET
    global TRANS_ID
    global TRANS
    global COUNT
    global STOCK
    global data
    global BE_VERBOSE
    BE_VERBOSE_L = False
    if not TRANS.in_transaction:
        condition = True
        #if ((row['c_1'] > row['senkou_span_a']) and
        #if ((row['kumo'] == 1) and (row['c_1'] > row['senkou_span_a']) and 
        if ((row['c_1'] > row['senkou_span_b']) and (row['c_1'] > row['senkou_span_a']) and 
                (row['c_1'] > row['c26']) and (row['kumo26'] == 1)):
            if row['open'] != 0:
                if BUDZET.equity > 4:
                    stock_number = TRANS.how_many_stocks(row['open'],
                                                         BUDZET.equity)
                    if stock_number > 0:
                        TRANS.open_transaction(stock_number, row['open'],
                                               get_date_only(row),
                                               be_verbose=BE_VERBOSE_L)
                        TRANS.curr_value(price=row['close'],
                                         date=get_date_only(row),
                                         be_verbose=BE_VERBOSE_L)
                        temp_sl = row['c_1'] - row['atr_sl']
                        TRANS.set_sl(sl_type='fixed',
                                     sl_factor=temp_sl,
                                     date_sl=get_date_only(row),
                                     be_verbose=BE_VERBOSE_L)
                        TRANS.define_risk(verbose=BE_VERBOSE_L)
                        BUDZET.manage_amount(-TRANS.open_total)
                        return 1
    else:
        if row['c_1'] < TRANS.stop_loss:
            if row['open'] != 0:
                TRANS.close_transaction(row['close'],
                                        get_date_only(row),
                                        be_verbose=BE_VERBOSE)
                BUDZET.manage_amount(TRANS.close_total)
                TRANS.reset_values()
                return -1
            else:
                pass#print('cena zamkniecia {}'.format(row['open']))
        else:
            #BE_VERBOSE = False
            TRANS.curr_value(row['close'],
                             date=get_date_only(row),
                             be_verbose=BE_VERBOSE_L)
            #added on 21.08.2022
            new_method = False
                                # True - checking which span is higher
                                # False - initial version, every checks was
                                #         done this way
            if new_method:
                if row['senkou_span_b'] > row['senkou_span_a']:
                    temp_sl = row['c_1'] - row['atr_sl']
                else:
                    temp_sl = row['c_1'] - row['atr_sl']
            else:
                temp_sl = row['c_1'] - row['atr_sl']
            # end added on 21.08.2022, next line commented out
            #temp_sl = row['kijun_sen'] - row['atr_sl']
            TRANS.set_sl(sl_type='fixed',
                         sl_factor=temp_sl,
                         date_sl=get_date_only(row),
                         be_verbose=BE_VERBOSE_L)
            TRANS.register_transaction(verbose=BE_VERBOSE_L)
            #BE_VERBOSE = True

def algo_2_1(row):
    '''
    wg mnie to jest to cena nad przecięciem 
    '''
    global BUDZET
    global TRANS_ID
    global TRANS
    global COUNT
    global STOCK
    global data
    global BE_VERBOSE
    if not TRANS.in_transaction:
        if ((row['c_1'] > row['kijun_sen']) and
            (row['tenkan_sen'] > row['kijun_sen']) and
            (row['tenkan_sen_3'] < row['kijun_sen_3'])):
            if row['open'] != 0:
                if BUDZET.equity > 4:
                    stock_number = TRANS.how_many_stocks(row['open'],
                                                         BUDZET.equity)
                    if stock_number > 0:
                        TRANS.open_transaction(stock_number, row['open'],
                                               get_date_only(row),
                                               be_verbose=BE_VERBOSE)
                        TRANS.curr_value(price=row['close'],
                                         date=get_date_only(row),
                                         be_verbose=BE_VERBOSE)
                        TRANS.set_sl(sl_type='fixed',
                                     sl_factor=(row['kijun_sen']-row['atr_sl']),
                                     date_sl=get_date_only(row),
                                     be_verbose=BE_VERBOSE)
                        TRANS.define_risk(verbose=BE_VERBOSE)
                        BUDZET.manage_amount(-TRANS.open_total)
                        return 1
    else:
        if row['c_1'] < TRANS.stop_loss:
            if row['open'] != 0:
                TRANS.close_transaction(row['close'],
                                        get_date_only(row),
                                        be_verbose=BE_VERBOSE)
                BUDZET.manage_amount(TRANS.close_total)
                TRANS.reset_values()
                return -1
            else:
                print('cena zamkniecia {}'.format(row['open']))
        else:
            TRANS.curr_value(row['close'],
                             date=get_date_only(row),
                             be_verbose=BE_VERBOSE)
            if TRANS.current_value > (TRANS.open_value + (3 * TRANS.risk)):
                new_sl = (TRANS.current_value - TRANS.risk)/TRANS.stocks_number
                TRANS.set_sl(sl_type='fixed',
                             sl_factor=new_sl,
                             date_sl=get_date_only(row),
                             be_verbose=BE_VERBOSE)
            else:
                TRANS.set_sl(sl_type='fixed',
                             sl_factor=(row['kijun_sen']-row['atr_sl']),
                             date_sl=get_date_only(row),
                             be_verbose=BE_VERBOSE)
            TRANS.register_transaction(verbose=BE_VERBOSE)


#****************************************************************************

STOCKS = ['AAPL', 'ACN', 'ADBE', 'ADSK', 'AJG', 'ALGN', 'AMD', 'AMT', 'AMZN',
          'AON', 'APH', 'APPS', 'ARKK', 'ASME.DE', 'ATRI', 'AVGO', 'AWK',
          'AXON', 'BA', 'BC8.DE', 'BLK', 'BRO', 'CBOE',
          'CBZ', 'CDNS', 'CELH', 'CGNX', 'CHD', 'CHE', 'CHTR', 'CNDX.L',
          'COST', 'COUP', 'CPRT', 'CRNC', 'CSCO', 'CSGP', 'CSL', 'CTAS',
          'CVNA', 'CWST', 'D6H.DE', 'DG', 'DHR', 'DIS', 'DLR', 'DOCU',
          'DSGX', 'DXCM', 'EL', 'ENPH', 'EPAM', 'EQIX', 'ETSY', 'EW', 'EXPD',
          'EXPO', 'EXR', 'FDS', 'FICO', 'FIVN', 'FTNT', 'FVRR',
          'GAW.L', 'GNRC', 'GOOG', 'GPN', 'GRMN', 'GRWG', 'HD', 'HEI', 'HRL',
          'HUBS', 'HUM', 'HYQ.DE', 'IAC', 'IDXX', 'ILMN', 'INMD', 'IQQH.DE',
          'IS3N.DE', 'JNJ', 'KC4.DE', 'KEYS', 'MA', 'MASI', 'MCD',
          'MDB', 'META', 'MKTX', 'MLAB', 'MMM', 'MNST', 'MO', 'MPW', 'MPWR',
          'MSCI', 'MSFT', 'MTCH', 'MTD', 'NEE', 'NEM.DE', 'NET', 'NFLX',
          'NICE', 'NKE', 'NOW', 'NTES', 'NVDA', 'NVR', 'ODFL', 'OI', 'OKTA',
          'ORLY', 'PAYC', 'PAYX', 'PDD', 'PG', 'PGR', 'PODD', 'POOL', 'PPG',
          'PYPL', 'QLYS', 'RGEN', 'RMD', 'RNG', 'ROKU', 'ROP', 'SBUX','SGLN.L',
          'SE', 'SHOP', 'SHW', 'SI', 'SLP', 'SPGI', 'SPSC', 'SQ', 'SRT3.DE',
          'STZ', 'SWDA.L', 'TAL', 'TDOC', 'TEAM', 'TGT', 'TMO', 'TROW', 'TSCO',
          'TSM', 'TTD', 'TYL', 'UFPI', 'UNH', 'V', 'VEEV', 'VWRA.L', 'WAT',
          'WEC', 'WSO', 'WST', 'XPEL', 'ZTS', 'XD9U.DE']

STOCKS = ['AMD']
TECH_EXCEPTIONS = []
EXCEPTIONS = TECH_EXCEPTIONS # + FUND_EXCEPTIONS
EXCEPTIONS = []
DATA_PATH = str(return_data_path())
HISTORY = []
END_DATE = date.today()
YEARS = 10
SAMPLES = 240 * YEARS
YEAR_T, MM_T, DAY_T = END_DATE.year, END_DATE.month, END_DATE.day
START_DATE = date(YEAR_T-YEARS, MM_T, DAY_T)
EXPECTED_COLUMNS = ['high', 'low', 'open', 'close', 'volume', 'adjclose']
ALL_TRADES = pd.DataFrame()
BE_VERBOSE = True
SHOW_GRAPH = False
SAVE_SINGLE_STOCK = True
SAVE_RESULTS = False
ALGO = [kumo_brekaut_01_02]#[algo_2_1]#długoterminono: [kumo_brekaut_01_02]
MULT_RISK = 1
ATR_RATIO = 4 #0.50 # 33 dla 10 lat
warnings.filterwarnings('ignore')
# Creating directory to store results
create_directory('Results')

for STOCK in STOCKS:
    if STOCK not in EXCEPTIONS:
        #print(STOCK)
        temp = []
        INITIAL_BUDGET = 6500
        BUDZET = Budget(amount=INITIAL_BUDGET)
        GeneralLedger = []
        TRANS_ID = 0
        COUNT = 0
        TRANS = Transaction(TRANS_ID, GeneralLedger)
        #DATA = get_data_from_bossa(stooq_name=STOCK, path_to_data=DATA_PATH)
        # [open, high, low, close. volum]
        try:
            DATA = get_data_yahoo(STOCK, START_DATE, END_DATE)
            DATA.columns = EXPECTED_COLUMNS
            #print(DATA.head(1))
            DATA['c_1'] = DATA.close.shift(1)
            DATA['c_3'] = DATA.close.shift(2)
            DATA['o_1'] = DATA.open.shift(1)
            DATA['l_1'] = DATA.low.shift(1)
            DATA['h_1'] = DATA.high.shift(1)
            DATA['sma200'] = DATA.close.rolling(window=200).mean()
            high_9 = DATA['h_1'].rolling(window=9).max()
            low_9 = DATA['l_1'].rolling(window=9).min()
            DATA['tenkan_sen'] = (high_9 + low_9) /2
            DATA['tenkan_sen_3'] = DATA.tenkan_sen.shift(3)
            high_26 = DATA['h_1'].rolling(window=26).max()
            low_26 = DATA['l_1'].rolling(window=26).min()
            DATA['kijun_sen'] = (high_26 + low_26) /2
            DATA['kijun_sen_3'] = DATA.kijun_sen.shift(3)
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
            DATA.loc[DATA.tenkan_sen > DATA.kijun_sen, 'cross'] = 1
            DATA.loc[DATA.tenkan_sen < DATA.kijun_sen, 'cross'] = -1
            DATA.loc[DATA.tenkan_sen == DATA.kijun_sen, 'cross'] = 0
            DATA['cross_2'] = DATA.cross.shift(2)
            DATA['sygnal'] = 0
            DATA.loc[DATA.senkou_span_a > DATA.senkou_span_b, 'kumo'] = 1
            DATA.loc[DATA.senkou_span_a < DATA.senkou_span_b, 'kumo'] = -1
            DATA.loc[DATA.senkou_span_a == DATA.senkou_span_b, 'kumo'] = 0
            DATA['kumo26'] = DATA.kumo.shift(-26)
            DATA['c26'] = DATA.c_1.shift(26)
            DATA['atr26'] = ATR(DATA.c_1, DATA.l_1, DATA.h_1, timeperiod=26)
            DATA['atr_sl'] = DATA.atr26 * ATR_RATIO
            data = DATA.tail(SAMPLES)
            '''
            kolumny = ['close', 'kijun_sen', 'tenkan_sen', 'senkou_span_a',
                        'senkou_span_b', 'chikou_span']#, 'sygnal']
            '''
            data['signal'] = data.apply(ALGO[0], axis=1)
            man_close_date = get_prev_workday_datestring()
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
            #print('{} trades sum: {:.2f}'.format(STOCK,
            #                                     trades['trans_result'].sum()))
            temp = [STOCK, trades.trans_result.sum()]
            HISTORY.append(temp)
            if buy.signal.sum() > 0 or sell.signal.sum() < 0:
                if SHOW_GRAPH:
                    plot_ichimoku(data, STOCK, buy, sell)
            ALL_TRADES = pd.concat([trades, ALL_TRADES])
            print('stock: {},nr -: {}, sum -: {:.2f}, nr +: {}, sum +: {:.2f}, total: {:.2f} \n'.format( 
                                            STOCK,
                                            trades['trans_result'].loc[trades.trans_result < 0].count(),
                                            trades['trans_result'].loc[trades.trans_result < 0].sum(),
                                            trades['trans_result'].loc[trades.trans_result > 0].count(),
                                            trades['trans_result'].loc[trades.trans_result > 0].sum(),
                                            trades['trans_result'].sum()))
        except:
            pass            
HIST = pd.DataFrame(HISTORY, columns=['stock', 'result'])
A_T = HIST.result.sum()
T_PERC = 100 * HIST.result.sum()
T_PERC = T_PERC/(HIST[HIST.result != 0].stock.count()*INITIAL_BUDGET)
PERC_Y = 100 * HIST.result.sum()
PERC_Y = PERC_Y/YEARS
PERC_Y = PERC_Y/(HIST[HIST.result != 0].stock.count()*INITIAL_BUDGET)
'''
print('all trades: {:.2f}, percent: {:.2f}%, \
       years: {}, \
       percent/year: {:.2f}%,\
       multiplier of risk: {},\
       muliplier do ATR ratio: {}'.format(A_T, T_PERC, YEARS, PERC_Y, MULT_RISK,
                                          ATR_RATIO))
'''
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
