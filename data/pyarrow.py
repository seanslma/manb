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

import pandas as pd


def pa_mod(
    ds: int | pd.Series,
    divisor: int,
) -> int | pd.Series:
    """
    Calculates remainder after division by a positive divisor

    Args:
        ds: An integer value or a pd.Series with int64[pyarrow] dtype
        divisor: The positive divisor for the modulo operation

    Returns:
        pd.Series: An integer or pd.series containing the modulo results
    """

    if divisor <= 0:
        raise ValueError('Divisor must be a positive integer')

    # # Handle negative values by adding the divisor first
    # val = ds + divisor

    # Check if divisor is a power of 2
    if divisor & (divisor - 1) == 0:
        # Efficient bitwise AND for power-of-2 divisors
        remainder = ds & (divisor - 1)
    else:
        # Slower integer division for non-power-of-2 divisors
        quotient = ds // divisor
        remainder = ds - (quotient * divisor)

    return remainder

    # # Handle cases where remainder is equal to the divisor (represents 0 remainder)
    # if isinstance(remainder, int):
    #     return remainder
    # else:
    #     return remainder.where(remainder != divisor, 0)  # not required?


d = pd.DataFrame({'x': [2, -8, 9]}, dtype='int64[pyarrow]')
print(pa_mod(d, 4))
