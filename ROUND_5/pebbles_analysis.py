import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

prices = pd.read_csv("../prices_round_5.csv")

pebbles = ["PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"]

# One row per timestamp, only day 2
day3 = prices[(prices["product"].isin(pebbles)) & (prices["day"] == 3)]
price_df = day3.pivot_table(index="timestamp", columns="product", values="mid_price").sort_index()

print(price_df.shape)
print(price_df.head(3))

mean_prices    = price_df.mean()
basket         = price_df.sum(axis=1)
basket_dev     = basket - 50000
contributions  = price_df - mean_prices

print(f"\nBasket deviation stats: mean={basket_dev.mean():.3f}  std={basket_dev.std():.3f}  max={basket_dev.abs().max():.1f}")
print(f"Big deviations (>10): {(basket_dev.abs() > 10).sum()} timestamps")

# Just plot the first 500 timestamps — no filtering, guaranteed non-empty
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

ax1.plot(basket_dev.iloc[:500].values, color="black", linewidth=1)
ax1.axhline(+10, color="red",   linestyle="--")
ax1.axhline(-10, color="green", linestyle="--")
ax1.set_title("Basket deviation from 50,000")

for col, name in zip(pebbles, ["L","M","S","XL","XS"]):
    ax2.plot(contributions[col].iloc[:500].values, linewidth=0.8, label=name)
ax2.axhline(0, color="black", linewidth=0.5)
ax2.set_title("Per-pebble contribution")
ax2.legend()

plt.tight_layout()
plt.show()



prices = pd.read_csv("prices_round_5.csv")

pebbles = ["PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"]

day3 = prices[(prices["product"].isin(pebbles)) & (prices["day"] == 3)]

# One row per timestamp, one column per pebble, value = mid_price
price_df = day3.pivot_table(index="timestamp", columns="product", values="mid_price").sort_index()

# ============================================================
# BASKET DEVIATION
# At each timestamp: sum of all 5 mid_prices minus 50,000
# Units: price points (same as mid_price)
# Should always be close to 0. Spikes = mispricing event.
# ============================================================
basket_dev = price_df.sum(axis=1) - 50000

# ============================================================
# PER-PEBBLE RETURN
# Tick-by-tick change in mid_price for each pebble.
# Units: price points (e.g. +20 means mid_price rose by 20)
# This is NOT the mid_price itself — it's the CHANGE.
# We use this to see WHO moved at the moment of the spike.
# ============================================================
returns = price_df.diff()

# ============================================================
# FIND SPIKE TIMESTAMPS
# We look for moments where the basket deviates by more than 10.
# We then group nearby spikes so we don't plot the same event twice.
# ============================================================
spike_mask = basket_dev.abs() > 10
spike_timestamps = basket_dev[spike_mask].index.tolist()

# Keep only one spike per cluster (min 30 ticks apart)
# so we get genuinely different events
selected_spikes = []
last = -999
for t in spike_timestamps:
    if t - last > 30:
        selected_spikes.append(t)
        last = t
    if len(selected_spikes) == 6:  # plot 6 different spike events
        break

print(f"Plotting {len(selected_spikes)} distinct spike events")

fig, axes = plt.subplots(len(selected_spikes), 2, figsize=(16, 3.5 * len(selected_spikes)))

for row, center in enumerate(selected_spikes):
    idx_pos = price_df.index.get_loc(center)
    window  = slice(max(0, idx_pos - 15), idx_pos + 15)

    x_vals  = basket_dev.iloc[window].index  # actual timestamps on x-axis

    # ── LEFT PANEL: basket deviation ──
    ax_left = axes[row, 0]
    ax_left.plot(x_vals, basket_dev.iloc[window].values, color="black", linewidth=1.5)
    ax_left.axhline(+10, color="red",   linestyle="--", linewidth=0.8, label="+10")
    ax_left.axhline(-10, color="green", linestyle="--", linewidth=0.8, label="-10")
    ax_left.axhline(0,   color="black", linewidth=0.4)
    ax_left.axvline(center, color="orange", linewidth=1, linestyle=":")  # mark the spike
    ax_left.set_title(f"Spike at t={center} — Basket deviation")
    ax_left.set_ylabel("Price points\n(sum of 5 mid_prices − 50,000)")
    ax_left.legend(fontsize=7)

    # ── RIGHT PANEL: per-pebble return ──
    # Y-axis = change in mid_price from previous tick (price points)
    # e.g. +20 means that pebble's mid_price rose by 20 in one tick
    ax_right = axes[row, 1]
    colors = ["blue","orange","green","red","purple"]
    short  = ["L","M","S","XL","XS"]
    for col, name, color in zip(pebbles, short, colors):
        ax_right.plot(x_vals, returns[col].iloc[window].values,
                      linewidth=1, label=name, color=color, marker="o", markersize=2)
    ax_right.axhline(0, color="black", linewidth=0.5)
    ax_right.axvline(center, color="orange", linewidth=1, linestyle=":")
    ax_right.set_title(f"Spike at t={center} — Per-pebble tick return")
    ax_right.set_ylabel("Price points\n(change in mid_price vs prev tick)")
    ax_right.legend(fontsize=7)

plt.tight_layout()
plt.show()


prices = pd.read_csv("prices_round_5.csv")

pebbles = ["PEBBLES_L","PEBBLES_M","PEBBLES_S","PEBBLES_XL","PEBBLES_XS"]

day3 = prices[(prices["product"].isin(pebbles)) & (prices["day"] == 3)]

# One row per timestamp, value = mid_price
price_df = day3.pivot_table(
    index="timestamp", columns="product", values="mid_price"
).sort_index()

# ============================================================
# PER-PEBBLE RETURN
# Y-axis: change in mid_price from previous tick (price points)
# ============================================================
returns = price_df.diff()

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
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

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
plt.show()