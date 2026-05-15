import numpy as np
#from scipy.stats import norm
#from scipy.optimize import brentq
import pandas as pd
#from sklearn.linear_model import LinearRegression
#from sklearn.preprocessing import PolynomialFeatures
import matplotlib.pyplot as plt


from tqdm import tqdm

def backtest_trader(trader, product, trades, prices):

    trader_df = trades[(trades['buyer'] == trader) | (trades['seller'] == trader)] # filter on trader
    trader_df = trader_df[trader_df['symbol'] == product] # filter on product
    product_prices = prices[prices['product'] == product] # filter on product

    position = 0
    buy_costs = 0
    sell_costs = 0
    pnls = []
    positions = []
    timestamps = []
    prev_pnl = 0

    for i, row in tqdm(product_prices.iterrows(), total=len(product_prices)):
        time = row['timestamp']
        mid_price = row['mid_price']
        product = row['product']

        trades = trader_df[trader_df['timestamp'] == time]

        if time % 1e6 == 0.0:
            if position > 0:
                prev_pnl = (mid_price * position) - buy_costs + sell_costs + prev_pnl
            elif position < 0:
                prev_pnl = sell_costs - buy_costs - (mid_price * abs(position)) + prev_pnl
            else:
                prev_pnl = sell_costs - buy_costs

            position = 0
            buy_costs = 0
            sell_costs = 0

        for j, trade in trades.iterrows():
            symbol = trade['symbol']
            if symbol != product:
                continue

            if trade['buyer'] == trader:
                position += trade['quantity']
                buy_costs += trade['price'] * trade['quantity']
            
            elif trade['seller'] == trader:                    
                position -= trade['quantity']
                sell_costs += trade['price'] * trade['quantity']
        
        if position > 0:
            pnl = (mid_price * position) - buy_costs + sell_costs + prev_pnl
    
        elif position < 0:
            pnl = sell_costs - buy_costs - (mid_price * abs(position)) + prev_pnl

        else:
            pnl = sell_costs - buy_costs + prev_pnl

        pnls.append(pnl)
        timestamps.append(time)
        positions.append(position)
    
    return pnls[-1], timestamps[-1], positions[-1]

def simple_mid_price(row):
    bid = row[3]
    ask = row[9]
    if np.isnan(bid):
        bid = 0
    elif np.isnan(ask):
        ask = 0
    return (bid+ask) / 2

def plot_corr(corr_matrix, title):
    # Show matrix as image
    plt.imshow(corr_matrix, vmin=-1, vmax=1)
    plt.colorbar()
    # Axis labels (product names)
    plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns, rotation=90)
    plt.yticks(range(len(corr_matrix.columns)), corr_matrix.columns)

    plt.title(title)
    plt.tight_layout()
    plt.savefig(title)
    plt.show()


prices_1 = pd.read_csv("prices_round_5_day_2.csv", delimiter=';')
prices_2 = pd.read_csv("prices_round_5_day_3.csv", delimiter=';')
prices_2['timestamp'] += 1e6 # s6hift day 2 to 0-24h
prices_3 = pd.read_csv("prices_round_5_day_4.csv", delimiter=';')
prices_3['timestamp'] += 2e6 # shift day 2 to 0-24h

trades_1 = pd.read_csv("trades_round_5_day_2.csv", delimiter=';')
trades_2 = pd.read_csv("trades_round_5_day_3.csv", delimiter=';')
trades_2['timestamp'] += 1e6
trades_3 = pd.read_csv("trades_round_5_day_4.csv", delimiter=';')
trades_3['timestamp'] += 2e6

prices = pd.concat([prices_1, prices_2, prices_3])
trades= pd.concat([trades_1, trades_2, trades_3])

products = sorted(set(trades['symbol'].unique()))

print(prices_1.head())


GalaxySoundsRecorders =["GALAXY_SOUNDS_DARK_MATTER", 
                        "GALAXY_SOUNDS_BLACK_HOLES", 
                        "GALAXY_SOUNDS_PLANETARY_RINGS", 
                        "GALAXY_SOUNDS_SOLAR_WINDS", 
                        "GALAXY_SOUNDS_SOLAR_FLAMES"]
VerticalSleepingPods = ["SLEEP_POD_SUEDE", 
                        "SLEEP_POD_LAMB_WOOL", 
                        "SLEEP_POD_POLYESTER", 
                        "SLEEP_POD_NYLON", 
                        "SLEEP_POD_COTTON"]
OrganicMicrochips = ["MICROCHIP_CIRCLE", 
                     "MICROCHIP_OVAL", 
                     "MICROCHIP_SQUARE", 
                     "MICROCHIP_RECTANGLE", 
                     "MICROCHIP_TRIANGLE"]
PurificationPebbles = ["PEBBLES_XS",
                        "PEBBLES_S",
                        "PEBBLES_M", 
                        "PEBBLES_L", 
                        "PEBBLES_XL"]
DomesticRobots= ["ROBOT_VACUUMING", 
                 "ROBOT_MOPPING", 
                 "ROBOT_DISHES", 
                 "ROBOT_LAUNDRY", 
                 "ROBOT_IRONING"]
UVVisors=["UV_VISOR_YELLOW",
            "UV_VISOR_AMBER", 
            "UV_VISOR_ORANGE", 
            "UV_VISOR_RED", 
            "UV_VISOR_MAGENTA"]
InstantTranslators=["TRANSLATOR_SPACE_GRAY", 
                    "TRANSLATOR_ASTRO_BLACK", 
                    "TRANSLATOR_ECLIPSE_CHARCOAL", 
                    "TRANSLATOR_GRAPHITE_MIST", 
                    "TRANSLATOR_VOID_BLUE"]
ConstructionPanels= ["PANEL_1X2",
                     "PANEL_2X2",
                     "PANEL_1X4",
                     "PANEL_2X4", 
                     "PANEL_4X4"]
LiquidBreathOxygenShakes= ["OXYGEN_SHAKE_MORNING_BREATH",
                            "OXYGEN_SHAKE_EVENING_BREATH",
                            "OXYGEN_SHAKE_MINT",
                            "OXYGEN_SHAKE_CHOCOLATE",
                            "OXYGEN_SHAKE_GARLIC"]
ProteinSnackPacks=["SNACKPACK_CHOCOLATE", 
                   "SNACKPACK_VANILLA",
                   "SNACKPACK_PISTACHIO", 
                   "SNACKPACK_STRAWBERRY",
                   "SNACKPACK_RASPBERRY"]


# == CORRELATION ==
# Need to create a dataframe whose columns are products and rows are timestamps 


#product_df = {prices[prices['product'] == product] for product in products}

'''product = "SNACKPACK_RASPBERRY"
raspberry_df=prices[prices['product'] == product] # filter by product
raspberry_df = raspberry_df[['timestamp','mid_price']]
raspberry_df=raspberry_df.rename(columns={"mid_price": product})

prices_df = raspberry_df
for product in ProteinSnackPacks:    
    new_df= prices[prices['product'] == product] # filter by product
    new_df = new_df[['mid_price']]
    new_df=new_df.rename(columns={"mid_price": product})
    prices_df = pd.concat(prices_df,new_df)
print(prices_df.head())'''
#product_df= prices[prices['product'] == product] # filter by product
#prices_df = product_df[['mid_price','timestamp']]
#prices_df.rename(columns={"mid_price": product})
#print(prices_df.head())
#prices_df = pd.concat(prices_df[product_df[product]], axis=1)
#print(product_df.head())

'''
# chose any product to inizialize the dataframe as one column with timestamps
product = "SNACKPACK_RASPBERRY"
snackpacks_prices_df=prices[prices['product'] == product][['timestamp']]
for product in ProteinSnackPacks:
    # extract the two columns 'timestamp' and 'mid_price'
    new_df= prices[prices['product'] == product][['timestamp','mid_price']]
    new_df=new_df.rename(columns={"mid_price": product})
    # merging two data frames matching on the column 'timestamp'
    snackpacks_prices_df=snackpacks_prices_df.merge(new_df, how='left', on='timestamp')
# Dropping the column 'timestamp'
snackpacks_prices_df= snackpacks_prices_df.drop('timestamp',axis=1)

# CORRELATION MATRIX FOR SNACKPACKS 
corr_matrix_snackpacks = snackpacks_prices_df.corr()
print(corr_matrix_snackpacks)
plt.figure(figsize=(12, 10))

plot_corr(corr_matrix_snackpacks,"corr_snackpacks")

# DATA FRAME OF PEBBLES PRICES
product = "SNACKPACK_RASPBERRY"
pebbles_prices_df=prices[prices['product'] == product][['timestamp']]
for product in PurificationPebbles:
    # extract the two columns 'timestamp' and 'mid_price'
    new_df= prices[prices['product'] == product][['timestamp','mid_price']]
    new_df=new_df.rename(columns={"mid_price": product})
    # merging two data frames matching on the column 'timestamp'
    pebbles_prices_df=pebbles_prices_df.merge(new_df, how='left', on='timestamp')
# Dropping the column 'timestamp'
pebbles_prices_df= pebbles_prices_df.drop('timestamp',axis=1)

# CORRELATION MATRIX FOR PEBBLES

corr_matrix_pebbles = pebbles_prices_df.corr()
print(corr_matrix_pebbles)
plt.figure(figsize=(12, 10))

plot_corr(corr_matrix_pebbles,"corr_pebbles")'''



#### PLOTTING MOVING AVERAGES AND PRICES 

returns = prices.diff()

# ============================================================
# CROSS-SECTIONAL Z-SCORE
# At each timestamp T, we have 5 returns (one per pebble).
# We compute the mean and std of those 5 numbers.
# Then z_i(T) = (return_i(T) - mean) / std
#
# A pebble with |z| > 2 is moving very differently from its siblings.
# That is the outlier. That is what we want to fade.
#
# Y-axis: standard deviations from the group mean (dimensionless)
# ============================================================
cross_mean = returns.mean(axis=1)   # mean return across 5 pebbles at each tick
cross_std  = returns.std(axis=1)    # std of returns across 5 pebbles at each tick

# z_score has same shape as returns: one z per pebble per tick
z_scores = returns.subtract(cross_mean, axis=0).divide(cross_std, axis=0)

# ============================================================
# PLOT: z-scores over 500 ticks
# When a line spikes past ±2, that pebble is the outlier.
# Check if it comes back toward 0 in the next 1-2 ticks.
# ============================================================
'''fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

# Top: raw returns so you can see the actual price movements
colors = ["blue","orange","green","red","purple"]
short  = ["L","M","S","XL","XS"]
for col, name, color in zip(pebbles, short, colors):
    ax1.plot(returns[col].iloc[:500].values,
             linewidth=0.7, label=name, color=color, alpha=0.8)
ax1.axhline(0, color="black", linewidth=0.5)
ax1.set_title("Per-pebble tick return (price points — how much each moved)")
ax1.set_ylabel("Change in mid_price (price points)")
ax1.legend(fontsize=8)

# Bottom: cross-sectional z-score — the outlier detector
for col, name, color in zip(pebbles, short, colors):
    ax2.plot(z_scores[col].iloc[:500].values,
             linewidth=0.7, label=name, color=color, alpha=0.8)
ax2.axhline(+2, color="red",   linestyle="--", linewidth=0.8, label="+2 threshold")
ax2.axhline(-2, color="green", linestyle="--", linewidth=0.8, label="-2 threshold")
ax2.axhline(0,  color="black", linewidth=0.5)
ax2.set_title("Cross-sectional z-score — which pebble is the outlier?")
ax2.set_ylabel("Std deviations from group mean (dimensionless)")
ax2.legend(fontsize=8)

plt.tight_layout()
plt.show()'''

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

for product in ['ROBOT_DISHES']:
    ax1.plot(returns[product].iloc[:500].values,
             linewidth=0.7, label=product, alpha=0.8)
ax1.axhline(0, color="black", linewidth=0.5)
ax1.set_title("Tick return (price points — how much each moved)")
ax1.set_ylabel("Change in mid_price (price points)")
ax1.legend(fontsize=8)


for product in ['ROBOT_DISHES']:
    ax2.plot(z_scores[product].iloc[:500].values,
             linewidth=0.7, label=product, alpha=0.8)
ax2.axhline(+2, color="red",   linestyle="--", linewidth=0.8, label="+2 threshold")
ax2.axhline(-2, color="green", linestyle="--", linewidth=0.8, label="-2 threshold")
ax2.axhline(0,  color="black", linewidth=0.5)
ax2.set_title("Cross-sectional z-score — which pebble is the outlier?")
ax2.set_ylabel("Std deviations from group mean (dimensionless)")
ax2.legend(fontsize=8)

plt.tight_layout()
plt.show()