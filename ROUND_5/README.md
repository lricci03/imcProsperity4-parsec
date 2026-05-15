# Round 5 of Prosperity Challenge 4 - Team Parsec #44 worldwide, #1 Switzerland

Round 5 shows entails 50 assets, with a limit of 10 each. The assests are grouped by categories, and a hint on the website suggests that we might cluster the items into categories that share patterns.

We decide to do a quick analysis of all assets with Hurst Exponent and AR(1) coefficient to understand their market behavior, and to run correlation tests to then work with categories.

## Correlation
We find correlations between
- Pebbles
- Snackpacks

### SNACKPACKS

There are two pairs of snackpacks that are (negatively) correlated: vanilla + chocolate, raspberry + strawberry.

We compute the Hurst exponents and AR(1) coefficient of each basket/spread (see *analysis-snackpacks-raw-prices.py*):

spread = product_1 - beta * product_2

where beta is the hedge ratio/ OLS regression slope. 

- SNACKPACK_CHOCOLATE vs SNACKPACK_VANILLA: Hurst: 0.45, AR1: -0.342, beta = -1.041
- SNACKPACK_RASPBERRY vs SNACKPACK_STRAWBERRY: Hurst: 0.453, AR1: -0.028, beta = -0.193.

They both show mean reversing tendence and the chocolate-vanilla pair shows in particular a strong short term spread reversal momentum. 

### SNACKPACK_VANILLA and SNACKPACK_CHOCOLATE

SNACKPACK_VANILLA and SNACKPACK_CHOCOLATE are negatively correlated, and their spread/basket has a strong tick-by-tick mean reversion.

Instead of betting on the spread to revert back to its mean, backtesting shows a higher PnL trading on the tick-by-tick reversal of the spread.\
Therefore we set a threshold and if, from the previous timestamp, the spread deviates more than this threshold, we place a limit order according to the deviation direction.

### SNACKPACK_RASPBERRY and SNACKPACK_STRAWBERRY

During the challenge we found an AR1 of -0.27 therefore we applied a
similar strategy as for the pair vanilla-chocolate.\
Instead of setting a threshold, we place limit orders as soon as the spread deviates from the previous timestamp. 

### PEBBLES
These assets were traded by Tommy.

## Market behaviour for all assets


### ROBOTS and OXYGEN SHAKES

We compute the Hurst Exponent and AR(1) coefficient of each asset.

**Hurst Exponent H:**
- H < 0.5  means Mean Reversion
- H ≈ 0.5  means Random Walk
- H > 0.5  means Trending / Momentum

In practice we look at: 
- H < 0.45     : Mean Reverting
- 0.45 - 0.55 : Random / Efficient Market
- H > 0.55     : Trending

**AR(1) of returns:**
- Beta < 0     -> Negative autocorrelation (short term mean reversion)
- Beta ≈ 0     -> Noise / random walk
- Beta > 0     -> Momentum

In practice we look at: 
- Beta < -0.03      : Short term Mean Reversion
- -0.03 < Beta < 0.03 : Noise
- Beta > 0.03       : Momentum

We focus on the following results:\
Strong Short-Term Mean reversion (ar1 < -0.10):
- OXYGEN_SHAKE_EVENING_BREATH, Hurst: 0.507, AR1: -0.118
- ROBOT_DISHES, Hurst: 0.485, AR1: -0.222
- ROBOT_IRONING, Hurst: 0.535, AR1: -0.121

Moderate Short-Term Mean Reversion (-0.10 <ar1 < -0.03):
- OXYGEN_SHAKE_CHOCOLATE, Hurst: 0.493, AR1: -0.082
- SNACKPACK_CHOCOLATE, Hurst: 0.465, AR1: -0.031

**Remark:** With more time we would have also focused on

Long Memory Trend (H > 0.55):\
'MICROCHIP_OVAL', 'MICROCHIP_SQUARE', 'OXYGEN_SHAKE_GARLIC', 'PANEL_1X4', 'UV_VISOR_AMBER'

(Long term) Mean Reversion (H < 0.45): 'SNACKPACK_RASPBERRY'.

**Remark 2:** Plotting the *Returns* (change in mid price from previous timestamp) we notice that they are extraordinarily high on given days. E.g. ROBOT_DISHES on day 4 have returns of 100, while they don't exceed 40 on days 2 and 3. Analogously ROBOT_IRONING have returns of 100 on day 1, while they don't exceed 25 on the other days.\
Therefore we decide to first trade aggressively on these returns (Step 0 below), and to follow a mean reversing strategy if returns are not exceptional (Step 1,2 below).\
Analogous statements hold for OXYGEN_SHAKE_CHOCOLATE and OXYGEN_SHAKE_EVENING_BREATH.

### Strategy for (selected) ROBOTS and OXYGEN SHAKES

We trade: ROBOT_DISHES, ROBOT_IRONING, OXYGEN_SHAKE_EVENING_BREATH and OXYGEN_SHAKE_CHOCOLATE.

Short-term mean reversion means that if from the previous timestamp the price went down, at the next timestamp it is likely to go up.\
We trade on this logic, and choose to take advantage of **Remark 2** above.\
During the competition, we made a mistake in the computaion of Hurst Exponents, and the selected assets showed some long-termn mean reversion. Therefore we decided to trade on (long term) mean reversion as well: entering the market when the price deviated from the rolling average (z-score), and exiting when it came back to it.\
With enter/exit we kept space for short-term mean reversion. 

- **Step 0**: If the return (change in mid price from previous timestamp) is exceptionally high (|return|>50) trade aggressively with market orders.

If not Step 0:
- **Step 1**: Entry or Exit depending on the Z-score.\
For exit we place market orders (buy/sell orders at best ask/best bid).\
Since we want to keep some inventory for step 2 we don't buy/sell more than 4. 
- **Step 2**: With the remaining positions staying inside the limits, take advantage of positive-negative returns (beta< -0.05).\
If the price went up/down from last tick, we sell/buy at best ask-1/best bid + 1.
