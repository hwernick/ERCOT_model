import requests
import pandas as pd


def fetch_eia_wind(year, api_key):
    url = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
    all_records = []
    offset = 0

    while True:
        params = {
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": "ERCO",
            "facets[fueltype][]": "WND",
            "start": f"{year}-01-01T00",
            "end": f"{year}-12-31T23",
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": 5000,
            "api_key": "7kiTkcm6UdcW9BUiWuZpcl2SX2sJW0vFgAb0RfZa"
        }
        response = requests.get(url, params=params)
        data = response.json()

        # Add this temporarily to see what's coming back
        if "response" not in data:
            print(f"API error for {year}: {data}")
            break

        records = data["response"]["data"]

        response = requests.get(url, params=params)
        data = response.json()
        records = data["response"]["data"]

        if not records:
            break

        all_records.extend(records)
        print(f"  {year}: fetched {len(all_records)} rows so far...")

        if len(records) < 5000:
            break

        offset += 5000

    df = pd.DataFrame(all_records)
    df["timestamp"] = pd.to_datetime(df["period"])
    df = df[["timestamp", "value"]].rename(columns={"value": "wind_mw"})
    df["wind_mw"] = pd.to_numeric(df["wind_mw"])

    print(f"{year}: {len(df)} total rows, wind range: {df['wind_mw'].min():.0f} - {df['wind_mw'].max():.0f} MW")
    return df


YAK = "7kiTkcm6UdcW9BUiWuZpcl2SX2sJW0vFgAb0RfZa"

wind_2019 = fetch_eia_wind(2019, YAK)
wind_2020 = fetch_eia_wind(2020, YAK)
wind_2021 = fetch_eia_wind(2021, YAK)
wind_2022 = fetch_eia_wind(2022, YAK)
wind_2023 = fetch_eia_wind(2023, YAK)
wind_2024 = fetch_eia_wind(2024, YAK)

all_wind = pd.concat([wind_2019, wind_2020, wind_2021,
                      wind_2022, wind_2023, wind_2024]).reset_index(drop=True)
all_wind = all_wind.sort_values("timestamp").reset_index(drop=True)

print(f"\nTotal shape: {all_wind.shape}")
all_wind.to_csv("ercot_all_wind.csv", index=False)
print("Saved to ercot_all_wind.csv")