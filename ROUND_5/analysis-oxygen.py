import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

prices = pd.read_csv("../prices_round_5.csv")


oxygen = ["OXYGEN_SHAKE_EVENING_BREATH","OXYGEN_SHAKE_CHOCOLATE","OXYGEN_SHAKE_GARLIC"]

prices = pd.read_csv("../prices_round_5.csv")



day3 = prices[(prices["product"].isin(oxygen))] # & (prices["day"] == 3)]

# One row per timestamp, value = mid_price
price_df = day3.pivot_table(
    index="timestamp", columns="product", values="mid_price"
).sort_index()

# ============================================================
# PER-OXYGEN RETURN
# Y-axis: change in mid_price from previous tick (price points)
# ============================================================
returns = price_df.diff()

# ========================================= RETURNS OXYGEN_SHAKE_EVENING_BREATH=======
fig, ax1 = plt.subplots(figsize=(10, 7), sharex=True)

colors = ['blue'] 
short = ['OXYGEN_SHAKE_EVENING_BREATH']

# --- Plot 1: Raw Returns ---
for col, name, color in zip(["OXYGEN_SHAKE_EVENING_BREATH"], short, colors):
    ax1.plot(returns[col].values, label=name, color=color)
ax1.set_title("Returns OXYGEN_SHAKE_EVENING_BREATH")
ax1.legend()

plt.tight_layout()
plt.show() # ONLY call this at the very end

# ========================================= RETURNS OXYGEN_SHAKE_CHOCOLATE=======
fig, ax1 = plt.subplots(figsize=(10, 7), sharex=True)

colors = ['orange'] 
short = ['OXYGEN_SHAKE_CHOCOLATE']

# --- Plot 1: Raw Returns ---
for col, name, color in zip(["OXYGEN_SHAKE_CHOCOLATE"], short, colors):
    ax1.plot(returns[col].values, label=name, color=color)
ax1.set_title("Returns OXYGEN_SHAKE_CHOCOLATE")
ax1.legend()

plt.tight_layout()
plt.show() # ONLY call this at the very end

# ========================================= RETURNS OXYGEN_SHAKE_GARLIC=======
# 1. Create the figure with 3 subplots upfront
fig, ax1 = plt.subplots(figsize=(10, 7), sharex=True)

colors = ['red'] # Matches your 2 oxygen
short = ['OXYGEN_SHAKE_GARLIC']

# --- Plot 1: Raw Returns ---
for col, name, color in zip(["OXYGEN_SHAKE_GARLIC"], short, colors):
    ax1.plot(returns[col].values, label=name, color=color)
ax1.set_title("Returns OXYGEN_SHAKE_GARLIC")
ax1.legend()

plt.tight_layout()
plt.show() # ONLY call this at the very end



# ======================================== ROLLING MEAN===========
# --- Plot 3: Rolling mean
rolling_mean = price_df.rolling(window=100, min_periods=1).mean()

# 2. Plotting
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
axes = [ax1, ax2, ax3]
colors = ['blue', 'orange','red']

for col, ax, color in zip(oxygen, axes, colors):
    # Plot raw price
    ax.plot(price_df[col].values, label='Actual Price', color=color, alpha=0.3)
    
    # Plot rolling mean
    ax.plot(rolling_mean[col].values, label='100-Tick Rolling Mean', color='black', linewidth=1.5)
    
    ax.set_title(f"Price vs Rolling Mean: {col}")
    ax.set_ylabel("Mid Price")
    ax.legend()

plt.xlabel("Timestamp")
plt.tight_layout()
plt.show()

# ======================================= z-scores

# 1. Calculate Time-Series Z-Score (Rolling 100)
window = 100
rolling_avg = price_df.rolling(window=window).mean()
rolling_std = price_df.rolling(window=window).std()
ts_z_scores = (price_df - rolling_avg) / rolling_std

# 2. Setup Figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
colors = ['blue', 'orange', 'red']

for i, col in enumerate(oxygen):
    # Plot Z-scores on the bottom axis
    ax2.plot(ts_z_scores.index, ts_z_scores[col], color=colors[i], label=f'{col} Z-Score', alpha=0.8)
    
    # --- PRINT ON GRAPH ---
    # Get latest value
    latest_z = ts_z_scores[col].iloc[-1]
    
    # Place text in top-left corner (0.02, 0.95) and step down for each pebble
    ax2.text(0.02, 0.95 - (i * 0.07), f"Latest {col} Z: {latest_z:.2f}", 
             transform=ax2.transAxes,  # Coordinate system: 0=bottom/left, 1=top/right
             color=colors[i], 
             fontweight='bold',
             fontsize=12,
             bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

# 3. Add trading thresholds
ax2.axhline(2, color='red', linestyle='--', alpha=0.5, label='Overbought (+2)')
ax2.axhline(-2, color='green', linestyle='--', alpha=0.5, label='Oversold (-2)')
ax2.axhline(0, color='black', linewidth=0.8)

ax2.set_title("Time-Series Z-Score (Deviation from 100-Tick Moving Average)")
ax2.legend(loc='lower right')

# Plot raw prices on top for context
for i, col in enumerate(oxygen):
    ax1.plot(price_df.index, price_df[col], color=colors[i], label=col)
ax1.set_title("Raw Mid Prices")
ax1.legend()

plt.tight_layout()
plt.show()


