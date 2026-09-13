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
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
import time
import numpy as np
import pandas as pd
from cachetools import cached, TTLCache

cache=TTLCache(maxsize=float('inf'),ttl=60)
@cached(cache)
def f1(m,n):
    df = d1(m,n)
    return df



# -

def d1(m, n):
    data = np.random.randn(m, n)
    cols = [f'col{j}' for j in range(1,n+1)]
    df = pd.DataFrame(data, columns=cols)
    return df



m = 1000000
n = 100
t0 = time.time()
d1 = f1(m, n)
print(f'time: {time.time() - t0:.3f}')
t0 = time.time()
d2 = f1(m, n)
print(f'time: {time.time() - t0:.3f}')
t0 = time.time()
d3 = f1(m, n)
print(f'time: {time.time() - t0:.3f}')


print(d1.shape)
print(d2.shape)
print(d3.shape)

