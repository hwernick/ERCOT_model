import pandas as pd
import numpy as np

# Load all 7 years of price data
df = pd.read_csv("ercot_all_hub_prices.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)

# Work with Houston only
df = df[df["hub"] == "HB_HOUSTON"].copy()
df = df.sort_values("timestamp").reset_index(drop=True)

# Create timestamp_hour for merging hourly data
df["timestamp_hour"] = df["timestamp"].dt.floor("h")

# --- LOAD DATA ---
load = pd.read_csv("ercot_all_load.csv")
load["timestamp"] = pd.to_datetime(load["timestamp"])
load = load.rename(columns={"timestamp": "timestamp_hour"})
df = df.merge(load, on="timestamp_hour", how="left")
print(f"Load merge nulls: {df['load_mw'].isna().sum()}")

# --- WIND DATA ---
wind = pd.read_csv("ercot_all_wind.csv")
wind["timestamp"] = pd.to_datetime(wind["timestamp"])
wind = wind.rename(columns={"timestamp": "timestamp_hour"})
df = df.merge(wind, on="timestamp_hour", how="left")
print(f"Wind merge nulls: {df['wind_mw'].isna().sum()}")

# --- TEMPERATURE DATA ---
temp = pd.read_csv("ercot_all_temp.csv")
temp["timestamp"] = pd.to_datetime(temp["timestamp"])
temp = temp.rename(columns={"timestamp": "timestamp_hour"})
df = df.merge(temp, on="timestamp_hour", how="left")
print(f"Temp merge nulls: {df['temp_f'].isna().sum()}")

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

# --- ROLLING PRICE FEATURES ---
df["price_roll_mean_4h"]  = df["price"].shift(1).rolling(16).mean()
df["price_roll_mean_24h"] = df["price"].shift(1).rolling(96).mean()
df["price_roll_std_4h"]   = df["price"].shift(1).rolling(16).std()

# --- LOAD FEATURES ---
df["load_lag_1h"]       = df["load_mw"].shift(4)
df["load_roll_mean_4h"] = df["load_mw"].shift(1).rolling(16).mean()

# --- WIND FEATURES (NaN ok for 2018 - LightGBM handles it) ---
df["wind_lag_1h"]      = df["wind_mw"].shift(4)
df["net_load"]         = df["load_mw"] - df["wind_mw"]
df["wind_pct_of_load"] = df["wind_mw"] / df["load_mw"]

# --- TEMPERATURE FEATURES ---
df["temp_lag_1h"]        = df["temp_f"].shift(4)
df["temp_roll_mean_4h"]  = df["temp_f"].shift(1).rolling(16).mean()
df["cooling_degrees"]    = (df["temp_f"] - 65).clip(lower=0)

# --- TARGETS ---
df["target_price_1h"] = df["price"].shift(-4)
spike_threshold = df["price"].quantile(0.95)
df["target_spike"] = (df["target_price_1h"] >= spike_threshold).astype(int)

print(f"Spike threshold: ${spike_threshold:.2f}")

# Only drop rows missing core features - wind NaNs are fine
core_cols = ["price", "load_mw", "price_lag_1h", "target_price_1h"]
df = df.dropna(subset=core_cols)

print(f"Shape after dropping NaN: {df.shape}")
print(f"Spike intervals: {df['target_spike'].sum()}")

df.to_csv("ercot_2024_features.csv", index=False)
print("Saved to ercot_2024_features.csv")