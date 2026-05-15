import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# Load data
prices_1 = pd.read_csv("../prices_round_5.csv")

# Filter snacks
ProteinSnackPacks = [
    'SNACKPACK_CHOCOLATE',
    'SNACKPACK_VANILLA',
    'SNACKPACK_PISTACHIO',
    'SNACKPACK_STRAWBERRY',
    'SNACKPACK_RASPBERRY',
]

snack_data = prices_1[prices_1['product'].isin(ProteinSnackPacks)].copy()

# Build merged dataframe
product = ProteinSnackPacks[0]
snackpacks_prices_df = snack_data[snack_data['product'] == product][['timestamp']].copy()

for product in ProteinSnackPacks:
    new_df = snack_data[snack_data['product'] == product][['timestamp', 'mid_price']].copy()
    new_df = new_df.rename(columns={"mid_price": product})
    snackpacks_prices_df = snackpacks_prices_df.merge(new_df, how='left', on='timestamp')

df = snackpacks_prices_df.drop('timestamp', axis=1).dropna().reset_index(drop=True)

print("="*80)
print("FORWARD PREDICTION: Testing ALL product pairs with LAGS")
print("="*80)

# ============================================================================
# Test all pairs with different lags
# ============================================================================
test_lags = [1, 2, 3, 5, 10]
all_results = []

for predictor in ProteinSnackPacks:
    for target in ProteinSnackPacks:
        if predictor == target:
            continue
        
        pred_short = predictor.replace('SNACKPACK_', '')
        target_short = target.replace('SNACKPACK_', '')
        
        print(f"\n{'='*80}")
        print(f"Testing: {pred_short} → {target_short}")
        print(f"{'='*80}")
        
        best_r2 = -1
        best_lag = None
        best_model = None
        best_rmse = None
        best_corr = None
        best_samples = None
        
        for lag in test_lags:
            # Create lagged features
            df_lag = df.copy()
            df_lag['PREDICTOR_LAG'] = df_lag[predictor].shift(lag)
            df_lag_clean = df_lag.dropna()
            
            if len(df_lag_clean) < 2:
                continue
            
            # Fit model
            X = df_lag_clean[['PREDICTOR_LAG']].values
            y = df_lag_clean[target].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Metrics
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            corr = df_lag_clean['PREDICTOR_LAG'].corr(df_lag_clean[target])
            
            print(f"  Lag={lag:2d}: R²={r2:.4f}, RMSE={rmse:7.2f}, Corr={corr:7.4f}, N={len(df_lag_clean)}")
            
            # Track best
            if r2 > best_r2:
                best_r2 = r2
                best_lag = lag
                best_model = model
                best_rmse = rmse
                best_corr = corr
                best_samples = len(df_lag_clean)
        
        if best_lag is not None:
            print(f"\n  ✓ Best: Lag={best_lag}, R²={best_r2:.4f}")
            
            all_results.append({
                'Predictor': pred_short,
                'Target': target_short,
                'Best_Lag': best_lag,
                'R²': best_r2,
                'RMSE': best_rmse,
                'Correlation': best_corr,
                'N_samples': best_samples,
                'Pair': f"{pred_short} → {target_short}"
            })

# ============================================================================
# SUMMARY TABLE
# ============================================================================
print(f"\n{'='*80}")
print("SUMMARY: ALL PAIRS WITH BEST LAG")
print(f"{'='*80}\n")

df_results = pd.DataFrame(all_results)
df_results_sorted = df_results.sort_values('R²', ascending=False)

print(df_results_sorted[['Predictor', 'Target', 'Best_Lag', 'R²', 'RMSE', 'Correlation']].to_string(index=False))

# ============================================================================
# IDENTIFY GOOD PREDICTORS (R² > 0.7)
# ============================================================================
print(f"\n{'='*80}")
print("🏆 GOOD PREDICTORS (R² > 0.7)")
print(f"{'='*80}\n")

good_predictors = df_results_sorted[df_results_sorted['R²'] > 0.7]

if len(good_predictors) > 0:
    for _, row in good_predictors.iterrows():
        print(f"  {row['Predictor']:15} → {row['Target']:15} | LAG={row['Best_Lag']:2d}, R²={row['R²']:.4f}")
else:
    print("  None found with R² > 0.7")

# ============================================================================
# VISUALIZATION 1: Heatmap of best R² for each pair
# ============================================================================
products_short = [p.replace('SNACKPACK_', '') for p in ProteinSnackPacks]
r2_matrix = pd.DataFrame(0.0, index=products_short, columns=products_short)
lag_matrix = pd.DataFrame(0, index=products_short, columns=products_short)

for _, row in df_results.iterrows():
    r2_matrix.loc[row['Predictor'], row['Target']] = row['R²']
    lag_matrix.loc[row['Predictor'], row['Target']] = row['Best_Lag']

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# R² heatmap
sns.heatmap(r2_matrix, annot=True, fmt='.3f', cmap='RdYlGn', center=0.5,
            vmin=0, vmax=1, square=True, ax=axes[0], cbar_kws={'label': 'R² Score'},
            linewidths=0.5)
axes[0].set_title('Prediction Quality (R²)\nRow predicts Column(t)', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Predictor (past)', fontweight='bold')
axes[0].set_xlabel('Target (future)', fontweight='bold')

# Lag heatmap
sns.heatmap(lag_matrix, annot=True, fmt='d', cmap='coolwarm',
            square=True, ax=axes[1], cbar_kws={'label': 'Best Lag'},
            linewidths=0.5)
axes[1].set_title('Best Lag for Each Pair\nRow predicts Column(t)', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Predictor (past)', fontweight='bold')
axes[1].set_xlabel('Target (future)', fontweight='bold')

plt.suptitle('Forward Prediction Analysis: All Product Pairs', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('all_pairs_prediction_heatmaps.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================================
# VISUALIZATION 2: Ranked by R²
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 8))

df_plot = df_results_sorted.head(15)  # Top 15 pairs
colors = ['green' if r2 > 0.7 else 'orange' if r2 > 0.5 else 'red' 
          for r2 in df_plot['R²']]

y_pos = np.arange(len(df_plot))
ax.barh(y_pos, df_plot['R²'], color=colors, alpha=0.8, edgecolor='black')

ax.set_yticks(y_pos)
ax.set_yticklabels([f"{row['Predictor']:10} → {row['Target']:10}" 
                     for _, row in df_plot.iterrows()], fontsize=9)
ax.set_xlabel('R² Score (prediction quality)', fontweight='bold')
ax.axvline(x=0.7, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Good (0.7)')
ax.axvline(x=0.5, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='Moderate (0.5)')
ax.set_xlim(0, 1)
ax.grid(axis='x', alpha=0.3)

# Add value labels
for i, (idx, row) in enumerate(df_plot.iterrows()):
    ax.text(row['R²'] + 0.02, i, f"LAG={row['Best_Lag']}", va='center', fontsize=8, fontweight='bold')

ax.legend(loc='lower right', fontsize=9)
plt.title('Top Predictions: Which Product Pair Works Best?\n(LAG values shown on bars)', 
          fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('all_pairs_prediction_ranked.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================================
# VISUALIZATION 3: Distribution of R² scores
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(df_results['R²'], bins=15, color='#4ECDC4', alpha=0.8, edgecolor='black')
ax.axvline(x=0.7, color='green', linestyle='--', linewidth=2, label='Good (0.7)')
ax.axvline(x=0.5, color='orange', linestyle='--', linewidth=2, label='Moderate (0.5)')
ax.axvline(x=df_results['R²'].mean(), color='red', linestyle='--', linewidth=2, 
           label=f'Mean ({df_results["R²"].mean():.3f})')

ax.set_xlabel('R² Score', fontweight='bold')
ax.set_ylabel('Number of Pairs', fontweight='bold')
ax.set_title('Distribution of Prediction Quality Across All Pairs', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('all_pairs_prediction_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================================
# STATISTICS
# ============================================================================
print(f"\n{'='*80}")
print("STATISTICS")
print(f"{'='*80}\n")

print(f"Total pairs tested: {len(df_results)}")
print(f"\nR² Distribution:")
print(f"  Mean:     {df_results['R²'].mean():.4f}")
print(f"  Median:   {df_results['R²'].median():.4f}")
print(f"  Min:      {df_results['R²'].min():.4f}")
print(f"  Max:      {df_results['R²'].max():.4f}")
print(f"  Std:      {df_results['R²'].std():.4f}")

print(f"\nPairs by quality:")
print(f"  R² > 0.8 (Excellent):  {(df_results['R²'] > 0.8).sum():2d} pairs")
print(f"  R² > 0.7 (Good):       {(df_results['R²'] > 0.7).sum():2d} pairs")
print(f"  R² > 0.5 (Moderate):   {(df_results['R²'] > 0.5).sum():2d} pairs")
print(f"  R² ≤ 0.5 (Poor):       {(df_results['R²'] <= 0.5).sum():2d} pairs")

print(f"\nBest lag usage:")
for lag in sorted(df_results['Best_Lag'].unique()):
    count = (df_results['Best_Lag'] == lag).sum()
    print(f"  Lag {lag:2d}: {count:2d} pairs")

print(f"\n{'='*80}")
print("✅ CONCLUSION")
print(f"{'='*80}\n")

if (df_results['R²'] > 0.7).sum() > 0:
    print(f"✓ YES! You can use lags to predict future prices.")
    print(f"  Found {(df_results['R²'] > 0.7).sum()} pairs with R² > 0.7 (good predictions)")
else:
    print(f"✗ Limited predictive power found.")
    print(f"  Best pair: {df_results_sorted.iloc[0]['Pair']} with R²={df_results_sorted.iloc[0]['R²']:.4f}")