import pandas as pd
import numpy as np

def analyze_market_features(file_path, categories_dict):
    # 1. Load and clean data
    df = pd.read_csv(file_path, delimiter=';')
    
    # pivot to get products as columns
    prices = df.pivot(index='timestamp', columns='product', values='mid_price')
    
    # 2. Reindex to ensure 100-unit spacing (handles missing timestamps)
    new_index = range(prices.index.min(), prices.index.max() + 100, 100)
    prices = prices.reindex(new_index)
    
    # 3. Create Smoothed Returns for each category (The "Macro" View)
    # Smoothing filters noise; pct_change identifies the "move"
    cat_indices = pd.DataFrame()
    for name, prods in categories_dict.items():
        existing = [p for p in prods if p in prices.columns]
        if existing:
            # We average the returns of all products in the category
            cat_indices[name] = prices[existing].pct_change().mean(axis=1).rolling(window=5).mean()

    # 4. Find lead-lags between CATEGORIES
    cat_results = []
    names = list(cat_indices.columns)
    lags = range(-20, 21) # +/- 2000 units

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            cat_a, cat_b = names[i], names[j]
            best_corr, best_lag = 0, 0
            
            for lag in lags:
                corr = cat_indices[cat_a].shift(lag).corr(cat_indices[cat_b])
                if abs(corr) > abs(best_corr):
                    best_corr, best_lag = corr, lag
            
            # Identify who leads based on shift direction
            leader = cat_a if best_lag > 0 else cat_b
            follower = cat_b if best_lag > 0 else cat_a
            
            cat_results.append({
                'Leader': leader,
                'Follower': follower,
                'Lag_Units': abs(best_lag) * 100,
                'Correlation': best_corr
            })

    # 5. Find lead-lags between INDIVIDUAL PRODUCTS (The "Micro" View)
    # This finds the specific "Bellwether" products
    prod_results = []
    # Flatten all products into one list for comparison
    all_prods = [p for sublist in categories_dict.values() for p in sublist if p in prices.columns]
    
    # Optimization: Let's just check the top Category pair to find the best sub-products
    if cat_results:
        top_pair = sorted(cat_results, key=lambda x: abs(x['Correlation']), reverse=True)[0]
        l_cat, f_cat = top_pair['Leader'], top_pair['Follower']
        
        for p_lead in categories_dict[l_cat]:
            for p_follow in categories_dict[f_cat]:
                if p_lead in prices.columns and p_follow in prices.columns:
                    s1 = prices[p_lead].pct_change().rolling(window=5).mean()
                    s2 = prices[p_follow].pct_change().rolling(window=5).mean()
                    
                    b_corr, b_lag = 0, 0
                    for lag in lags:
                        c = s1.shift(lag).corr(s2)
                        if abs(c) > abs(b_corr):
                            b_corr, b_lag = c, lag
                    
                    prod_results.append({
                        'Lead_Product': p_lead,
                        'Follow_Product': p_follow,
                        'Lag_Units': abs(b_lag) * 100,
                        'Correlation': b_corr
                    })

    return pd.DataFrame(cat_results).sort_values(by='Correlation', key=abs, ascending=False), \
           pd.DataFrame(prod_results).sort_values(by='Correlation', key=abs, ascending=False)

# --- Define Categories ---
categories = {
    "GalaxySounds": ["GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_SOLAR_FLAMES"],
    "SleepingPods": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
    "Microchips": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"],
    "Pebbles": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "Robots": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY", "ROBOT_IRONING"],
    "UVVisors": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"],
    "Translators": ["TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE"],
    "Panels": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OxygenShakes": ["OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"],
    "SnackPacks": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_STRAWBERRY", "SNACKPACK_RASPBERRY"]
}

# --- Execute ---
cat_summary, prod_summary = analyze_market_features("prices_round_5_day_2.csv", categories)

print("--- CATEGORY LEAD-LAG SUMMARY ---")
print(cat_summary.head(10))

print("\n--- SUB-PRODUCT DRILLDOWN (BEST PAIRS) ---")
print(prod_summary.head(10))
