# ---
# jupyter:
#   jupytext:
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

import polars as pl
import nemas as nm
import mspu.polars
from pathlib import Path

path = Path('~/dat/nem').expanduser()

filepath = path / 'PUBLIC_ARCHIVE#DISPATCHPRICE#FILE01#202606010000.zip'
d = nm.read_zip(filepath, drop_metadata_columns=False)
for k,v in d.items():
    print(k)
    v.ht()

filepath = path / 'PUBLIC_ARCHIVE#DISPATCHLOAD#FILE01#202606010000.zip'
d = nm.read_zip(filepath, drop_metadata_columns=False)
for k,v in d.items():
    print(k)
    v.ht(c=9)

filepath = path / 'PUBLIC_ARCHIVE#DISPATCH_UNIT_SCADA#FILE01#202606010000.zip'
d = nm.read_zip(filepath, drop_metadata_columns=False)
for k,v in d.items():
    print(k)
    v.ht()

filepath = path / 'PUBLIC_DISPATCHIS_20260601.zip'
d = nm.read_zip(filepath, drop_metadata_columns=False)
for k,v in d.items():
    print(k)
    v.ht()
