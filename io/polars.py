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

# ## read excel using camline
#

# +
from pathlib import Path

xlfl = Path.home().joinpath('dat/test/cola.xlsx')
wsnm = ['COCA COLA CO']

# +
import pandas as pd

dp = pd.read_excel(
    xlfl,
    sheet_name=wsnm[0],
    engine='calamine',
    dtype_backend='pyarrow',
    skiprows=3,
    nrows=5,
    skipfooter=0,
    usecols='B:D'
)
dp[:2]

# +
import polars as pl

dl = pl.read_excel(
    xlfl,
    sheet_name=wsnm[0],
    engine='calamine',
    read_options={
        'column_names': ['usd', 'fy09', 'fy10'],
        'header_row': 3,
        'skip_rows': 0,
        'n_rows': 5,
        'use_columns': 'B:D',
    },
)

dl[:2]
# -

dp.dtypes
