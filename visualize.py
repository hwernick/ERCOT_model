import pandas as pd
import plotly.express as px

# Load the data we saved
df = pd.read_csv("ercot_2024_hub_prices.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

print(df.head())
print(f"\nShape: {df.shape}")

# part 1
houston = df[df["hub"] == "HB_HOUSTON"].copy()

fig = px.line(
    houston,
    x="timestamp",
    y="price",
    title="HB_HOUSTON Real-Time Prices 2024",
    labels={"price": "Price ($/MWh)", "timestamp": "Date"}
)

fig.show()

# part 2
# Filter out spikes to see the underlying pattern
houston_calm = houston[houston["price"] < 200]

fig2 = px.line(
    houston_calm,
    x="timestamp",
    y="price",
    title="HB_HOUSTON Prices 2024 (excluding spikes above $200)",
    labels={"price": "Price ($/MWh)", "timestamp": "Date"}
)

fig2.show()


# part 3
houston["hour"] = houston["timestamp"].dt.hour

hourly_avg = houston.groupby("hour")["price"].mean().reset_index()

fig3 = px.bar(
    hourly_avg,
    x="hour",
    y="price",
    title="Average HB_HOUSTON Price by Hour of Day (2024)",
    labels={"price": "Avg Price ($/MWh)", "hour": "Hour of Day"}
)

fig3.show()