'''import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from hurst import compute_Hc
import joblib
import os


# Hurst 
# H > 0.5 : trend momentum
# H < 0.5 : mean reversion
# More precisely:
# H < 0.4: Strong mean reversion. Below 0.2 is an extreme outlier that suggests a very rigid price container.
# 0.4 < H < 0.55: random walk (Efficient market. Hard to predict, essentially "Brownian Motion.")
# H > 0.6: Trending (The "Momentum" zone. If it went up, it’s likely to keep going up.)

# Autoregressive Beta AR1
# Beta measures autocorrelation: how much previous tick's move predicts current move
# Beta > 0: Momentum (Positive autocorrelation).
# Beta < 0: Mean Reversion (Negative autocorrelation/price flipping).
# Beta ≈ 0: Random Walk (at that specific lag).
# More precisely:
# Beta < -0.05: Negative autocorrelation. Price "flips" every tick. Good for instant scalping.
# -0.05 < Beta < 0.05: Noise. The very next tick is unpredictable noise.
# Beta > 0.05:  Positive autocorrelation. Short-term momentum. The next tick usually follows the current one


# Simple regression helper
def get_beta(y, X):
    # Align X and y and remove NaNs
    data = pd.concat([y, X], axis=1).dropna()
    model = LinearRegression().fit(data.iloc[:, 1:], data.iloc[:, 0])
    return model.coef_[0]

def hurst(prices):
    returns = np.log(prices).diff().dropna()
    # 1. Regression implementation
    X = returns.shift(1).to_frame() # X needs to be a 2D array/DF for sklearn
    y = returns
    AR1 = get_beta(y, X) # Autoregressive (AR1) Beta
    # 2. Hurst
    H, _, _ = compute_Hc(returns)
    return H, AR1

#If Beta is negative and Hurst is < 0.5: strong case for a Mean Reversion strategy (betting that the price will return to its average).
#If Beta is positive and Hurst is > 0.5: Trending market.

prices = pd.read_csv("../prices_round_5.csv",index_col=0)
#prices['product'] = prices['product'].str.strip()
products = sorted(set(prices['product'].unique()))

vanilla = prices[prices['product'] == "SNACKPACK_VANILLA"].copy()
chocolate = prices[prices['product'] == "SNACKPACK_CHOCOLATE"].copy()

# 1. Alignment: Ensure both series share the exact same timestamps
# This fixes the "doesn't work" issue caused by mismatched row indices
vanilla = vanilla.set_index('timestamp').sort_index()
chocolate = chocolate.set_index('timestamp').sort_index()

common_idx = vanilla.index.intersection(chocolate.index)
v_pr = vanilla.loc[common_idx, 'mid_price']
c_pr = chocolate.loc[common_idx, 'mid_price']

# 2. Extract Beta from Covariance Matrix
# Matrix format: [[Var(V), Cov(V,C)], [Cov(C,V), Var(C)]]
matrix = np.cov(v_pr, c_pr)
beta = matrix[0, 1] / matrix[1, 1]

# 3. Compute Spread and Statistics
# Strategy 1 Formula: Spread = Vanilla - (Beta * Chocolate)
spread = v_pr - (beta * c_pr)

H_exact, AR1_exact = hurst(spread)
H=round(H_exact,3)
AR1=round(AR1_exact,3)

print("Hurst", H)
print("AR1", AR1)

'''

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from hurst import compute_Hc

# Simple regression helper - completely safe from index-mismatching
def get_beta(y, X):
    # Strip pandas indices entirely to prevent alignment mismatch
    y_raw = y.to_numpy().flatten()
    X_raw = X.to_numpy().reshape(-1, 1)
    
    # Remove rows where either has a NaN
    mask = ~np.isnan(y_raw) & ~np.isnan(X_raw).flatten()
    
    model = LinearRegression().fit(X_raw[mask], y_raw[mask])
    return model.coef_[0]

def calculate_metrics(prices, is_spread=False):
    # FIXED: Use simple arithmetic returns if it's a spread to avoid np.log(negative) crash
    if is_spread:
        returns = prices.diff().dropna()
    else:
        returns = np.log(prices).diff().dropna()
        
    # AR(1) Beta Setup
    X = returns.shift(1)
    y = returns
    
    # Slice off the first NaN element caused by shifting
    AR1 = get_beta(y.iloc[1:], X.iloc[1:])
    
    # FIXED: The hurst library needs raw price scale arrays, not return tracking scales!
    H, _, _ = compute_Hc(prices.to_numpy())
    
    return H, AR1

# --- Data Loading ---
prices = pd.read_csv("../prices_round_5.csv", index_col=0)
products = sorted(set(prices['product'].unique()))

vanilla = prices[prices['product'] == "SNACKPACK_VANILLA"].copy()
chocolate = prices[prices['product'] == "SNACKPACK_CHOCOLATE"].copy()

# Alignment Engine
vanilla = vanilla.set_index('timestamp').sort_index()
chocolate = chocolate.set_index('timestamp').sort_index()

common_idx = vanilla.index.intersection(chocolate.index)
v_pr = vanilla.loc[common_idx, 'mid_price']
c_pr = chocolate.loc[common_idx, 'mid_price']

# Extract Hedge Ratio Beta
matrix = np.cov(v_pr, c_pr)
beta = matrix[0, 1] / matrix[1, 1]

# Compute Spread
spread = v_pr - (beta * c_pr)

# Process Spread (Pass is_spread=True)
H_exact, AR1_exact = calculate_metrics(spread, is_spread=True)
print("--- Basket Spread Analysis ---")
print("Spread Hurst:", round(H_exact, 3))
print("Spread AR1:", round(AR1_exact, 3))


