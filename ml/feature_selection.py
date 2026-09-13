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
import numpy as np
import polars as pl
from sklearn.svm import SVR, SVC
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import VarianceThreshold, SelectKBest, RFE, f_classif, r_regression, f_regression
from statsmodels.stats.outliers_influence import variance_inflation_factor

np.random.seed(13)

# +
d = pl.DataFrame(
    np.array([
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [0, 1.1, 1.9, 3, 4, 5.1, 6, 7, 7.9, 9, 9.9],
            [0, 0.97, 2, 3, 4.1, 4.9, 6, 7.2, 8.1, 9.1, 10.1],
            [1, 1, 1, 1.1, 1, 1, 1, 0.9, 1, 1, 1.2],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    ]), #+ np.random.rand(5, 11) / 10, 
    orient='col', 
    schema=['x', 'y', 'z', 'a', 't'],
)
X = d.select(pl.exclude('t'))
y = d['t'].cast(pl.Int32)
print(X)

n_features_to_select = 2
ml_type = 'regression'
# -

print(X.corr())

# Variance Threshold
selector = VarianceThreshold(threshold=0.0)
X_ = selector.fit_transform(X)
print(selector.get_support())
print(np.array(X.columns)[selector.get_support()])


# faster variance threshold
def drop_constant_columns(df: pl.DataFrame) -> pl.DataFrame:
    return df.select([
        col for col in df.columns
        if df[col].n_unique() > 1
    ])
X_ = drop_constant_columns(X)
print(X_.columns)


# faster variance threshold
def drop_low_variance_columns(df: pl.DataFrame, threshold: float = 0.0) -> pl.DataFrame:
    stats = df.select([
        pl.var(col).alias(col) for col in df.columns
    ])
    variances = stats.row(0)  # get variances as a list
    return df.select([
        col for col, var in zip(df.columns, variances) if var > threshold
    ])
X_ = drop_low_variance_columns(X)
print(X_.columns)    

# +
# RFE
model = LinearRegression()
rfe = RFE(model, n_features_to_select=2)
rfe.fit(X, y)

# Get indices of selected features
selected_indices = rfe.get_support()
print('lrm indices:', selected_indices)

# +
if ml_type == 'classif':
    model = SVC(kernel='linear')
else:
    model = SVR(kernel='linear')
rfe = RFE(model, n_features_to_select=n_features_to_select)
rfe.fit(X, y)

# Get indices of selected features
selected_indices = rfe.get_support()
print("rfe indices:", selected_indices)
# -

selector = SelectKBest(
    f_regression,
    k=n_features_to_select,
).fit(X, y)
selected_indices = selector.get_support()
print("psn indices:", selected_indices)
print("psn  scores:", selector.scores_)

features = X
f = [
    variance_inflation_factor(features, feature_index)
    for feature_index in range(X.shape[1])
]
f

# super slow
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
if ml_type == 'classif':
    mi_scores = mutual_info_classif(X, y, n_jobs=-1, discrete_features=False, random_state=13)
else:
    mi_scores = mutual_info_regression(X, y, n_jobs=-1, discrete_features=False, random_state=1)
mi_scores

import xgboost as xgb
# model = xgb.XGBClassifier(
#     objective='binary:logistic',  # Default for binary classification
#     eval_metric='logloss',        # Can also use 'auc' or others
# )
# model = xgb.XGBClassifier(
#     objective='multi:softprob',   # Outputs class probabilities
#     eval_metric='mlogloss',       # Multiclass log-loss
#     num_class=3,                  # Replace with actual number of classes
# )
model = xgb.XGBRegressor(
    objective='reg:squarederror',  # Default for regression, minimizes squared error
    eval_metric='rmse',            # Metric for evaluation
)
model.fit(X, y)
importance = model.feature_importances_
print(importance)

import lightgbm as lgb
train_data = lgb.Dataset(data=X.to_arrow(), label=y.to_arrow())
# for small number of features, reduce `num_leaves` to avoid warnings
# for small number of data points, reduce `min_data_in_leave` to avoid warnings
# warnings #1: [Warning] No further splits with positive gain, best gain: -inf
# warnings #2: There are no meaningful features which satisfy the provided configuration. 
# Decreasing Dataset parameters min_data_in_bin or min_data_in_leaf and re-constructing Dataset might resolve this warning.
# params = {
#     'objective': 'binary',
#     'metric': 'binary_logloss', # or 'auc' for AUC score
# }
# params = {
#     'objective': 'multiclass',
#     'metric': 'multi_logloss',  # or 'multi_error'
#     'num_class': 3,             # replace 3 with the actual number of classes
# }
params = {
    'objective': 'regression', 
    'metric': 'rmse', 
    'verbose': -1, # no info messages
    'num_leaves': 2, 
    'min_data_in_leaf': 2,
}
model = lgb.train(params, train_data, num_boost_round=100, )
importance = model.feature_importance(importance_type='gain')
print(importance)

# feature importance is super slow, lgb: 35x faster, xgb: 15x faster
from catboost import CatBoostClassifier, CatBoostRegressor
# model = CatBoostClassifier(verbose=None)
model = CatBoostRegressor(verbose=0)
model.fit(X.to_pandas(), y.to_pandas())
importance = model.get_feature_importance()
print(importance)

# +
# Permutation Importance example
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

# Train a model, Random Forest is a great choice as it's a powerful tree-based model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X.to_pandas(), y.to_pandas())

# Calculate Permutation Importance on the test set to get a more reliable estimate
perm = permutation_importance(model, X.to_pandas(), y.to_pandas(), n_repeats=10, random_state=13)

# Get and sort the `perm.importances_mean` attribute that gives the average importance score
df = pl.DataFrame({
    'feature': X.columns,
    'perm_score': perm.importances_mean,
    'perm_score_std': perm.importances_std,
}).sort('perm_score', descending=True)
print(df)
# -

# embedded Lasso (L1) regularization
from sklearn.linear_model import Lasso
# Initialize and train the Lasso model
model = Lasso(alpha=0.01)
model.fit(X, y)
# Features with a coefficient of 0 are not important
print(model.coef_)
