import gridstatus
import pandas as pd

ercot = gridstatus.Ercot()

all_years = []

for year in [2022, 2023, 2024]:
    print(f"Fetching {year} price data...")
    df = ercot.get_rtm_spp(year=year, verbose=False)

    # Filter to our four hubs
    HUBS = ["HB_HOUSTON", "HB_NORTH", "HB_SOUTH", "HB_WEST"]
    df = df[df["Location"].isin(HUBS)]
    df = df[["Interval Start", "Location", "SPP"]]
    df = df.rename(columns={"Interval Start": "timestamp", "Location": "hub", "SPP": "price"})

    all_years.append(df)
    print(f"  Got {len(df)} rows")

# Combine all years
combined = pd.concat(all_years).reset_index(drop=True)
combined["timestamp"] = pd.to_datetime(combined["timestamp"], utc=True).dt.tz_localize(None)
combined = combined.sort_values("timestamp").reset_index(drop=True)

print(f"\nTotal shape: {combined.shape}")
print(f"Date range: {combined['timestamp'].min()} to {combined['timestamp'].max()}")

combined.to_csv("ercot_all_hub_prices.csv", index=False)
print("Saved to ercot_all_hub_prices.csv")