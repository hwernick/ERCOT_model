import pandas as pd
import numpy as np

# Load all three years of price data
df = pd.read_csv("ercot_all_hub_prices.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)
df = df[df["hub"] == "HB_HOUSTON"].copy()
df = df.sort_values("timestamp").reset_index(drop=True)

# Load all three years of load data
load = pd.read_csv("ercot_all_load.csv")
load["timestamp"] = pd.to_datetime(load["timestamp"])
load = load.dropna()

# Merge load onto price data by hour
df["timestamp_hour"] = df["timestamp"].dt.floor("h")
load = load.rename(columns={"timestamp": "timestamp_hour"})
df = df.merge(load, on="timestamp_hour", how="left")

print(f"Load merge nulls: {df['load_mw'].isna().sum()}")

# --- TIME FEATURES ---
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.dayofweek
df["month"] = df["timestamp"].dt.month
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

# --- PRICE LAG FEATURES ---
df["price_lag_1h"]  = df["price"].shift(4)
df["price_lag_4h"]  = df["price"].shift(16)
df["price_lag_24h"] = df["price"].shift(96)

# --- ROLLING FEATURES ---
df["price_roll_mean_4h"]  = df["price"].shift(1).rolling(16).mean()
df["price_roll_mean_24h"] = df["price"].shift(1).rolling(96).mean()
df["price_roll_std_4h"]   = df["price"].shift(1).rolling(16).std()

# --- LOAD FEATURES ---
df["load_mw"] = df["load_mw"]
df["load_lag_1h"] = df["load_mw"].shift(4)
df["load_roll_mean_4h"] = df["load_mw"].shift(1).rolling(16).mean()

# --- TARGETS ---
df["target_price_1h"] = df["price"].shift(-4)
spike_threshold = df["price"].quantile(0.95)
df["target_spike"] = (df["target_price_1h"] >= spike_threshold).astype(int)

print(f"Spike threshold: ${spike_threshold:.2f}")

df = df.dropna()
print(f"Shape after dropping NaN: {df.shape}")

df.to_csv("ercot_2024_features.csv", index=False)
print("Saved to ercot_2024_features.csv")