import pandas as pd


def load_native_load(filepath):
    df = pd.read_excel(filepath)
    print(f"  Columns: {df.columns.tolist()[:5]}")

    def parse_ercot_hour(s):
        s = str(s).strip().replace(" DST", "")
        if s.endswith("24:00"):
            s = s.replace("24:00", "00:00")
            for fmt in ["%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M"]:
                try:
                    return pd.to_datetime(s, format=fmt) + pd.Timedelta(days=1)
                except:
                    continue
        for fmt in ["%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M"]:
            try:
                return pd.to_datetime(s, format=fmt)
            except:
                continue
        return pd.NaT

    # Handle different column names across years
    hour_col = "Hour Ending" if "Hour Ending" in df.columns else df.columns[0]
    ercot_col = "ERCOT" if "ERCOT" in df.columns else [c for c in df.columns if "ERCOT" in str(c)][0]

    df["timestamp"] = df[hour_col].apply(parse_ercot_hour)
    df = df[["timestamp", ercot_col]].rename(columns={ercot_col: "load_mw"})
    return df


print("Loading all 7 years of load data...")

years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
all_loads = []

for year in years:
    print(f"Loading {year}...")
    df = load_native_load(f"Native_Load_{year}.xlsx")
    df = df.dropna()
    all_loads.append(df)
    print(f"  {year}: {len(df)} rows")

all_load = pd.concat(all_loads).reset_index(drop=True)
all_load = all_load.sort_values("timestamp").reset_index(drop=True)

print(f"\nTotal shape: {all_load.shape}")
print(f"Date range: {all_load['timestamp'].min()} to {all_load['timestamp'].max()}")

all_load.to_csv("ercot_all_load.csv", index=False)
print("Saved to ercot_all_load.csv")