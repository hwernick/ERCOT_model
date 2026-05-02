
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, classification_report
import pickle

# Load our feature set
df = pd.read_csv("ercot_2024_features.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# --- DEFINE FEATURES AND TARGETS ---
# These are the columns the model gets to look at
FEATURES = [
    "hour", "day_of_week", "month", "is_weekend",
    "hour_sin", "hour_cos",
    "price_lag_1h", "price_lag_4h", "price_lag_24h",
    "price_roll_mean_4h", "price_roll_mean_24h", "price_roll_std_4h",
    "load_mw", "load_lag_1h", "load_roll_mean_4h"
]

X = df[FEATURES]

# Two separate targets
y_price = df["target_price_1h"]   # regression - what will price be?
y_spike = df["target_spike"]       # classification - will it spike?

# --- TRAIN/TEST SPLIT ---
# IMPORTANT: we split by time, not randomly
# Training on future data to predict the past would be cheating
# We train on first 80% of the year, test on last 20%
split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test  = X.iloc[split_index:]

y_price_train = y_price.iloc[:split_index]
y_price_test  = y_price.iloc[split_index:]

y_spike_train = y_spike.iloc[:split_index]
y_spike_test  = y_spike.iloc[split_index:]

print(f"Training on {len(X_train)} intervals")
print(f"Testing on {len(X_test)} intervals")
print(f"Test period starts: {df['timestamp'].iloc[split_index]}")

# --- MODEL 1: PRICE FORECASTER (regression) ---
print("\nTraining price forecast model...")

price_model = lgb.LGBMRegressor(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    random_state=42
)

price_model.fit(X_train, y_price_train)

price_preds = price_model.predict(X_test)
mae = mean_absolute_error(y_price_test, price_preds)
print(f"Price Model MAE: ${mae:.2f}")

# --- MODEL 2: SPIKE CLASSIFIER ---
print("\nTraining spike classifier...")

spike_model = lgb.LGBMClassifier(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    scale_pos_weight=19,  # spikes are 5% of data so we up-weight them
    random_state=42
)

spike_model.fit(X_train, y_spike_train)

spike_preds = spike_model.predict(X_test)
print("\nSpike Classifier Report:")
print(classification_report(y_spike_test, spike_preds,
      target_names=["Normal", "Spike"]))

# --- SAVE MODELS ---
with open("price_model.pkl", "wb") as f:
    pickle.dump(price_model, f)

with open("spike_model.pkl", "wb") as f:
    pickle.dump(spike_model, f)

print("\nModels saved.")