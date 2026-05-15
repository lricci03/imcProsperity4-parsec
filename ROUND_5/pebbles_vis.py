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



prices = pd.read_csv("../prices_round_5.csv")
trades = pd.read_csv("../trades_round_5.csv")

PurificationPebbles = ["PEBBLES_XS",
                        "PEBBLES_S",
                        "PEBBLES_M", 
                        "PEBBLES_L", 
                        "PEBBLES_XL"]


xs = prices[prices['product'] == "PEBBLES_XS"].copy()
xs_trades = trades[trades['symbol'] == "PEBBLES_XS"].copy()


s = prices[prices['product'] == "PEBBLES_S"].copy()
s_trades = trades[trades['symbol'] == "PEBBLES_S"].copy()

m = prices[prices['product'] == "PEBBLES_M"].copy()
m_trades = trades[trades['symbol'] == "PEBBLES_M"].copy()

l = prices[prices['product'] == "PEBBLES_L"].copy()
l_trades = trades[trades['symbol'] == "PEBBLES_L"].copy()

xl = prices[prices['product'] == "PEBBLES_XL"].copy()
xl_trades = trades[trades['symbol'] == "PEBBLES_XL"].copy()

# 1. Merge XS and S
step1 = pd.merge(
    xs[['timestamp', 'mid_price']], 
    s[['timestamp', 'mid_price']], 
    on='timestamp', 
    suffixes=('_xs', '_s')
)

# 2. Merge M into the result
step2 = pd.merge(
    step1, 
    m[['timestamp', 'mid_price']], 
    on='timestamp'
)
# Rename the new 'mid_price' column from M so it doesn't get confused later
step2 = step2.rename(columns={'mid_price': 'mid_price_m'})

# 3. Merge L into the result
step3 = pd.merge(
    step2, 
    l[['timestamp', 'mid_price']], 
    on='timestamp'
)
# Rename the new 'mid_price' column from L
step3 = step3.rename(columns={'mid_price': 'mid_price_l'})

# 4. Calculate the sum
step3['total_sum'] = (
    step3['mid_price_xs'] + 
    step3['mid_price_s'] + 
    step3['mid_price_m'] + 
    step3['mid_price_l']
)

# merge xl
step4 = pd.merge(
    step3, 
    xl[['timestamp', 'mid_price']], 
    on='timestamp'
)

# Rename the new 'mid_price' column from XL
step4 = step4.rename(columns={'mid_price': 'mid_price_xl'})

step4['total_sum'] = (
    step4['mid_price_xs'] + 
    step4['mid_price_s'] + 
    step4['mid_price_m'] + 
    step4['mid_price_l'] +
    step4['mid_price_xl']
)
step4['diff'] = (
    step4['mid_price_xs'] + 
    step4['mid_price_s'] + 
    step4['mid_price_m'] + 
    step4['mid_price_l'] -
    step4['mid_price_xl']
)




plt.plot(xs["timestamp"], xs["mid_price"], label="XS mid_price", linewidth=0.5, alpha=0.8)
plt.plot(s["timestamp"], s["mid_price"], label="S mid_price", linewidth=0.5, alpha=0.8)
plt.plot(m["timestamp"], m["mid_price"], label="M mid_price", linewidth=0.5, alpha=0.8)
plt.plot(l["timestamp"], l["mid_price"], label="L mid_price", linewidth=0.5, alpha=0.8)
plt.plot(xl["timestamp"], xl["mid_price"], label="XL mid_price", linewidth=0.5, alpha=0.8)
plt.plot(step3['timestamp'], step3['total_sum'], label="xs+s+m+l", linewidth=1, alpha=0.8) 
plt.plot(step4['timestamp'], step4['total_sum'], label="xs+s+m+l+xl", linewidth=1, alpha=0.8) 
plt.plot(step4['timestamp'], step4['diff'], label="xs+s+m+l-xl", linewidth=1, alpha=0.8) 

# colored dots for bot trades
plt.scatter(xs_trades["timestamp"], xs_trades["price"],
            color='red', zorder=5, label="bot trades", s=3)
plt.scatter(s_trades["timestamp"], s_trades["price"],
            color='red', zorder=5, label="bot trades", s=3)
plt.scatter(m_trades["timestamp"], m_trades["price"],
            color='red', zorder=5, label="bot trades", s=3)
plt.scatter(l_trades["timestamp"], l_trades["price"],
            color='red', zorder=5, label="bot trades", s=3)
plt.scatter(xl_trades["timestamp"], xl_trades["price"],
            color='red', zorder=5, label="bot trades", s=3)


plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.legend()
plt.xlabel("Timestamp")
plt.ylabel("Price")
plt.title(f"Pebbles")
plt.show()


"""
plt.figure(figsize=(10, 5))
plt.plot(s['timestamp'], s['mid_price'], label='XS', linewidth=0.5)
plt.plot(strawberry['timestamp'], strawberry['bid_price_1'], label='Strawberry best bid', linewidth=0.5)
plt.plot(strawberry['timestamp'], strawberry['ask_price_1'], label='Strawberry best ask', linewidth=0.5)
plt.plot(pistachio['timestamp'], pistachio['mid_price'], label='Pistachio', linewidth=0.5)
plt.plot(pistachio['timestamp'], pistachio['bid_price_1'], label='Pistachio best bid', linewidth=0.5)
plt.plot(pistachio['timestamp'], pistachio['ask_price_1'], label='Pistachio best ask', linewidth=0.5)

plt.title('Strawberry vs Pistachio')
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
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




