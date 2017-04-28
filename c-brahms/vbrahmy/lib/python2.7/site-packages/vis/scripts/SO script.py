import pandas as pd
import numpy as np
import time
import pdb

ser = pd.Series(['aa','bb','cc','dd','ee','ff','gg','hh','ii','jj','kk'])
df = pd.concat([ser.shift(-x) for x in range(4)], axis=1)
terms = ['ff']

t0 = time.time()
ind = -np.arange(0, df.shape[1])+pd.Index(ser).get_loc('ff')
result = df.iloc[np.setdiff1d(ser.index, ind)]
t1 = time.time()

print str(t1-t0)

t2 = time.time()
res2 = df.loc[~(df=='ggg').apply(np.any, axis=1)]
t3 = time.time()

print str(t3-t2)

pdb.set_trace()