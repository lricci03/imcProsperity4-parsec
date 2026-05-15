import pandas as pd
import matplotlib.pyplot as plt


GalaxySoundsRecorders =[ "GALAXY_SOUNDS_DARK_MATTER", 
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

day=2
#day=3
#day=4

# Read the CSV — note sep=";" because it uses semicolons not commas
prices = pd.read_csv(f"../ROUND_5/prices_round_5_day_{day}.csv", sep=";")
trades = pd.read_csv(f"../ROUND_5/trades_round_5_day_{day}.csv", sep=";")

strawberry = prices[prices['product'] == "SNACKPACK_STRAWBERRY"].copy()
strawberry_trades = trades[trades['symbol'] == "SNACKPACK_STRAWBERRY"].copy()


raspberry = prices[prices['product'] == "SNACKPACK_RASPBERRY"].copy()
raspberry_trades = trades[trades['symbol'] == "SNACKPACK_RASPBERRY"].copy()

vanilla = prices[prices['product'] == "SNACKPACK_VANILLA"].copy()
vanilla_trades = trades[trades['symbol'] == "SNACKPACK_VANILLA"].copy()

pistachio = prices[prices['product'] == "SNACKPACK_PISTACHIO"].copy()
pistachio_trades = trades[trades['symbol'] == "SNACKPACK_PISTACHIO"].copy()

chocolate = prices[prices['product'] == "SNACKPACK_CHOCOLATE"].copy()
chocolate_trades = trades[trades['symbol'] == "SNACKPACK_CHOCOLATE"].copy()

plt.plot(strawberry["timestamp"], strawberry["mid_price"], label="strawberry mid_price", linewidth=0.5, alpha=0.8)
plt.plot(raspberry["timestamp"], raspberry["mid_price"], label="raspberry mid_price", linewidth=0.5, alpha=0.8)
plt.plot(vanilla["timestamp"], vanilla["mid_price"], label="vanilla mid_price", linewidth=0.5, alpha=0.8)
plt.plot(pistachio["timestamp"], pistachio["mid_price"], label="pistachio mid_price", linewidth=0.5, alpha=0.8)
plt.plot(chocolate["timestamp"], chocolate["mid_price"], label="chocolate mid_price", linewidth=0.5, alpha=0.8)


plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.legend()
plt.xlabel("Timestamp")
plt.ylabel("Price")
plt.title(f"Protein Snackpacks")
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(strawberry['timestamp'], strawberry['mid_price'], label='Strawberry', linewidth=0.5)
plt.plot(strawberry['timestamp'], strawberry['bid_price_1'], label='Strawberry best bid', linewidth=0.5)
plt.plot(strawberry['timestamp'], strawberry['ask_price_1'], label='Strawberry best ask', linewidth=0.5)
plt.plot(pistachio['timestamp'], pistachio['mid_price'], label='Pistachio', linewidth=0.5)
plt.plot(pistachio['timestamp'], pistachio['bid_price_1'], label='Pistachio best bid', linewidth=0.5)
plt.plot(pistachio['timestamp'], pistachio['ask_price_1'], label='Pistachio best ask', linewidth=0.5)

plt.title('Strawberry vs Pistachio')
plt.xlabel('Timestamp')
plt.ylabel('Price')
plt.legend()
plt.show()

# Merge on timestamp to ensure you subtract the right rows
diff_df = pd.merge(
    strawberry[['timestamp', 'mid_price']], 
    pistachio[['timestamp', 'mid_price']], 
    on='timestamp', 
    suffixes=('_s', '_p')
)

plt.figure(figsize=(10, 5))
plt.plot(diff_df['timestamp'], diff_df['mid_price_s'] - diff_df['mid_price_p'], color='red', label='Strawberry - Pistachio')

plt.axhline(0, color='black', linestyle='--', alpha=0.5) # Zero line for reference
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.title('Price Spread: Strawberry minus Pistachio')
plt.xlabel('Timestamp')
plt.ylabel('Price Difference')
plt.legend()
plt.show()






"""
for product in GalaxySoundsRecorders:
    # Filter the dataframes for the specific product
    product_prices = prices[prices['product'] == product].copy()
    product_trades = trades[trades['symbol'] == product].copy()
    
    # FIX: Assign the calculation to the DataFrame, not the string variable
    product_prices["mid_calc"] = (product_prices["bid_price_1"] + product_prices["ask_price_1"]) / 2
    
    # Plotting with the product name in the label for clarity
    plt.figure(figsize=(10, 4))
    plt.plot(product_prices["timestamp"], product_prices["ask_price_1"], label=f"Best Ask", alpha=0.5)
    plt.plot(product_prices["timestamp"], product_prices["bid_price_1"], label=f"Best Bid", alpha=0.5)
    plt.plot(product_prices["timestamp"], product_prices["mid_price"], label="Mid Price", color='blue', linewidth=0.5)

    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
    
    plt.title(f"Price Analysis for {product}")
    plt.legend()
    plt.show()
"""


"""
# rolling mid point
rolling_window1=5
prices1 = []
rolling_prices1 = []

for _, row in hydrogel.iterrows():
    if pd.isna(row['bid_price_1']) or pd.isna(row['ask_price_1']):
        rolling_prices1.append(rolling_prices1[-1] if rolling_prices1 else None)
        continue
    mid = int((row['bid_price_1'] + row['ask_price_1']) / 2)
    prices1.append(mid)
    if len(prices1) > rolling_window1:
        prices1.pop(0)
    rolling_prices1.append(int(sum(prices1) / len(prices1)))



hydrogel['rolling_price_1'] = rolling_prices1


# EMA lines
ema_alphas = {"ema_0.01": 0.01, "ema_0.005": 0.005, "ema_0.002": 0.002}
ema_values = {k: [] for k in ema_alphas}
ema_state  = {k: None for k in ema_alphas}

for _, row in hydrogel.iterrows():
    if pd.isna(row['bid_price_1']) or pd.isna(row['ask_price_1']):
        for k in ema_alphas:
            ema_values[k].append(ema_values[k][-1] if ema_values[k] else None)
        continue
    mid = (row['bid_price_1'] + row['ask_price_1']) / 2
    for k, alpha in ema_alphas.items():
        if ema_state[k] is None:
            ema_state[k] = mid
        ema_state[k] = alpha * mid + (1 - alpha) * ema_state[k]
        ema_values[k].append(ema_state[k])

for k in ema_alphas:
    hydrogel[k] = ema_values[k]


#plt.figure()
#plt.plot(tomatoes["timestamp"], tomatoes["ask_price_1"], label="ask_price_1")
#plt.plot(tomatoes["timestamp"], tomatoes["mid_price"],   label="mid", linewidth=2)
#plt.plot(hydrogel["timestamp"], hydrogel["ask_price_1"], label="ask_price_1", alpha=0.5)
#plt.plot(hydrogel["timestamp"], hydrogel["bid_price_1"], label="bid_price_1", alpha=0.5 )
#plt.plot(hydrogel["timestamp"], hydrogel["mid_price"], label="mid_price", color='blue', linewidth=1)
#plt.plot(hydrogel["timestamp"], hydrogel["rolling_price_1"], label=f"rolling price 1 ({rolling_window1})", linewidth=2, color='green')

#plt.plot(hydrogel["timestamp"], hydrogel["ema_0.01"],  label="EMA α=0.01",  linewidth=2, color='red',    linestyle='--')



# colored dots for bot trades
#plt.scatter(hydrogel_trades["timestamp"], hydrogel_trades["price"],
#            color='red', zorder=5, label="bot trades", s=10)

"""


