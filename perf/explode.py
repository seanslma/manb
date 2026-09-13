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
from typing import Union
import time
import string
import numpy as np
import pandas as pd

from mapu.pandas import pd_ht
pd.DataFrame.ht = pd_ht

def gen_rand_strs(
    rng: np.random._generator.Generator,
    str_cnt: int,
    str_len: tuple[int, int],
    str_chars: list[str],
) -> list[str]:
    str_lens = rng.integers(low=str_len[0], high=str_len[1], size=str_cnt, endpoint=True)
    rand_strs = [''.join(rng.choice(str_chars, size=str_len)) for str_len in str_lens]
    return rand_strs


def gen_str_vals(
    size: int,
    rng: np.random._generator.Generator,
    str_cnt: int = None,
    str_len: Union[int, tuple[int, int]] = None,
    str_chars: list[str] = None,
    col_strs: list[str] = None,
) -> np.ndarray:
    if str_cnt is None:
        str_cnt = 10
    if str_len is None:
        str_len = (5, 5)
    elif isinstance(str_len, int):
        str_len = (str_len, str_len)
    if col_strs is None:
        if str_chars is None:
            str_chars = [c for c in string.ascii_letters + string.digits]
        col_strs = gen_rand_strs(rng, str_cnt, str_len, str_chars)
    val = rng.choice(col_strs, size=size)
    return val


def gen_ts_vals(
    size: int,
    rng: np.random._generator.Generator,
    start_date: str = None,
    end_date: str = None,
    freq: str = None,
    random: bool = False,
) -> np.ndarray:
    if start_date is None:
        start_date = '2024-01-01'
    if end_date is None:
        end_date = '2025-01-01'
    if freq is None:
        freq = 'D'
    if random is None:
        random = False
    val = pd.date_range(start_date, end_date, freq=freq, inclusive='left')[:size]
    if random:
        val = rng.choice(val, size=size)
    return val


def gen_num_vals(
    size: int,
    rng: np.random._generator.Generator,
    low: Union[int, float] = None,
    high: Union[int, float] = None,
    dtype: str = None,
) -> np.ndarray:
    if low is None:
        low = 0
    if high is None:
        high = 2
    func = rng.integers if dtype[0] == 'i' else rng.uniform
    vals = func(low=low, high=high, size=size)
    return vals


def gen_missing_vals(
    vals: np.ndarray,
    rng: np.random._generator.Generator,
    dtype: str,
    missing_pct: float = None,
) -> np.ndarray:
    if missing_pct is None or missing_pct <= 0 or missing_pct >= 1:
        return vals
    if dtype == 's':
        missing_val = None
    elif dtype == 't':
        missing_val = np.datetime64('NaT')
    else:
        missing_val = np.nan
    if dtype == 'i':
        vals = vals.astype(np.float64)
    mask = rng.uniform(size=len(vals)) <= missing_pct
    vals[mask] = missing_val
    return vals


def sanitize_parameters(
    name_prefix: str,
    params: dict,
    par_names: list[str],
):
    if isinstance(params, int):
        cnt = params
        par = {}
    else:
        cnt = params['count']
        par = {
            k: v + [None] * (cnt - len(v)) if isinstance(v, list) else [v] * cnt
            for k, v in params.items()
        }
    if name_prefix in ('i', 'f'):
        par_names += ['dtype']
        par['dtype'] = [name_prefix] * cnt
    default_val = [None] * cnt
    parameters = [
        {key: par.get(key, default_val)[i] for key in par_names}
        for i in range(cnt)
    ]
    col_names = par.get('name')
    if col_names is None or col_names.count(None) > 1 or col_names.count('') > 1:
        col_names = [f'{name_prefix}{i}' for i in range(1, cnt+1)]
    col_missing_pcts = par.get('missing_pct', default_val)
    return col_names, parameters, col_missing_pcts


def gen_rand_df(
    nrow: int,
    str_cols: dict = None,
    ts_cols: dict = None,
    int_cols: dict = None,
    float_cols: dict = None,
    rand_seed: int = 11,
) -> pd.DataFrame:
    col_types = ['s', 't', 'i', 'f']
    inputs = [str_cols, ts_cols, int_cols, float_cols]
    funcs = [gen_str_vals, gen_ts_vals, gen_num_vals, gen_num_vals]
    par_names = [
        ['str_cnt', 'str_len', 'str_chars', 'col_strs'],
        ['start_date', 'end_date', 'freq', 'random'],
        ['low', 'high'],
        ['low', 'high'],
    ]
    df = pd.DataFrame()
    rng = np.random.default_rng(seed=rand_seed)
    for i, params in enumerate(inputs):
        if params is not None:
            col_names, col_params, col_missing_pcts = sanitize_parameters(
                col_types[i], params, par_names[i]
            )
            df = pd.concat([df, pd.DataFrame({
                col: gen_missing_vals(
                    funcs[i](nrow, rng, **col_params[j]),
                    rng,
                    col_types[i],
                    col_missing_pcts[j],
                ) for j, col in enumerate(col_names)
            })], axis=1)
    return df


# -

pd.set_option('display.width', 240)


def get_df():
    return gen_rand_df(
        nrow=10,
        str_cols={
            'count': 2,
            'name': ['id', 'category'],
            'str_len': [8, (5,20)],
            'str_count': [100, 30],
        },
        ts_cols={
            'count': 2,
            'name': ['start_date', 'end_date'],
            'start_date': ['2020-01-01', '2023-01-01'],
            'end_date': ['2023-01-01', '2025-01-01'],
            'freq': 'MS',
            'random': True,
        },
        float_cols={
            'count': 2,
            'low': 0.0,
            'high': 100.0,
            'missing_pct': 0.1,
        },
    )
df = get_df()
print(df[:2])

dc = df.copy()
dg = df.copy()


# +
# ChatGPT solution
def generate_half_hourly(row):
    return pd.date_range(start=row['start_date'], end=row['end_date'], freq='30min')

# Explode the date range into half-hourly timestamps
dc['ts'] = dc.apply(generate_half_hourly, axis=1)

# Explode the DataFrame on the 'ts' column
dc = dc.explode('ts')
dc[:2]

# -

# %%timeit -r 3 -n 7
dg = df.copy()
dg['ts'] = dg.apply(lambda row: pd.date_range(row['start_date'], row['end_date'], freq='30min'), axis=1)
# dz = dg.explode('ts')

dg = df.copy()
dg['ts'] = dg.apply(lambda row: pd.date_range(row['start_date'], row['end_date'], freq='30min'), axis=1)

# %%timeit -r 3 -n 7
dz = dg.explode('ts')

# %%timeit -r 3 -n 7
d1 = df.copy()
d1['ts'] = [
        pd.date_range(start, end, freq='30min')
        for start, end in zip(df['start_date'].values, df['end_date'].values)
    ]
# d1 = d1.explode('ts')

# %%timeit -r 3 -n 7
for start, end in zip(df['start_date'].values, df['end_date'].values): pass


# ## explode 

# +
def explode_old(df, start_date_col, end_date_col, freq):
    t0 = time.time()
    df['ts'] = [
        pd.date_range(start=row[start_date_col], end=row[end_date_col], freq=freq)
        for (_, row) in df.iterrows()
    ]
    print(f'Old  create list time: {time.time()-t0:.3f}')

    t0 = time.time()
    df = df.explode('ts')
    print(f'Old explode list time: {time.time()-t0:.3f}')
    return df

def explode_new(df, start_date_col, end_date_col, freq):
    # Get exploded timestamp column
    # t0 = time.time()
    dt = pd.concat([
        pd.DataFrame({'i': i, 'ts': pd.date_range(start=s, end=e, freq=freq)})
        for i, (s, e) in enumerate(zip(df[start_date_col], df[end_date_col]))
    ]).set_index('i').rename_axis(None, axis=0)
    # print(f'New  create list time: {time.time()-t0:.3f}')

    # Re-sampling df based on new timestamp column
    # t0 = time.time()
    df = df.reindex(dt.index).assign(ts=dt.ts)
    # print(f'New      reindex time: {time.time()-t0:.3f}')
    return df


# -

start_date_col = 'start_date'
end_date_col = 'end_date'
freq = '30min'

# %%timeit -r 8 -n 10
# t0 = time.time()
d2 = explode_new(df, 'start_date', 'end_date', '30min')
# t2 = time.time() - t0
# print(f'New time {t2:.3f}')

t0 = time.time()
d1 = explode_old(df, 'start_date', 'end_date', '30min')
t1 = time.time() - t0
print(f'Old time {t1:.3f}')

# %%time
df['ts'] = [
    pd.date_range(start=row[start_date_col], end=row[end_date_col], freq=freq)
    for (_, row) in df.iterrows()
]

# %%time
d = df.explode('ts')

df[:2]

# %%time
d = df.get(['ts']).reset_index(names=['id']).explode('ts')

# # %%time
d = df.get(['ts']).reset_index(drop=True).rename_axis('i', axis=0).reset_index()
d[:2]

# # %%timeit -r 10 -n 100
dt = pd.concat([
    pd.DataFrame({'i': key, 'ts': row['ts']})
    for (key, row) in d.iterrows()
]).set_index('i').rename_axis(None, axis=0)
dt[:2]

# %%timeit -r 10 -n 100
dt = pd.concat([
    pd.DataFrame({'i': i, 'ts': ts})
    for i, ts in zip(d['i'].values, d['ts'].values)
]).set_index('i').rename_axis(None, axis=0)
# dt[:2]

# %%time
d = df.drop(columns='ts').reindex(dt.index)
d['ts'] = dt.ts
d[:2]

# # %%timeit
# explode `ts` column
d = df.get(['ts']).reset_index(drop=True)
dt = pd.concat([
    pd.DataFrame({'i': key, 'ts': row['ts']})
    for (key, row) in d.iterrows()
]).set_index('i').rename_axis(None, axis=0)
d = df.drop(columns='ts').reindex(dt.index)
d['ts'] = dt.ts
d[:2]

# # %%timeit
# explode `ts` column and expand
dt = pd.concat([
    pd.DataFrame({'i': key, 'ts': pd.date_range(start=row['start_date'], end=row['end_date'], freq='30min')})
    for (key, row) in df.iterrows()
]).set_index('i').rename_axis(None, axis=0)
dx = df.drop(columns='ts').reindex(dt.index)
dx['ts'] = dt.ts
dx[:2]


def explode_df_column(df):
    d = df.get(['ts']).reset_index(drop=True).rename_axis('i', axis=0).reset_index()
    dt = pd.concat([
        pd.DataFrame({'i': i, 'ts': ts})
        for (i, ts) in zip(d['i'].values, d['ts'].values)
    ]).set_index('i').rename_axis(None, axis=0)
    df = df.drop(columns='ts').reindex(dt.index)
    df['ts'] = dt.ts
    return df
dd = df.copy()
dd['ts'] = [
    pd.date_range(start=row[start_date_col], end=row[end_date_col], freq=freq)
    for (_, row) in dd.iterrows()
]

# %%timeit -r 3 -n 10
dx = dd.copy()
dy = explode_df_column(dx)

# %%timeit -r 3 -n 10
dz = dd.explode('ts')
dz.shape

dy.equals(dz)

# +
# %%timeit -r 3 -n 10
# Create a DataFrame with new index and exploded ts column
dt = pd.concat([
    pd.DataFrame({'i': i, 'ts': pd.date_range(start, end, freq='30min')})
    for i, (start, end) in enumerate(zip(df['start_date'], df['end_date']))
]).set_index('i').rename_axis(None, axis=0)

# Resample original df based on new index and add the exploded ts column
dn = df.reindex(dt.index).assign(ts=dt.ts)
# -

(703+691)/49.8

# ## explode perf

# +
import numpy as np
import pandas as pd
import timeit

n = 500
nums = np.random.randint(0, n, size=n)  # 0 to 99
df = pd.DataFrame({
    'A': [list(pd.date_range(pd.to_datetime('2026-01-01') + pd.DateOffset(days=i), periods=nums[i]+1)) for i in range(n)],
    'B': np.random.rand(n),
})
df.ht()

# Yours (with empty-list fix)
def explode_df_column1(df, col, drop_index=False):
    """
    Explode df col from list to single value.
    The col must not be in the df index levels.
    """
    d = df.get([col]).reset_index(drop=True).rename_axis('i', axis=0).reset_index()
    dt = pd.concat([
        pd.DataFrame({'i': i, 'ts': ts})
        for (i, ts) in zip(d['i'].values, d[col].values)
    ]).set_index('i').rename_axis(None, axis=0)
    df = df.drop(columns=col).reindex(dt.index)
    df[col] = dt.ts
    return df.reset_index(drop=True)
    
def explode_df_column2(df, col, drop_index=False):
    """I've seen teams scramble when a model API goes down mid-demo. Local fallback models have saved us more than once, especially when latency or uptime really matters.
    Explode df col from list to single value.
    The col must not be in the df index levels.
    """
    if not drop_index:
        index_names = df.index.names
    df_explode = pd.concat([
        pd.DataFrame({'i': i, col: ts})
        for (i, ts) in enumerate(df[col].values)
    ]).set_index('i').rename_axis(None, axis=0)
    df = (
        df
        .reset_index(drop=drop_index)
        .drop(columns=col)
        .reindex(df_explode.index)
        .reset_index(drop=True)
        .assign(**{col: df_explode[col].values})
    )
    if not drop_index:
        df = df.set_index(index_names)
    return df


# -

# %%timeit -r 3 -n 10
d1 = explode_df_column1(df, 'A', True)

# %%timeit -r 3 -n 10
d2 = explode_df_column2(df, 'A', True)

# %%timeit -r 3 -n 10
d3 = df.explode('A', ignore_index=True)

d1 = explode_df_column1(df, 'A', True)
d2 = explode_df_column2(df, 'A', True)
d3 = df.explode('A', ignore_index=True)
print(d1.equals(d2))
print(d1.equals(d3))
print(d2.equals(d3))

t0 = time.time()
df1 = pd.DataFrame({
    'A': [pd.date_range(pd.to_datetime('2026-01-01') + pd.DateOffset(days=i), periods=nums[i]+1) for i in range(n)],
    'B': np.random.rand(n),
})
print(f't: {time.time() - t0:.3f}')
t0 = time.time()
df2 = pd.DataFrame({
    'A': [list(pd.date_range(pd.to_datetime('2026-01-01') + pd.DateOffset(days=i), periods=nums[i]+1)) for i in range(n)],
    'B': np.random.rand(n),
})
print(f't: {time.time() - t0:.3f}')
t0 = time.time()
d1 = df1.explode('A', ignore_index=True)
print(f't: {time.time() - t0:.3f}')
t0 = time.time()
d2 = df2.explode('A', ignore_index=True)
print(f't: {time.time() - t0:.3f}')

from mapu.pandas import df_diffs
df_diffs(d1, d3.get(['B', 'A']).reset_index(drop=True))

from mapu.data import gen_rand_df
d = gen_rand_df(
    nrow=100,
    str_cols={
        'count': 2,
        'name': ['id', 'category'],
        'str_len': [8, (5,20)],
        'str_count': [100, 30],
    },
    ts_cols={
        'count': 2,
        'name': ['start_date', 'end_date'],
        'start_date': ['2020-01-01', '2023-01-01'],
        'end_date': ['2023-01-01', '2025-01-01'],
        'freq': 'MS',
        'random': True,
    },
    float_cols={
        'count': 2,
        'low': 0.0,
        'high': 100.0,
        'missing_pct': 0.1,
    },
)
d[:2]

import time
t0 = time.time()
df = d.copy()
df.ht(1)
df['ts'] = [
    pd.date_range(start, end, freq='30min')
    for start, end in zip(df['start_date'].values, df['end_date'].values)
]
print(f'time list {time.time() - t0:.3f} seconds')
t1 = time.time()
d1 = df.explode('ts', ignore_index=True)
print(f'time explode {time.time() - t1:.3f} seconds')
print(f'time total {time.time() - t0:.3f} seconds')
d1.ht(1,c=-1,w=-1)


# +
def explode_df_column(df, col, drop_index=False):
    """
    Explode df col from list to single value.
    The col must not be in the df index levels.
    """
    if not drop_index:
        index_names = df.index.names
        new_index_names = [f'IdxName_{i}' for i in range(len(index_names))]
        df.index = df.index.set_names(new_index_names)
    df_explode = pd.concat([
        pd.DataFrame({'i': i, col: ts})
        for (i, ts) in enumerate(df[col].values)
    ]).set_index('i').rename_axis(None, axis=0)
    df = (
        df
        .reset_index(drop=drop_index)
        .drop(columns=col)
        .reindex(df_explode.index)
        .reset_index(drop=True)
        .assign(**{col: df_explode[col].values})
    )
    if not drop_index:
        df = df.set_index(new_index_names).rename_axis(index_names)
    return df

import time
df = d.copy()
t0 = time.time()
df['ts'] = [
    pd.date_range(start, end, freq='30min')
    for start, end in zip(df['start_date'].values, df['end_date'].values)
]
print(f'time list {time.time() - t0:.3f} seconds')
t1 = time.time()
d1 = explode_df_column(df, 'ts')
print(f'time explode {time.time() - t1:.3f} seconds')
print(f'time total {time.time() - t0:.3f} seconds')    
# -


