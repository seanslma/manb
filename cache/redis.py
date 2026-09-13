# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: p12
#     language: python
#     name: python3
# ---

import redis
r = redis.Redis('localhost', 6379, 0)
print(r.ping())
print(r.keys("*"))

r.delete('k')

import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import time

# +
#df to parquet bytes
t0 = time.time()
table = pa.Table.from_pandas(d)
parquet_stream = io.BytesIO()
pq.write_table(table, parquet_stream)
parquet_bytes = parquet_stream.getvalue()
print(f'dump: {time.time() - t0:.3f} size: {len(parquet_bytes)/1024/1024} MB')

#parquet bytes to df
t0 = time.time()
parquet_stream = io.BytesIO(parquet_bytes)
parquet_table = pq.read_table(parquet_stream)
df_restored = parquet_table.to_pandas()
print(f'pq load: {time.time() - t0:.3f}')
# -

chunk_size = 1024 * 1024  # 1 MB
num_chunk = -(len(buf) // -chunk_size)
num_chunk

import time
t0 = time.time()
chunk_size = 1024 * 1024  # 1 MB
num_chunk = -(len(buf) // -chunk_size)
r.set('df', num_chunk)
for i in range(0, len(buf), chunk_size):
    chunk = buf[i:i + chunk_size]
    r.set(f'df{i}', chunk)
print(f'time: {time.time() - t0:.3f}')

t0 = time.time()
n_chunk = r.get('df')
chunks = [r.get(f'df{i}') for i in range(n_chunk)]
bf = b''.join(chunks)
print(f'time: {time.time() - t0:.3f}')

df = pickle.loads(bf)
df.head(2)

r.hset('hkey',mapping={'a':'1', 'b':'2'})

r.hdel('hkey', 'a', 'b')

r.hmget('hkey', ['a', 'b'])

r.setrange('k',2, 'a12345')

r.getbit('k', 2)

# +
import io
import pickle
from functools import partial
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.feather as pf
import time

test_redis = True

def timeit(func, n=5):
    t0 = time.time()
    for i in range(n):
        func()
    return (time.time() - t0) / n

def pkldumps(d):
    b = pickle.dumps(d)
    if test_redis:
        r.set('df', b)
    return b

def pklloads(b):
    if test_redis:
        b = r.get('df')
    return pickle.loads(b)

def paqdumps(d):
    buf = io.BytesIO()
    #pq.write_table(pa.Table.from_pandas(d), buf)
    pq.write_table(d, buf, compression='zstd')
    b = buf.getvalue()
    if test_redis:
        r.set('df', b)
    return b

def paqloads(b):
    if test_redis:
        b = r.get('df')
    buf = pa.BufferReader(b)
    #return pq.read_table(buf).to_pandas()
    return pq.read_table(buf)

def feadumps(d):
    buf = io.BytesIO()
    #d.to_feather(buf)
    pf.write_feather(d, buf, compression='zstd')
    b = buf.getvalue()
    if test_redis:
        r.set('df', b)
    return b

def fealoads(b):
    if test_redis:
        b = r.get('df')
    buf = io.BytesIO(b)
    #return pd.read_feather(buf)
    return pf.read_table(buf)

def hdfdumps(d):
    buf = io.BytesIO()
    d.to_hdf(buf, 'bar', mode='w') #cannot be io stream
    return buf.getvalue()

def hdfloads(b):
    buf = io.BytesIO(b)
    return pd.read_hdf(buf, 'bar', mode='r')

dc = {
    # 'pickle': [pklloads, pkldumps],
    # 'feather': [fealoads, feadumps],
    'parquet': [paqloads, paqdumps],
    #'hdf': [hdfloads, hdfdumps],  not supported
}

result = []
for name, (loads, dumps) in dc.items():
    print(name)
    b = dumps(df)
    s = len(b) / 1024 / 1024
    result.append([name, timeit(lambda: dumps(df)), timeit(lambda: loads(b)), s])
dt = pd.DataFrame(result, columns=['name', 'dump', 'load', 'MB'])
print(dt.round(1).to_string(index=False))
# -

print(dt.round(1).to_string(index=False))


# +
def paqdumps(d, i):
    buf = io.BytesIO()
    if i==0:
        # 3.15 s ± 88.8 ms
        d.to_parquet(buf)
    else:
        # 3.09 s ± 126 ms
        table = pa.Table.from_pandas(d)
        pq.write_table(table, buf)
    return buf.getvalue()

def paqloads(b, i):
    if i==0:
        # 1.79 s ± 18.9 ms
        buf = io.BytesIO(b)
        f = pd.read_parquet(buf)
    elif i==1:
        # 1.75 s ± 20.3 ms
        buf = pa.BufferReader(b)
        f = pd.read_parquet(buf)
    elif i==2:
        # 1.83 s ± 15.5 ms, to_pandas is slow
        buf = io.BytesIO(b)
        f = pq.read_pandas(buf).to_pandas()
    elif i==3:
        # 1.72 s ± 27.2 ms
        buf = pa.BufferReader(b)
        f = pq.read_pandas(buf).to_pandas()
    elif i==4:
        # 1.77 s ± 72.9 ms
        buf = io.BytesIO(b)
        f = pq.read_table(buf).to_pandas()
    elif i==5:
        # 1.70 s ± 21.8 ms
        buf = pa.BufferReader(b)
        f = pq.read_table(buf).to_pandas()
    return f

for i in range(2):
    t0 = time.time()
    b = paqdumps(d, i)
    print(f'dump {i}: {time.time() - t0:.3f}')
for i in range(6):
    t0 = time.time()
    f = paqloads(b, i)
    print(f'load {i}: {time.time() - t0:.3f}')
# -

# %%timeit -r 3 -n 5
b = paqdumps(d, 0)

# # %%timeit -r 3 -n 5
b = paqdumps(d, 1)

# # %%timeit -r 3 -n 5
f0 = paqloads(b, 0)

# # %%timeit -r 3 -n 5
f1 = paqloads(b, 1)

# %%timeit -r 3 -n 5
f2 = paqloads(b, 2)

# %%timeit -r 3 -n 5
f3 = paqloads(b, 3)

# %%timeit -r 3 -n 5
f3 = paqloads(b, 4)

# # %%timeit -r 3 -n 5
f3 = paqloads(b, 5)

# %%timeit -r 3 -n 5
_ = pa.Table.from_pandas(d)
