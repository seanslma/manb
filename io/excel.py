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

# +
import pandas as pd
import polars as pl

from pathlib import Path
from mapy.tst.dataframe import gen_rand_df

dir = Path.home().joinpath('dat')
# -

df = gen_rand_df(
    nrow=100000,
    str_cols={
        'count': 3,
        'name': ['s1', 's2', 's3'],
        'str_len': [10, (1,15), (1,50)],
        'str_count': [1000, 500, 100],
    },
    ts_cols={
        'count': 2,
        'name': ['t1', 't2'],
        'start_date': ['2020-01-01', '2021-01-01'],
        'end_date': ['2021-01-01', '2022-01-01'],
        'freq': 's',
        },
    float_cols={
        'count': 3,
        'name': [f'f{i}' for i in range(1, 4)],
        'low': 0,
        'high': 1,
    },
)
df[:2]

# +

xl = pd.ExcelWriter(dir.joinpath('test_xl.xlsx'))
df.to_excel(xl, index=False)
xl.close()
# -

df.to_excel(dir.joinpath('test_df.xlsx'), sheet_name='df', index=False)


