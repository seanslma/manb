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

# # Rounding values with constraints

# **Controlled Rounding**: 
# Rounding values to integers while controlling the rounding error across multiple constraints simultaneously.
#
# **Controlled Rounding** doesn't just round each cell independently. It tries to ensure things like:
# - each cell becomes an integer (often 0/1)
# - row totals are close to the original row totals
# - column totals are close to the original column totals
# - grand total is preserved or rounded consistently
# - possibly cumulative/subtotal constraints are preserved
# - cells that are exactly zero remain zero
#
# Normal rounding: doesn't care whether the resulting **totals** make sense.
#
# Controlled rounding says: Round individual cells while controlling rows + columns + totals + subtotals
#
# This is particularly important for statistical tables, financial data, population counts, percentages, etc., where independently rounded cells can produce inconsistent totals.
#
# For example:
#
# > **cumulative row sums must also stay within the floor/ceil of the cumulative fractional sums.**
#
# That's more restrictive than basic controlled rounding. You could think of it as:
#
# **binary controlled rounding + marginal constraints + cumulative constraints.**
#
# This distinction is important because **basic controlled rounding may be feasible while your additional cumulative constraints make the problem infeasible**.
#
# If you're asking because you're considering using a **known controlled-rounding algorithm/library** for your matrix problem, I can also explain the main algorithms (e.g. **linear programming, network flow, bipartite matching, and Cox controlled rounding**) and which one fits your constraints.
#

import numpy as np
from ortools.sat.python import cp_model


def relaxed_controlled_round(
    A, 
    tol=1e-4, 
    scale=10000, 
    col_penalty_weight=1e4, 
    row_penalty_weight=1e3, 
    elem_dev_weight=1e1,
    col_step_penalty=False,
    elem_penalty=False,
):
    n, m = A.shape
    base = np.floor(A).astype(int)
    frac = A - base
    K = int(np.ceil(frac.sum()))

    model = cp_model.CpModel()

    # X[i,j] only exists where frac > 0
    X = {}
    for i in range(n):
        for j in range(m):
            X[i, j] = model.NewBoolVar(f"x[{i},{j}]") if frac[i, j] > tol else None

    def col(j):
        return [X[i, j] for i in range(n) if X[i, j] is not None]

    def row(i):
        return [X[i, j] for j in range(m) if X[i, j] is not None]

    # total count constraint
    model.Add(sum(v for i in range(n) for v in row(i)) == K)

    # cumulative row constraints
    row_frac = frac.sum(axis=1)
    cum_frac = np.cumsum(row_frac)
    running = []
    for i in range(n):
        running.extend(row(i))
        lo = int(np.floor(cum_frac[i] - tol))
        hi = int(np.ceil(cum_frac[i] + tol))
        model.Add(sum(running) >= lo)
        model.Add(sum(running) <= hi)

    # soft column penalty
    col_penalty_terms = []
    col_frac = frac.sum(axis=0)
    if col_step_penalty:
        for j in range(m):
            vars_j = col(j)
            target_j = int(round(col_frac[j] * scale))
            Xsum_j_scaled = sum(v * scale for v in vars_j) if vars_j else 0
    
            # Dj (scaled), as an absolute deviation
            Dj = model.NewIntVar(0, scale * n, f"D{j}")
            model.AddAbsEquality(Dj, Xsum_j_scaled - target_j)
    
            # indicator: is Dj >= 1*scale (i.e. Dj_real >= 1)?
            z = model.NewBoolVar(f"z{j}")
            model.Add(Dj >= scale).OnlyEnforceIf(z)
            model.Add(Dj < scale).OnlyEnforceIf(z.Not())
    
            Pj = model.NewIntVar(0, scale * n, f"P{j}")
            model.Add(Pj == Dj).OnlyEnforceIf(z)
            model.Add(Pj == 0).OnlyEnforceIf(z.Not())
    
            col_penalty_terms.append(Pj)
    else:
        # soft col penalty, abs(colsum(frac) - colsum(X)) * col_weight, no threshold
        for j in range(m):
            vars_j = col(j)
            target_j = int(round(col_frac[j] * scale))
            Xsum_j_scaled = sum(v * scale for v in vars_j) if vars_j else 0
    
            Dj = model.NewIntVar(0, scale * n, f"D{j}")
            model.AddAbsEquality(Dj, Xsum_j_scaled - target_j)
            col_penalty_terms.append(Dj)
        
    # soft row penalty, abs(rowsum(frac) - rowsum(X)) * row_weight, no threshold
    row_penalty_terms = []
    for i in range(n):
        vars_i = row(i)
        target_i = int(round(row_frac[i] * scale))
        Xsum_i_scaled = sum(v * scale for v in vars_i) if vars_i else 0

        Ri = model.NewIntVar(0, scale * m, f"R{i}")
        model.AddAbsEquality(Ri, Xsum_i_scaled - target_i)
        row_penalty_terms.append(Ri)

    if elem_penalty:
        # elementwise |X - frac| term, scaled to match integer domain
        # abs(X-frac) = frac + X*(1-2*frac); the "frac" constant part doesn't
        # affect the argmin, so we only need the X-dependent part in the objective
        elem_dev_terms = []
        for i in range(n):
            for j in range(m):
                if X[i, j] is not None:
                    coef = int(round((1 - 2 * frac[i, j]) * scale))
                    elem_dev_terms.append(X[i, j] * coef)
    else:
        # cumulative-per-column penalty: 
        # minimize sum_j sum_i |cum_frac[i,j] - cum_X[i,j]|
        cum_dev_terms = []
        cum_frac_cols = np.cumsum(frac, axis=0)  # shape (n, m), cumulative down each column
        for j in range(m):
            running = []
            for i in range(n):
                running.append(X[i, j] if X[i, j] is not None else 0)
                target = int(round(cum_frac_cols[i, j] * scale))
                Xsum_scaled = sum(v * scale for v in running)
    
                Cij = model.NewIntVar(0, scale * n, f"C[{i},{j}]")
                model.AddAbsEquality(Cij, Xsum_scaled - target)
                cum_dev_terms.append(Cij)
            
    # minimize sum of 
    # - col total not match with rounded value
    # - row total not match with rounded value
    # - element deviations
    model.Minimize(
        sum(t * col_penalty_weight for t in col_penalty_terms)
        + sum(t * row_penalty_weight for t in row_penalty_terms)
        + (
            sum(t * elem_dev_weight for t in elem_dev_terms) if elem_penalty 
            else sum(t * elem_dev_weight for t in cum_dev_terms)
          )
    )

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise ValueError("infeasible")

    sol = np.zeros_like(A, dtype=int)
    for i in range(n):
        for j in range(m):
            if X[i, j] is not None:
                sol[i, j] = solver.Value(X[i, j])
    return frac, sol


# +
A = np.array([
    [1.2, 0.7], 
    [0.9, 1.4],
])

frac, sol = relaxed_controlled_round(A)
print(frac)
print(np.sum(frac))
print(sol)
# -

A = np.array([
    [20397.9652,
14731.5307,
14853.5355,
 9025.5454
],
    [15452.0905,
11159.8797,
11249.0033,
 6833.4149],
]).T
frac, sol = relaxed_controlled_round(A)
print(frac)
print(np.sum(frac))
print(sol)

frac.sum(axis=1)

A = np.array([
    [0.0000,
     0.0000,
  3452.0535,
 13715.8174,
 18026.1838
],
    [17448.5591,
 17636.9015,
   914.5394,
     0.0000,
     0.0000
    ],
]).T
frac, sol = relaxed_controlled_round(A)
print(frac)
print(np.sum(frac))
print(sol)

A = np.array([
    [147.2486757,
101.4170847,
104.7075579,
62.5189908
],
    [4328.452971,
3154.271113,
3181.182483,
2043.078313
    ],
    [10025.0847,
7086.26907,
7021.399741,
4343.941698
    ],    
]).T
frac, sol = relaxed_controlled_round(A, elem_penalty=True)
print(frac)
print(np.sum(frac))
print(sol)
print(frac.sum(axis=1))
print(frac.sum(axis=0))

[[0.2486757 0.452971  0.0847   ]
 [0.4170847 0.271113  0.26907  ]
 [0.7075579 0.182483  0.399741 ]
 [0.5189908 0.078313  0.941698 ]]
4.572398099999049
[[0 1 0]
 [1 0 0]
 [0 0 1]
 [1 0 1]]
[0.7863467 0.9572677 1.2897819 1.5390018]
[1.8923091 0.98488   1.695209 ]

# ## one col case

# +
import numpy as np
from ortools.sat.python import cp_model

def relaxed_controlled_round_1col(a, tol=1e-4, scale=10000, dev_weight=1e1):
    a = np.asarray(a)
    n = a.shape[0]
    base = np.floor(a).astype(int)
    frac = a - base
    K = int(np.ceil(frac.sum() - tol))

    model = cp_model.CpModel()

    X = [
        model.NewBoolVar(f"x[{i}]") 
        if frac[i] > tol else None 
        for i in range(n)
    ]

    def val(i):
        return X[i] if X[i] is not None else 0

    # total count constraint
    model.Add(sum(val(i) for i in range(n)) == K)

    # cumulative constraints (this is the only real structural constraint here)
    cum_frac = np.cumsum(frac)
    running = []
    for i in range(n):
        running.append(val(i))
        lo = int(np.floor(cum_frac[i] - tol))
        hi = int(np.ceil(cum_frac[i] + tol))
        model.Add(sum(running) >= lo)
        model.Add(sum(running) <= hi)

    # elementwise deviation term = |X[i] - frac[i]|, linear in X since frac is constant
    # (this also *is* the row-penalty term, since each row has only one cell)
    dev_terms = []
    for i in range(n):
        if X[i] is not None:
            coef = int(round((1 - 2 * frac[i]) * scale))
            dev_terms.append(X[i] * coef)

    model.Minimize(sum(t * dev_weight for t in dev_terms))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise ValueError("infeasible")

    sol = np.array([solver.Value(X[i]) if X[i] is not None else 0 for i in range(n)])
    return frac, sol


# -

a = np.array(
    [
        325.7612,
        329.2385,
        333.0003,
        333.0003,
    ]
)
frac, sol = relaxed_controlled_round_1col(a)
print(frac)
print(np.sum(frac))
print(sol)
