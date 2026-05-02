import pandas as pd


def load_native_load(filepath):
    df = pd.read_excel(filepath)

    def parse_ercot_hour(s):
        s = str(s).strip().replace(" DST", "")
        if s.endswith("24:00"):
            s = s.replace("24:00", "00:00")
            # Try both date formats
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

    df["timestamp"] = df["Hour Ending"].apply(parse_ercot_hour)
    df = df[["timestamp", "ERCOT"]].rename(columns={"ERCOT": "load_mw"})
    return df


print("Loading all three years of load data...")

load_2022 = load_native_load("Native_Load_2022.xlsx")
print(f"2022: {len(load_2022)} rows, nulls: {load_2022['timestamp'].isna().sum()}")

load_2023 = load_native_load("Native_Load_2023.xlsx")
print(f"2023: {len(load_2023)} rows, nulls: {load_2023['timestamp'].isna().sum()}")

load_2024 = load_native_load("Native_Load_2024.xlsx")
print(f"2024: {len(load_2024)} rows, nulls: {load_2024['timestamp'].isna().sum()}")

all_load = pd.concat([load_2022, load_2023, load_2024]).reset_index(drop=True)
all_load = all_load.sort_values("timestamp").reset_index(drop=True)

print(f"\nTotal shape: {all_load.shape}")
print(f"Date range: {all_load['timestamp'].min()} to {all_load['timestamp'].max()}")

all_load.to_csv("ercot_all_load.csv", index=False)
print("Saved to ercot_all_load.csv")