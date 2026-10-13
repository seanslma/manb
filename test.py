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

import os
user_home_path = os.path.expanduser('~')
print(f'User home directory: {user_home_path}')

# +

from pathlib import Path
user_home_path = Path.home()
print(f'Users home directory: {user_home_path}')


# -

class Car:
    """
    A simple Docstring for our Car class
    """
    pass


print(Car.__doc__)

# +
from datetime import datetime, timedelta

def get_year_months1(
    start_date: str,
    end_date: str,
) -> list[tuple[int, int]]:
    """
    Return a list of (year, month) tuples from start_date up to end_date.

    Parameters:
    -----------
    start_date : str
        Start date in 'YYYY-MM-DD' format
    end_date : str
        End date in 'YYYY-MM-DD' format (exclusive).

    Returns:
    --------
    list of tuples
        A list of (year, month) tuples for each month in the range.
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # total months since year 0, as integers — lets us do arithmetic directly
    start_idx = start.year * 12 + (start.month - 1)
    end_idx = end.year * 12 + (end.month - 1)
    if end.day > 1:
        end_idx += 1  # end_date's own month is partially included, so keep it
    print(start_idx, end_idx)

    return [
        (idx // 12, idx % 12 + 1)
        for idx in range(start_idx, end_idx)
    ]

def get_year_months2(
    start_date: str,
    end_date: str,
) -> list[tuple[int, int]]:
    """
    Return a list of (year, month) tuples from start_date to end_date.

    Parameters:
    -----------
    start_date : str
        Start date in 'YYYY-MM-DD' format.
    end_date : str
        End date in 'YYYY-MM-DD' format (exclusive).

    Returns:
    --------
    list of tuples
        A list of (year, month) tuples for each month in the range.
    """
    start = datetime.strptime(start_date, '%Y-%m-%d').replace(day=1)
    end = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=1)
    end_ym = (end.year, end.month)

    year_months = []
    current = start
    while (current.year, current.month) <= end_ym:
        year_months.append((current.year, current.month))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return year_months
    


# -

print(get_year_months1('2026-01-31', '2026-02-01'))
print(get_year_months2('2026-01-31', '2026-02-01'))

print(get_year_months1('2026-01-01', '2026-02-01'))
print(get_year_months2('2026-01-01', '2026-02-01'))

from pathlib import Path
year = 2026
month = 2
Path('c:/test', f'_zips/{year}/{month:02}', 't%23est%23.zip').name.replace('%23', '#')

import polars as pl
import mspu.polars
file = '/home/sma/dat/nem/dispatch_price/year=2025/month=12/part-0.parquet'
d = pl.read_parquet(file)
d.ht()

import polars as pl
import mspu.polars
import nemas as nm
file = '/home/sma/dat/nem/_mmsdm/2026/01/PUBLIC_ARCHIVE#DISPATCHPRICE#FILE01#202601010000.zip'
d0 = nm.read_zip(file)
d0['dispatch_price'].ht()
