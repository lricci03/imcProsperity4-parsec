# Round 5 of Prosperity Challenge 4 - Team Parsec (#44 worldwide, #1 Switzerland)

Round 5 entails 50 assets, with a limit of 10 each. The assets are grouped by categories, and a hint on the website suggests that some products may share common patterns.

We begin with a statistical analysis of all assets using:
- Hurst exponents,
- AR(1) coefficients,
- pairwise correlations.


# Statistical Indicators

We use the Hurst exponent to characterize long-horizon persistence or mean reversion, while AR(1) coefficients on returns are used to detect short-term reversal exploitable at the tick level.

## Hurst Exponent $H$

- $H < 0.5$: Mean Reversion
- $H \approx 0.5$: Random Walk
- $H > 0.5$: Trending / Momentum

In practice we use:
- $H < 0.45$: Mean Reverting
- $0.45 < H < 0.55$: Random / Efficient Market
- $H > 0.55$: Trending

## AR(1) of Returns

- $\beta < 0$: Negative autocorrelation (short-term mean reversion)
- $\beta \approx 0$: Noise / random walk
- $\beta > 0$: Momentum

In practice we use:
- $\beta < -0.03$: Short-term mean reversion
- $-0.03 < \beta < 0.03$: Noise
- $\beta > 0.03$: Momentum


# Correlated Assets and Relative-Value Strategies

We identified strong relationships within:
- Snackpacks
- Pebbles

## SNACKPACKS

There are two negatively correlated snackpack pairs:
- VANILLA + CHOCOLATE
- RASPBERRY + STRAWBERRY

We compute the Hurst exponents and AR(1) coefficients of each basket/spread (see `analysis-snackpacks-raw-prices.py`):

$
\text{spread} = \text{product}_1 - \beta \cdot \text{product}_2
$

where $\beta$ is the hedge ratio / OLS regression slope.

- SNACKPACK_CHOCOLATE vs SNACKPACK_VANILLA  
  Hurst: 0.45, AR1: -0.342, beta = -1.041

- SNACKPACK_RASPBERRY vs SNACKPACK_STRAWBERRY  
  Hurst: 0.453, AR1: -0.028, beta = -0.193

Both spreads exhibit mean reverting behavior, while the chocolate-vanilla pair shows particularly strong short-term spread reversal.

## Strategy: SNACKPACK_VANILLA and SNACKPACK_CHOCOLATE

SNACKPACK_VANILLA and SNACKPACK_CHOCOLATE are negatively correlated, and their spread shows noticeable tick-by-tick mean reversion.

Instead of betting on long-horizon spread convergence, backtesting indicated that exploiting one-tick spread reversals produced higher PnL.

Therefore we introduce a threshold: if the spread deviates more than the threshold from the previous timestamp, we place a limit order according to the deviation direction.


## Strategy: SNACKPACK_RASPBERRY and SNACKPACK_STRAWBERRY

During the challenge we found an AR1 of approximately -0.27, therefore we applied a similar strategy as for the vanilla-chocolate pair.

However, due to the weaker magnitude of deviations, we reacted directly to spread direction changes rather than introducing a fixed threshold. We placed limit orders as soon as the spread showed temporary dislocation.

## Strategy: PEBBLES

The sum of pebble prices is approximately stationary around 50'000.

We observed that short-term moves in PEBBLES_XL often preceded compensating moves in the remaining pebble products. Based on this empirical observation, we used PEBBLES_XL as a leading signal for a relative-value mean reversion strategy.

We compute tick-by-tick changes in the XL mid price and interpret large deviations ($|\Delta| > 20$) as temporary dislocations rather than sustainable trends.

When a significant upward move occurs:
- we short PEBBLES_XL,
- and go long the correlated pebble assets.

Analogously in the opposite direction.

The strategy also propagates the previous signal into the following tick.

Execution is mostly passive, with orders submitted close to the best bid or ask to improve fill quality and potentially capture spread edge.

# Single-Asset Mean Reversion Strategies

## ROBOTS and OXYGEN SHAKES

We focus on the following assets:

### Strong Short-Term Mean Reversion ($\text{AR1} < -0.10$)

- OXYGEN_SHAKE_EVENING_BREATH 
  Hurst: 0.507, AR1: -0.118

- ROBOT_DISHES  
  Hurst: 0.485, AR1: -0.222

- ROBOT_IRONING
  Hurst: 0.535, AR1: -0.121

### Moderate Short-Term Mean Reversion

- OXYGEN_SHAKE_CHOCOLATE  
  Hurst: 0.493, AR1: -0.082

- SNACKPACK_CHOCOLATE 
  Hurst: 0.465, AR1: -0.031

## Additional Observations

With more time we would also have explored:

### Long-Memory Trend ($H > 0.55$)

- MICROCHIP_OVAL
- MICROCHIP_SQUARE
- OXYGEN_SHAKE_GARLIC
- PANEL_1X4
- UV_VISOR_AMBER

### Long-Term Mean Reversion ($H < 0.45$)

- SNACKPACK_RASPBERRY


# Strategy for ROBOTS and OXYGEN SHAKES

We trade:
- ROBOT_DISHES
- ROBOT_IRONING
- OXYGEN_SHAKE_EVENING_BREATH
- OXYGEN_SHAKE_CHOCOLATE

The returns of these assets exhibited episodic volatility bursts, being several times larger on certain days than under normal conditions.

This motivated a two-regime strategy:
1. aggressive reaction to exceptional moves,
2. passive short-term mean reversion during normal conditions.

During the competition we initially misestimated the Hurst exponents, which led us to incorporate not only short-horizon mean reversion, but also long-horizon mean reversion components.

This resulted in a combined strategy:
- enter positions when price deviates from a rolling average (z-score),
- exit as price reverts,
- while still preserving inventory capacity for short-term reversal opportunities.

## Trading Logic

### Step 0: Exceptional Returns

If the return is exceptionally large ($|\text{return}| > 50$), we trade aggressively with market orders.

### Step 1: Z-score Entry / Exit

If Step 0 is not triggered:
- enter or exit positions according to the z-score,
- use market orders for exits (best ask / best bid),
- keep inventory space for Step 2.

Therefore we never buy or sell more than 4 units during this phase.

### Step 2: Short-Term Mean Reversion

With the remaining inventory capacity, we exploit short-term reversal effects ($\beta < -0.05$).

If the price increased from the previous tick:
- we sell near the best ask.

If the price decreased:
- we buy near the best bid.

More precisely, orders are placed at:
- best ask - 1,
- best bid + 1.