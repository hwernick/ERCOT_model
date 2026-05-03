import requests
import pandas as pd


# Open-Meteo free historical weather API
# No signup, no API key needed
# Using Houston coordinates (29.76, -95.37)

def fetch_temperature(year):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": 29.76,
        "longitude": -95.37,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "hourly": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "timezone": "America/Chicago"
    }

    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["hourly"]["time"]),
        "temp_f": data["hourly"]["temperature_2m"]
    })

    print(f"{year}: {len(df)} rows, temp range: {df['temp_f'].min():.1f}F - {df['temp_f'].max():.1f}F")
    return df


temp_2018 = fetch_temperature(2018)
temp_2019 = fetch_temperature(2019)
temp_2020 = fetch_temperature(2020)
temp_2021 = fetch_temperature(2021)
temp_2022 = fetch_temperature(2022)
temp_2023 = fetch_temperature(2023)
temp_2024 = fetch_temperature(2024)

all_temp = pd.concat([temp_2018, temp_2019, temp_2020, temp_2021,
                      temp_2022, temp_2023, temp_2024]).reset_index(drop=True)
all_temp = all_temp.sort_values("timestamp").reset_index(drop=True)

print(f"\nTotal shape: {all_temp.shape}")
all_temp.to_csv("ercot_all_temp.csv", index=False)
print("Saved to ercot_all_temp.csv")