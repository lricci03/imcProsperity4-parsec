# ============================================================
# PAIRS / BASKET ANALYSIS USING RAW PRICES
# ============================================================

#   We use:
#
#     spread = A - beta * B



import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from hurst import compute_Hc


# ============================================================
# BUILD RAW SPREAD
# ============================================================

def build_raw_spread(series_A, series_B):
    """
    Builds hedge-ratio-adjusted spread:

        spread = A - beta * B

    Beta estimated using linear regression.
    """

    # ----------------------------------------
    # Align series
    # ----------------------------------------

    df = pd.concat(
        [series_A, series_B],
        axis=1
    ).dropna()

    df.columns = ["A", "B"]

    # ----------------------------------------
    # Hedge ratio
    # A = beta * B
    # ----------------------------------------

    model = LinearRegression()

    model.fit(
        df[["B"]],
        df["A"]
    )

    beta = model.coef_[0]

    # ----------------------------------------
    # Spread
    # ----------------------------------------

    spread = df["A"] - beta * df["B"]

    return spread, beta


# ============================================================
# AR(1)
# ============================================================

def get_ar1_beta(series):

    returns = series.diff().dropna()

    X = returns.shift(1).to_frame(name="lagged")
    y = returns

    data = pd.concat([y, X], axis=1).dropna()

    if len(data) < 10:
        return np.nan

    model = LinearRegression(
        fit_intercept=False
    )

    model.fit(
        data[["lagged"]],
        data.iloc[:, 0]
    )

    return model.coef_[0]


# ============================================================
# SPREAD ANALYSIS
# ============================================================

def analyze_raw_spread(series_A, series_B):

    spread, hedge_ratio = build_raw_spread(
        series_A,
        series_B
    )

    # ----------------------------------------
    # Hurst
    # ----------------------------------------

    try:

        H, _, _ = compute_Hc(
            spread,
            kind='price',
            simplified=True
        )

    except Exception as e:

        print(f"Hurst failed: {e}")
        H = np.nan

    # ----------------------------------------
    # AR(1)
    # ----------------------------------------

    ar1 = get_ar1_beta(spread)
    
    return {
        "Hurst": round(H, 3),
        "AR1": round(ar1, 3),
        "Hedge_Ratio": round(hedge_ratio, 3)
    }



# ============================================================
# LOAD PRODUCTS
# ============================================================

prices = pd.read_csv("../prices_round_5.csv", index_col=0)

snackpack_chocolate = prices.loc[
    prices["product"] == "SNACKPACK_CHOCOLATE",
    "mid_price"
].reset_index(drop=True)

snackpack_vanilla = prices.loc[
    prices["product"] == "SNACKPACK_VANILLA",
    "mid_price"
].reset_index(drop=True)

snackpack_raspberry = prices.loc[
    prices["product"] == "SNACKPACK_RASPBERRY",
    "mid_price"
].reset_index(drop=True)

snackpack_strawberry = prices.loc[
    prices["product"] == "SNACKPACK_STRAWBERRY",
    "mid_price"
].reset_index(drop=True)


# ============================================================
# ANALYZE PAIRS
# ============================================================

pair_1 = analyze_raw_spread(
    snackpack_chocolate,
    snackpack_vanilla
)

pair_2 = analyze_raw_spread(
    snackpack_raspberry,
    snackpack_strawberry
)


# ============================================================
# PRINT RESULTS
# ============================================================

print("=" * 60)

print("\nSNACKPACK_CHOCOLATE vs SNACKPACK_VANILLA")
print(pair_1)

print("\nSNACKPACK_RASPBERRY vs SNACKPACK_STRAWBERRY")
print(pair_2)