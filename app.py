import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from model import (
    add_indicators,
    get_signal,
    predict_next_close,
    get_rsi_status,
    calculate_stock_score
)
from utils import generate_explanation, ask_ai_about_stock
from data_loader import get_data, get_latest_market_snapshot, simulate_live_update
from report_generator import (
    build_stock_report,
    build_market_summary_report,
    build_watchlist_report,
    convert_df_to_csv
)
from watchlist_manager import load_watchlist, save_watchlist
from alert_engine import generate_stock_alerts, generate_market_alerts

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="NEPSE AI Agent", layout="wide")


# -----------------------------
# Load CSS
# -----------------------------
def load_css():
    css_path = BASE_DIR / "style.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("System Controls")

data_source = st.sidebar.selectbox(
    "Select Data Source",
    ["CSV", "SCRAPER", "API"],
    index=0
)

enable_demo_live = st.sidebar.checkbox("Enable demo live movement", value=False)
auto_refresh = st.sidebar.checkbox("Auto refresh", value=False)
refresh_seconds = st.sidebar.slider("Refresh every (seconds)", 5, 60, 15)
refresh_btn = st.sidebar.button("Refresh Now")


# -----------------------------
# Loaders
# -----------------------------
@st.cache_data(ttl=60)
def load_market_data(source):
    return get_data(source)


@st.cache_data(ttl=300)
def load_csv_history():
    return get_data("CSV")


try:
    if refresh_btn:
        st.cache_data.clear()

    df = load_market_data(data_source)

    if enable_demo_live and data_source == "CSV":
        df = simulate_live_update(df)

except Exception as e:
    st.error(f"Live data loading failed: {e}")
    st.stop()


# -----------------------------
# Auto refresh
# -----------------------------
if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

# -----------------------------
# Load history for live mode
# -----------------------------
history_df = load_csv_history()
history_df["Date"] = pd.to_datetime(history_df["Date"])


# -----------------------------
# Add indicators
# -----------------------------
all_frames = []
for symbol in df["Symbol"].unique():
    part = df[df["Symbol"] == symbol].copy()
    part = add_indicators(part)
    all_frames.append(part)

df = pd.concat(all_frames, ignore_index=True)

latest_df = get_latest_market_snapshot(df)


# -----------------------------
# Predictions + SIGNAL FIX
# -----------------------------
predicted_prices = []
confidences = []
models_used = []
scores = []
lr_maes = []
rf_maes = []
final_signals = []

for _, row in latest_df.iterrows():
    symbol = row["Symbol"]

    # Build model dataset
    if data_source == "SCRAPER":
        hist = history_df[history_df["Symbol"] == symbol].copy()
        live = df[df["Symbol"] == symbol].tail(1).copy()

        if not hist.empty:
            model_df = pd.concat([hist, live])
        else:
            model_df = live
    else:
        model_df = df[df["Symbol"] == symbol]

    model_df = model_df.sort_values("Date")

    # Predict
    pred = predict_next_close(model_df)

    # SIGNAL FIX (very important)
    signal = pred["signal_override"] if pred.get("signal_override") else get_signal(row)

    # Score
    temp_row = row.copy()
    temp_row["Signal"] = signal
    score = calculate_stock_score(temp_row, pred["predicted_price"], pred["confidence"])

    # Append
    predicted_prices.append(pred["predicted_price"])
    confidences.append(pred["confidence"])
    models_used.append(pred["model_used"])
    scores.append(score)
    lr_maes.append(pred["metrics"]["Linear Regression"])
    rf_maes.append(pred["metrics"]["Random Forest"])
    final_signals.append(signal)


# Assign
latest_df["Predicted_Close"] = predicted_prices
latest_df["Confidence"] = confidences
latest_df["Model_Used"] = models_used
latest_df["Stock_Score"] = scores
latest_df["LR_MAE"] = lr_maes
latest_df["RF_MAE"] = rf_maes
latest_df["Signal"] = final_signals


# -----------------------------
# Watchlist
# -----------------------------
saved_watchlist = load_watchlist()
symbols = sorted(df["Symbol"].unique())

watchlist = st.sidebar.multiselect(
    "Watchlist",
    symbols,
    default=[s for s in saved_watchlist if s in symbols]
)

if st.sidebar.button("Save Watchlist"):
    save_watchlist(watchlist)


# -----------------------------
# Header
# -----------------------------
st.title("📈 NEPSE AI Agent (Live Integrated)")

# -----------------------------
# Market movers
# -----------------------------
g1, g2, g3 = st.columns(3)

with g1:
    st.subheader("Top Gainers")
    st.dataframe(
        latest_df.sort_values("Change", ascending=False).head(5)[
            ["Symbol", "Close", "Change", "Signal", "Stock_Score"]
        ],
        use_container_width=True
    )

with g2:
    st.subheader("Top Losers")
    st.dataframe(
        latest_df.sort_values("Change").head(5)[
            ["Symbol", "Close", "Change", "Signal", "Stock_Score"]
        ],
        use_container_width=True
    )

with g3:
    st.subheader("Top Opportunities")
    st.dataframe(
        latest_df.sort_values("Stock_Score", ascending=False).head(5)[
            ["Symbol", "Close", "Signal", "Confidence", "Stock_Score"]
        ],
        use_container_width=True
    )


# -----------------------------
# Select stock
# -----------------------------
selected_symbol = st.selectbox("Select Stock", symbols)

if data_source == "SCRAPER":
    hist = history_df[history_df["Symbol"] == selected_symbol]
    live = df[df["Symbol"] == selected_symbol].tail(1)

    stock_df = pd.concat([hist, live]).drop_duplicates(subset=["Date"])
else:
    stock_df = df[df["Symbol"] == selected_symbol]

stock_df = stock_df.sort_values("Date")
stock_df = add_indicators(stock_df)

row = latest_df[latest_df["Symbol"] == selected_symbol].iloc[0]


# -----------------------------
# Cards
# -----------------------------
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Price", f"Rs. {row['Close']:.2f}")
c2.metric("Prediction", f"Rs. {row['Predicted_Close']:.2f}")
c3.metric("Signal", row["Signal"])
c4.metric("Confidence", f"{row['Confidence']}%")
c5.metric("Score", f"{row['Stock_Score']}/100")


# -----------------------------
# Chart
# -----------------------------
fig = go.Figure()
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["Close"], name="Close"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["SMA_3"], name="SMA 3"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["SMA_5"], name="SMA 5"))

st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# RSI
# -----------------------------
fig_rsi = px.line(stock_df, x="Date", y="RSI", title="RSI")
st.plotly_chart(fig_rsi, use_container_width=True)


# -----------------------------
# Alerts
# -----------------------------
st.subheader("Alerts")
for alert in generate_stock_alerts(row):
    st.warning(alert)


# -----------------------------
# AI Panel
# -----------------------------
st.subheader("AI Analyst")

st.write(generate_explanation(
    row,
    row["Predicted_Close"],
    row["Confidence"],
    row["Stock_Score"]
))

question = st.text_input("Ask AI")

if question:
    st.success(
        ask_ai_about_stock(
            question,
            row,
            row["Predicted_Close"],
            row["Confidence"],
            row["Stock_Score"],
            row["Model_Used"]
        )
    )


# -----------------------------
# Export
# -----------------------------
st.subheader("Export")

st.download_button(
    "Download Market",
    convert_df_to_csv(build_market_summary_report(latest_df)),
    "market.csv"
)