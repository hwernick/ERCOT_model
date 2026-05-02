import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pickle
import shap

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ERCOT Signal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0a0a0f;
        color: #e0e0e0;
    }
    .main { background-color: #0a0a0f; }
    .stApp { background-color: #0a0a0f; }

    h1, h2, h3 {
        font-family: 'Space Mono', monospace;
        color: #00ff88;
    }

    .metric-card {
        background: #12121a;
        border: 1px solid #1e1e2e;
        border-left: 3px solid #00ff88;
        padding: 16px 20px;
        border-radius: 4px;
        margin-bottom: 12px;
    }

    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 28px;
        font-weight: 700;
        color: #00ff88;
    }

    .metric-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #666;
        margin-top: 4px;
    }

    .signal-buy {
        color: #00ff88;
        font-family: 'Space Mono', monospace;
        font-weight: 700;
    }

    .signal-sell {
        color: #ff4466;
        font-family: 'Space Mono', monospace;
        font-weight: 700;
    }

    .sidebar .sidebar-content {
        background-color: #0d0d14;
    }

    div[data-testid="stSidebar"] {
        background-color: #0d0d14;
        border-right: 1px solid #1e1e2e;
    }
</style>
""", unsafe_allow_html=True)


# --- LOAD DATA AND MODELS ---
@st.cache_data
def load_data():
    df = pd.read_csv("ercot_2024_features.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_resource
def load_models():
    with open("price_model.pkl", "rb") as f:
        price_model = pickle.load(f)
    with open("spike_model.pkl", "rb") as f:
        spike_model = pickle.load(f)
    return price_model, spike_model


df = load_data()
price_model, spike_model = load_models()

FEATURES = [
    "hour", "day_of_week", "month", "is_weekend",
    "hour_sin", "hour_cos",
    "price_lag_1h", "price_lag_4h", "price_lag_24h",
    "price_roll_mean_4h", "price_roll_mean_24h", "price_roll_std_4h",
    "load_mw", "load_lag_1h", "load_roll_mean_4h"
]

# --- GENERATE SIGNALS ---
X = df[FEATURES]
df["price_forecast"] = price_model.predict(X)
df["spike_prob"] = spike_model.predict_proba(X)[:, 1]

# Signal logic
df["signal"] = "hold"
df.loc[df["spike_prob"] > 0.5, "signal"] = "sell"
df.loc[df["spike_prob"] < 0.1, "signal"] = "buy"

# --- SIDEBAR ---
st.sidebar.markdown("## ⚡ ERCOT SIGNAL")
st.sidebar.markdown("---")

hub = st.sidebar.selectbox("Hub", ["HB_HOUSTON"])
days = st.sidebar.slider("Days to display", 7, 90, 30)
spike_threshold = st.sidebar.slider("Sell signal threshold", 0.3, 0.9, 0.5)

# Update signals based on threshold
df["signal"] = "hold"
df.loc[df["spike_prob"] > spike_threshold, "signal"] = "sell"
df.loc[df["spike_prob"] < 0.1, "signal"] = "buy"

st.sidebar.markdown("---")
st.sidebar.markdown("**Signal Logic**")
st.sidebar.markdown("🟢 **BUY** — spike prob < 10%")
st.sidebar.markdown(f"🔴 **SELL** — spike prob > {int(spike_threshold * 100)}%")
st.sidebar.markdown("⬜ **HOLD** — between thresholds")

# --- FILTER TO SELECTED WINDOW ---
latest = df["timestamp"].max()
cutoff = latest - pd.Timedelta(days=days)
view = df[df["timestamp"] >= cutoff].copy()

# --- HEADER ---
st.markdown("# ⚡ ERCOT SIGNAL")
st.markdown("*Real-time settlement point price signals for ERCOT trading hubs*")
st.markdown("---")

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    current_price = view["price"].iloc[-1]
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">${current_price:.2f}</div>
        <div class="metric-label">Current Price ($/MWh)</div>
    </div>""", unsafe_allow_html=True)

with col2:
    current_spike_prob = view["spike_prob"].iloc[-1]
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{current_spike_prob:.0%}</div>
        <div class="metric-label">Spike Probability</div>
    </div>""", unsafe_allow_html=True)

with col3:
    current_signal = view["signal"].iloc[-1].upper()
    color = "#00ff88" if current_signal == "BUY" else "#ff4466" if current_signal == "SELL" else "#888"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{color}">{current_signal}</div>
        <div class="metric-label">Current Signal</div>
    </div>""", unsafe_allow_html=True)

with col4:
    current_load = view["load_mw"].iloc[-1]
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{current_load / 1000:.1f} GW</div>
        <div class="metric-label">System Load</div>
    </div>""", unsafe_allow_html=True)

# --- PANEL 1: PRICE CHART WITH SIGNALS ---
st.markdown("### Price History + Signals")

buy_signals = view[view["signal"] == "buy"]
sell_signals = view[view["signal"] == "sell"]

fig = go.Figure()

# Price line
fig.add_trace(go.Scatter(
    x=view["timestamp"], y=view["price"],
    mode="lines", name="Price",
    line=dict(color="#444466", width=1),
))

# Buy signals
fig.add_trace(go.Scatter(
    x=buy_signals["timestamp"], y=buy_signals["price"],
    mode="markers", name="Buy",
    marker=dict(color="#00ff88", size=6, symbol="triangle-up")
))

# Sell signals
fig.add_trace(go.Scatter(
    x=sell_signals["timestamp"], y=sell_signals["price"],
    mode="markers", name="Sell",
    marker=dict(color="#ff4466", size=6, symbol="triangle-down")
))

fig.update_layout(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0a0a0f",
    font=dict(color="#888", family="Space Mono"),
    xaxis=dict(gridcolor="#1a1a2e", showgrid=True),
    yaxis=dict(gridcolor="#1a1a2e", showgrid=True, title="$/MWh"),
    legend=dict(bgcolor="#12121a", bordercolor="#1e1e2e"),
    height=400,
    margin=dict(l=0, r=0, t=20, b=0)
)

st.plotly_chart(fig, use_container_width=True)

# --- PANEL 2: P&L CURVE ---
st.markdown("### Simulated P&L")
st.caption("Assumes 1 MWh battery: charges on BUY signal, discharges on SELL signal")

pnl = view.copy()
pnl["pnl"] = 0.0
position = None
buy_price = 0

for i, row in pnl.iterrows():
    if row["signal"] == "buy" and position is None:
        position = "long"
        buy_price = row["price"]
    elif row["signal"] == "sell" and position == "long":
        pnl.at[i, "pnl"] = row["price"] - buy_price
        position = None
        buy_price = 0

pnl["cumulative_pnl"] = pnl["pnl"].cumsum()

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=pnl["timestamp"], y=pnl["cumulative_pnl"],
    mode="lines", name="Cumulative P&L",
    line=dict(color="#00ff88", width=2),
    fill="tozeroy",
    fillcolor="rgba(0,255,136,0.05)"
))

fig2.update_layout(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0a0a0f",
    font=dict(color="#888", family="Space Mono"),
    xaxis=dict(gridcolor="#1a1a2e"),
    yaxis=dict(gridcolor="#1a1a2e", title="$/MWh profit"),
    height=300,
    margin=dict(l=0, r=0, t=20, b=0)
)

st.plotly_chart(fig2, use_container_width=True)

total_pnl = pnl["cumulative_pnl"].iloc[-1]
n_trades = (pnl["pnl"] != 0).sum()
st.markdown(f"**{n_trades} completed trades** · **Total P&L: ${total_pnl:.2f}/MWh**")

# --- PANEL 3: SPIKE PROBABILITY ---
st.markdown("### Spike Probability (Last 7 Days)")

recent = df[df["timestamp"] >= latest - pd.Timedelta(days=7)]

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=recent["timestamp"], y=recent["spike_prob"],
    mode="lines", name="Spike Probability",
    line=dict(color="#ff4466", width=1.5),
    fill="tozeroy",
    fillcolor="rgba(255,68,102,0.1)"
))

fig3.add_hline(y=spike_threshold, line_dash="dash",
               line_color="#ff4466", opacity=0.5,
               annotation_text="Sell threshold")

fig3.update_layout(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0a0a0f",
    font=dict(color="#888", family="Space Mono"),
    xaxis=dict(gridcolor="#1a1a2e"),
    yaxis=dict(gridcolor="#1a1a2e", title="Probability", range=[0, 1]),
    height=250,
    margin=dict(l=0, r=0, t=20, b=0)
)

st.plotly_chart(fig3, use_container_width=True)

# --- PANEL 4: SHAP FEATURE IMPORTANCE ---
st.markdown("### Why Did the Model Fire?")
st.caption("Feature importance for the most recent signal")

explainer = shap.TreeExplainer(spike_model)
last_row = X.iloc[[-1]]
shap_values = explainer.shap_values(last_row)

if isinstance(shap_values, list):
    shap_vals = shap_values[1][0]
else:
    shap_vals = shap_values[0]

shap_df = pd.DataFrame({
    "feature": FEATURES,
    "importance": shap_vals
}).sort_values("importance", key=abs, ascending=True)

colors = ["#00ff88" if v > 0 else "#ff4466" for v in shap_df["importance"]]

fig4 = go.Figure(go.Bar(
    x=shap_df["importance"],
    y=shap_df["feature"],
    orientation="h",
    marker_color=colors
))

fig4.update_layout(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0a0a0f",
    font=dict(color="#888", family="Space Mono"),
    xaxis=dict(gridcolor="#1a1a2e", title="SHAP value"),
    yaxis=dict(gridcolor="#1a1a2e"),
    height=400,
    margin=dict(l=0, r=0, t=20, b=0)
)

st.plotly_chart(fig4, use_container_width=True)
st.caption("🟢 Green = pushes toward SELL signal · 🔴 Red = pushes toward BUY signal")