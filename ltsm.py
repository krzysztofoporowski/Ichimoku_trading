import pandas as pd
import tensorflow as tf

data_path = "../data/"
input_file = data_path + 'AMICA.mst'
data = pd.read_csv(input_file, usecols=[1,2,3,4,5,6], skiprows=[0],
                   names=['date', 'o', 'h', 'l', 'c', 'v'],
                   index_col=[0], parse_dates=True)

