import os
import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from hurst import compute_Hc


# ============================================================
# HURST + AR(1) MARKET REGIME DETECTION
# ============================================================

# Hurst Interpretation
# --------------------
# H < 0.5  -> Mean Reversion
# H ≈ 0.5  -> Random Walk
# H > 0.5  -> Trending / Momentum

# Suggested practical zones:
# H < 0.45     : Mean Reverting
# 0.45 - 0.55 : Random / Efficient Market
# H > 0.55     : Trending


# AR(1) Interpretation
# --------------------
# Beta < 0     -> Negative autocorrelation (mean reversion)
# Beta ≈ 0     -> Noise / random walk
# Beta > 0     -> Momentum

# Suggested practical zones:
# Beta < -0.03      : Mean Reversion
# -0.03 < Beta < 0.03 : Noise
# Beta > 0.03       : Momentum


# ============================================================
# AR(1) REGRESSION
# ============================================================

def get_ar1_beta(returns):
    """
    Computes AR(1) beta:
        r_t = beta * r_(t-1)

    Parameters
    ----------
    returns : pd.Series

    Returns
    -------
    float
        AR(1) coefficient
    """

    X = returns.shift(1).to_frame(name="lagged_returns")
    y = returns

    data = pd.concat([y, X], axis=1).dropna()

    if len(data) < 10:
        return np.nan

    model = LinearRegression(fit_intercept=False)

    model.fit(
        data[["lagged_returns"]],
        data.iloc[:, 0]
    )

    return model.coef_[0]


# ============================================================
# HURST + AR1
# ============================================================

def compute_hurst_and_ar1(prices):
    """
    Computes:
    1. Hurst exponent on log prices
    2. AR(1) beta on log returns

    Parameters
    ----------
    prices : pd.Series

    Returns
    -------
    tuple
        (Hurst exponent, AR1 beta)
    """

    # Remove invalid prices
    prices = prices.dropna()

    # Hurst should be computed on log prices
    log_prices = np.log(prices)

    # Returns for AR(1)
    returns = log_prices.diff().dropna()

    # Safety check
    if len(log_prices) < 100:
        return np.nan, np.nan

    # ----------------------------
    # AR(1)
    # ----------------------------
    ar1_beta = get_ar1_beta(returns)

    # ----------------------------
    # Hurst
    # ----------------------------
    try:
        H, _, _ = compute_Hc(
            log_prices,
            kind='price',
            simplified=True
        )
    except Exception as e:
        print(f"Hurst computation failed: {e}")
        H = np.nan

    return H, ar1_beta


# ============================================================
# MARKET CLASSIFICATION
# ============================================================

def classify_market(H, ar1):

    if np.isnan(H) or np.isnan(ar1):
        return "Insufficient Data"

    # Strong short-term mean reversion
    if ar1 < -0.10:
        return "Strong Mean Reversion"

    # Moderate mean reversion
    elif ar1 < -0.03:
        return "Weak Mean Reversion"

    # Momentum
    elif ar1 > 0.03:
        return "Momentum"

    # Long-memory trend
    elif H > 0.55:
        return "Long Memory Trend"

    # Long-memory mean reversion
    elif H < 0.45:
        return "Long Memory Mean Reversion"

    else:
        return "Random Walk / Efficient"
    
# ============================================================
# LOAD DATA
# ============================================================

prices = pd.read_csv(
    "../prices_round_5.csv",
    index_col=0
)

# Optional cleanup
prices["product"] = prices["product"].astype(str).str.strip()

products = sorted(prices["product"].unique())


# ============================================================
# LOAD PREVIOUS RESULTS IF AVAILABLE
# ============================================================

CACHE_FILE = "hurst_attributes.pkl"

if os.path.exists(CACHE_FILE):

    print("Loading cached results...")

    hurst_attributes = joblib.load(CACHE_FILE)

else:

    print("Computing Hurst + AR(1)...")

    hurst_attributes = {}

    for product in products:

        # ----------------------------------------
        # Extract product prices
        # ----------------------------------------

        product_prices = prices.loc[
            prices["product"] == product,
            "mid_price"
        ]

        # Remove invalid values
        product_prices = product_prices[
            product_prices > 0
        ]

        # ----------------------------------------
        # Compute metrics
        # ----------------------------------------

        H, ar1 = compute_hurst_and_ar1(product_prices)

        # Round values
        H_rounded = round(H, 3) if not np.isnan(H) else np.nan
        ar1_rounded = round(ar1, 3) if not np.isnan(ar1) else np.nan

        # ----------------------------------------
        # Market classification
        # ----------------------------------------

        market_type = classify_market(H, ar1)

        # ----------------------------------------
        # Store results
        # ----------------------------------------

        hurst_attributes[product] = {
            "H": H_rounded,
            "AR1": ar1_rounded,
            "market": market_type
        }

        # ----------------------------------------
        # Print summary
        # ----------------------------------------

        print(
            f"{product}: "
            f"Hurst = {H_rounded}, "
            f"AR1 = {ar1_rounded}"
        )

        print(f" -> {market_type}\n")

    # Save results
    joblib.dump(hurst_attributes, CACHE_FILE)

    print(f"Results saved to {CACHE_FILE}")


# ============================================================
# FILTER PRODUCTS BY MARKET TYPE
# ============================================================

strong_MR_list = [
    product
    for product in products
    if hurst_attributes[product]["market"]
    == "Strong Mean Reversion"
]

weak_MR_list = [
    product
    for product in products
    if hurst_attributes[product]["market"]
    == "Weak Mean Reversion"
]

momentum_list = [
    product
    for product in products
    if hurst_attributes[product]["market"]
    == "Momentum"
]

long_memory_trend_list = [
    product
    for product in products
    if hurst_attributes[product]["market"]
    == "Long Memory Trend"
]

long_memory_MR_list = [
    product
    for product in products
    if hurst_attributes[product]["market"]
    == "Long Memory Mean Reversion"
]

efficient_market_list = [
    product
    for product in products
    if hurst_attributes[product]["market"]
    == "Random Walk / Efficient"
]


# ============================================================
# PRINT RESULTS
# ============================================================

print("=" * 60)

print("\nStrong Mean Reversion:")
print(strong_MR_list)

print("\nWeak Mean Reversion:")
print(weak_MR_list)

print("\nMomentum:")
print(momentum_list)

print("\nLong Memory Trend:")
print(long_memory_trend_list)

print("\nLong Memory Mean Reversion:")
print(long_memory_MR_list)

print("\nRandom Walk / Efficient:")
print(efficient_market_list)

print('Strong Mean reversion:')
for product in strong_MR_list:
    print(f"{product}, Hurst: {hurst_attributes[product]['H']}, AR1: {hurst_attributes[product]['AR1']}")

print('Weak Mean Reversion:')
for product in weak_MR_list:
    print(f"{product}, Hurst: {hurst_attributes[product]['H']}, AR1: {hurst_attributes[product]['AR1']}")


