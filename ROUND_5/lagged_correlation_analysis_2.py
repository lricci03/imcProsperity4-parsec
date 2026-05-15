import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from statsmodels.tsa.stattools import adfuller, coint


# ================= Analysis of CHOCOLATE and VANILLA correlation ====================

# Load data
prices_1 = pd.read_csv("../prices_round_5.csv")

# Filter snacks
ProteinSnackPacks = [
    'SNACKPACK_CHOCOLATE',
    'SNACKPACK_VANILLA',
    'SNACKPACK_PISTACHIO',
    'SNACKPACK_STRAWBERRY',
    'SNACKPACK_RASPBERRY',
]

snack_data = prices_1[prices_1['product'].isin(ProteinSnackPacks)].copy()

# Build merged dataframe
product = ProteinSnackPacks[0]
snackpacks_prices_df = snack_data[snack_data['product'] == product][['timestamp']].copy()

for product in ProteinSnackPacks:
    new_df = snack_data[snack_data['product'] == product][['timestamp', 'mid_price']].copy()
    new_df = new_df.rename(columns={"mid_price": product})
    snackpacks_prices_df = snackpacks_prices_df.merge(new_df, how='left', on='timestamp')

df = snackpacks_prices_df.drop('timestamp', axis=1).dropna().reset_index(drop=True)

c = df['SNACKPACK_CHOCOLATE'].values
v = df['SNACKPACK_VANILLA'].values

# ════════════════════════════════════════════════════════════════
# STRATEGY 1 — check that residuals of c(t-1) -> v(t) are mean-reverting
# ════════════════════════════════════════════════════════════════

# Fit v(t) ~ c(t-1)
c_lag = c[:-1].reshape(-1, 1)
v_curr = v[1:]

reg1 = LinearRegression().fit(c_lag, v_curr)
residuals1 = v_curr - reg1.predict(c_lag)

adf_stat, adf_p, _, _, crit, _ = adfuller(residuals1)
print("── Strategy 1: ADF on residuals of c(t-1) → v(t) ──")
print(f"  ADF statistic : {adf_stat:.4f}")
print(f"  p-value       : {adf_p:.4f}")
print(f"  Critical values: {crit}")
print(f"  Mean-reverting : {'YES ✓' if adf_p < 0.05 else 'NO ✗'}")


# ════════════════════════════════════════════════════════════════
# STRATEGY 2 — check stationarity of spread and cointegration
# ════════════════════════════════════════════════════════════════

# Fit beta: v(t) ~ beta * c(t), compute spread
reg2 = LinearRegression().fit(c.reshape(-1, 1), v)
beta = reg2.coef_[0]
spread = v + beta * c

# (a) Check spread stationarity via ADF
adf_stat2, adf_p2, _, _, crit2, _ = adfuller(spread)
print("\n── Strategy 2a: ADF on spread ──")
print(f"  Beta           : {beta:.4f}")
print(f"  ADF statistic  : {adf_stat2:.4f}")
print(f"  p-value        : {adf_p2:.4f}")
print(f"  Stationary     : {'YES ✓' if adf_p2 < 0.05 else 'NO ✗'}")

# (b) Engle-Granger cointegration test
coint_stat, coint_p, coint_crit = coint(v, c)
print("\n── Strategy 2b: Engle-Granger cointegration test ──")
print(f"  Statistic      : {coint_stat:.4f}")
print(f"  p-value        : {coint_p:.4f}")
print(f"  Cointegrated   : {'YES ✓' if coint_p < 0.05 else 'NO ✗'}")

# ════════════════════════════════════════════════════════════════
# STRATEGY 3 — check predictive relationship c(t) -> v(t+1)
# ════════════════════════════════════════════════════════════════

c_curr = c[:-1].reshape(-1, 1)
v_next = v[1:]

reg3 = LinearRegression().fit(c_curr, v_next)
residuals3 = v_next - reg3.predict(c_curr)

print("\n── Strategy 3: c(t) → v(t+1) regression ──")
print(f"  Coefficient    : {reg3.coef_[0]:.4f}")
print(f"  R²             : {reg3.score(c_curr, v_next):.4f}")
# No mean-reversion assumption needed — just check R² is meaningful