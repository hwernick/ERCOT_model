# ERCOT model

ML tool I made to predict price spikes in the Texas power grid and generates buy/sell signals for battery storage operators.

## What it does

- Pulls real-time settlement point prices from ERCOT for four Texas hubs
- Trains two models: one to forecast prices 1 hour ahead, one to predict price spikes
- Generates buy signals when prices are expected to be low (good time to charge a battery)
- Generates sell signals when a price spike is likely (good time to discharge)
- Displays everything in an interactive dashboard with a simulated P&L curve

Battery storage operators make money by charging when electricity is cheap and discharging when it's expensive. This tool tries to predict those moments in advance using historical grid data.

## How to run it

Install dependencies:
```bash
pip install lightgbm pandas numpy scikit-learn shap plotly streamlit requests gridstatus openpyxl
```

Fetch data and train models:
```bash
python fetch_data.py
python fetch_grid_data.py
python features.py
python train_model.py
```

Launch the dashboard:
```bash
streamlit run dashboard.py
```

## Data sources

- ERCOT real-time settlement point prices (public, no login required)
- ERCOT hourly system load (public, downloaded from ercot.com)

## Current model performance

- Price forecast: ~$19 mean absolute error on 1-hour ahead predictions
- Spike classifier: 78% recall on top 5% price events
