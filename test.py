from cmath import nan
from datetime import timedelta, datetime, date
import sys

#from WSEDataReader.wsedatareader import get_yahoo_date
sys.path.append('c:/Users/krzysiu/python/SimTradeSim')
sys.path.append('c:/Users/krzysiu/python/WSEDataReader')
sys.path.append('c:/Users/krzysiu/python/misctradingtools')

from wsedatareader import get_yahoo_date, get_data_yahoo

import pandas as pd

data_biezaca = get_yahoo_date()
spolka = get_data_yahoo("AMD", "2021-01-01", data_biezaca)

print(spolka)
