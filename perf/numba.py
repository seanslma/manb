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
#     display_name: dev
#     language: python
#     name: python3
# ---

# +
import numpy as np
from numba import njit, prange

np.random.seed(11)
ar = np.random.rand(100, 1000)


def calculate_distances1(arr):
    m = arr.shape[0]
    n = arr.shape[1]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            v = 0.0
            for k in range(n):
                v += abs(arr[i, k] - arr[j, k])
            dist_arr[i, j] = v
            dist_arr[j, i] = v
    return dist_arr
# 2.68 s ± 16.8 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)


def calculate_distances2(arr):
    m = arr.shape[0]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            dist_arr[i, j] = np.linalg.norm(arr[i] - arr[j], 1)
            dist_arr[j, i] = dist_arr[i, j]
    return dist_arr
# 40.7 ms ± 1.5 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)


@njit(cache=True)
def calculate_distances3(arr):
    m = arr.shape[0]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            dist_arr[i, j] = np.linalg.norm(arr[i] - arr[j], 1)
            dist_arr[j, i] = dist_arr[i, j]
    return dist_arr
# 10.9 ms ± 507 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)


@njit('float64[:,::1](float64[:,::1])', cache=True)
def calculate_distances4(arr):
    m = arr.shape[0]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            dist_arr[i, j] = np.linalg.norm(arr[i] - arr[j], 1)
            dist_arr[j, i] = dist_arr[i, j]
    return dist_arr
# 10.5 ms ± 208 µs per loop per loop (mean ± std. dev. of 7 runs, 10 loops each)


@njit('float64[:,::1](float64[:,::1])', cache=True)
def calculate_distances5(arr):
    m = arr.shape[0]
    n = arr.shape[1]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            v = 0.0
            for k in range(n):
                v += abs(arr[i, k] - arr[j, k])
            dist_arr[i, j] = v
            dist_arr[j, i] = v
    return dist_arr
# 8.2 ms ± 163 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)


@njit('float64[:,::1](float64[:,::1])', cache=True, parallel=True, nogil=True)
def calculate_distances6(arr):
    m = arr.shape[0]
    n = arr.shape[1]
    dist_arr = np.zeros((m, m))
    for i in prange(m):
        for j in range(i):
            v = 0.0
            for k in range(n):
                v += abs(arr[i, k] - arr[j, k])
            dist_arr[i, j] = v
            dist_arr[j, i] = v
    return dist_arr
# 122 ms ± 10.2 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
# 3.68 ms ± 157 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)


# -

# %%timeit -r 3 -n 7
d1 = calculate_distances1(ar)

# %%timeit -r 3 -n 7
d1 = calculate_distances2(ar)

# %%timeit -r 3 -n 7
d1 = calculate_distances3(ar)

# %%timeit -r 3 -n 7
d1 = calculate_distances4(ar)

# %%timeit -r 3 -n 7
d1 = calculate_distances5(ar)

# %%timeit -r 3 -n 7
d1 = calculate_distances6(ar)
