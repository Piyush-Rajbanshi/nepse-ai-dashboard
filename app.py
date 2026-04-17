# import time
# from pathlib import Path

# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import streamlit as st
# import streamlit.components.v1 as components

# from model import (
#     add_indicators,
#     get_signal,
#     predict_next_close,
#     get_rsi_status,
#     calculate_stock_score
# )
# from utils import generate_explanation, ask_ai_about_stock
# from data_loader import get_data, get_latest_market_snapshot, simulate_live_update
# from report_generator import (
#     build_stock_report,
#     build_market_summary_report,
#     build_watchlist_report,
#     convert_df_to_csv
# )
# from watchlist_manager import load_watchlist, save_watchlist
# from alert_engine import generate_stock_alerts, generate_market_alerts

# BASE_DIR = Path(__file__).resolve().parent

# st.set_page_config(page_title="NEPSE AI Agent", layout="wide")


# # -----------------------------
# # Load CSS
# # -----------------------------
# def load_css():
#     css_path = BASE_DIR / "style.css"
#     if css_path.exists():
#         css = css_path.read_text(encoding="utf-8")
#         st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# load_css()

# # -----------------------------
# # Sidebar
# # -----------------------------
# st.sidebar.header("System Controls")

# data_source = st.sidebar.selectbox(
#     "Select Data Source",
#     ["CSV", "SCRAPER", "API"],
#     index=0
# )

# enable_demo_live = st.sidebar.checkbox("Enable demo live movement", value=False)
# auto_refresh = st.sidebar.checkbox("Auto refresh", value=False)
# refresh_seconds = st.sidebar.slider("Refresh every (seconds)", 5, 60, 15)
# refresh_btn = st.sidebar.button("Refresh Now")


# # -----------------------------
# # Loaders
# # -----------------------------
# @st.cache_data(ttl=60)
# def load_market_data(source):
#     return get_data(source)


# @st.cache_data(ttl=300)
# def load_csv_history():
#     return get_data("CSV")


# try:
#     if refresh_btn:
#         st.cache_data.clear()

#     df = load_market_data(data_source)

#     if enable_demo_live and data_source == "CSV":
#         df = simulate_live_update(df)

# except Exception as e:
#     st.error(f"Live data loading failed: {e}")
#     st.stop()


# # -----------------------------
# # Auto refresh
# # -----------------------------
# if auto_refresh:
#     time.sleep(refresh_seconds)
#     st.rerun()

# # -----------------------------
# # Load history for live mode
# # -----------------------------
# history_df = load_csv_history()
# history_df["Date"] = pd.to_datetime(history_df["Date"])


# # -----------------------------
# # Add indicators
# # -----------------------------
# all_frames = []
# for symbol in df["Symbol"].unique():
#     part = df[df["Symbol"] == symbol].copy()
#     part = add_indicators(part)
#     all_frames.append(part)

# df = pd.concat(all_frames, ignore_index=True)

# latest_df = get_latest_market_snapshot(df)


# # -----------------------------
# # Predictions + SIGNAL FIX
# # -----------------------------
# predicted_prices = []
# confidences = []
# models_used = []
# scores = []
# lr_maes = []
# rf_maes = []
# final_signals = []

# for _, row in latest_df.iterrows():
#     symbol = row["Symbol"]

#     # Build model dataset
#     if data_source == "SCRAPER":
#         hist = history_df[history_df["Symbol"] == symbol].copy()
#         live = df[df["Symbol"] == symbol].tail(1).copy()

#         if not hist.empty:
#             model_df = pd.concat([hist, live])
#         else:
#             model_df = live
#     else:
#         model_df = df[df["Symbol"] == symbol]

#     model_df = model_df.sort_values("Date")

#     # Predict
#     pred = predict_next_close(model_df)

#     # SIGNAL FIX (very important)
#     signal = pred["signal_override"] if pred.get("signal_override") else get_signal(row)

#     # Score
#     temp_row = row.copy()
#     temp_row["Signal"] = signal
#     score = calculate_stock_score(temp_row, pred["predicted_price"], pred["confidence"])

#     # Append
#     predicted_prices.append(pred["predicted_price"])
#     confidences.append(pred["confidence"])
#     models_used.append(pred["model_used"])
#     scores.append(score)
#     lr_maes.append(pred["metrics"]["Linear Regression"])
#     rf_maes.append(pred["metrics"]["Random Forest"])
#     final_signals.append(signal)


# # Assign
# latest_df["Predicted_Close"] = predicted_prices
# latest_df["Confidence"] = confidences
# latest_df["Model_Used"] = models_used
# latest_df["Stock_Score"] = scores
# latest_df["LR_MAE"] = lr_maes
# latest_df["RF_MAE"] = rf_maes
# latest_df["Signal"] = final_signals


# # -----------------------------
# # Watchlist
# # -----------------------------
# saved_watchlist = load_watchlist()
# symbols = sorted(df["Symbol"].unique())

# watchlist = st.sidebar.multiselect(
#     "Watchlist",
#     symbols,
#     default=[s for s in saved_watchlist if s in symbols]
# )

# if st.sidebar.button("Save Watchlist"):
#     save_watchlist(watchlist)


# # -----------------------------
# # Header
# # -----------------------------
# st.title("📈 NEPSE AI Agent (Live Integrated)")

# # -----------------------------
# # Market movers
# # -----------------------------
# g1, g2, g3 = st.columns(3)

# with g1:
#     st.subheader("Top Gainers")
#     st.dataframe(
#         latest_df.sort_values("Change", ascending=False).head(5)[
#             ["Symbol", "Close", "Change", "Signal", "Stock_Score"]
#         ],
#         use_container_width=True
#     )

# with g2:
#     st.subheader("Top Losers")
#     st.dataframe(
#         latest_df.sort_values("Change").head(5)[
#             ["Symbol", "Close", "Change", "Signal", "Stock_Score"]
#         ],
#         use_container_width=True
#     )

# with g3:
#     st.subheader("Top Opportunities")
#     st.dataframe(
#         latest_df.sort_values("Stock_Score", ascending=False).head(5)[
#             ["Symbol", "Close", "Signal", "Confidence", "Stock_Score"]
#         ],
#         use_container_width=True
#     )


# # -----------------------------
# # Select stock
# # -----------------------------
# selected_symbol = st.selectbox("Select Stock", symbols)

# if data_source == "SCRAPER":
#     hist = history_df[history_df["Symbol"] == selected_symbol]
#     live = df[df["Symbol"] == selected_symbol].tail(1)

#     stock_df = pd.concat([hist, live]).drop_duplicates(subset=["Date"])
# else:
#     stock_df = df[df["Symbol"] == selected_symbol]

# stock_df = stock_df.sort_values("Date")
# stock_df = add_indicators(stock_df)

# row = latest_df[latest_df["Symbol"] == selected_symbol].iloc[0]


# # -----------------------------
# # Cards
# # -----------------------------
# c1, c2, c3, c4, c5 = st.columns(5)

# c1.metric("Price", f"Rs. {row['Close']:.2f}")
# c2.metric("Prediction", f"Rs. {row['Predicted_Close']:.2f}")
# c3.metric("Signal", row["Signal"])
# c4.metric("Confidence", f"{row['Confidence']}%")
# c5.metric("Score", f"{row['Stock_Score']}/100")


# # -----------------------------
# # Chart
# # -----------------------------
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["Close"], name="Close"))
# fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["SMA_3"], name="SMA 3"))
# fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["SMA_5"], name="SMA 5"))

# st.plotly_chart(fig, use_container_width=True)


# # -----------------------------
# # RSI
# # -----------------------------
# fig_rsi = px.line(stock_df, x="Date", y="RSI", title="RSI")
# st.plotly_chart(fig_rsi, use_container_width=True)


# # -----------------------------
# # Alerts
# # -----------------------------
# st.subheader("Alerts")
# for alert in generate_stock_alerts(row):
#     st.warning(alert)


# # -----------------------------
# # AI Panel
# # -----------------------------
# st.subheader("AI Analyst")

# st.write(generate_explanation(
#     row,
#     row["Predicted_Close"],
#     row["Confidence"],
#     row["Stock_Score"]
# ))

# question = st.text_input("Ask AI")

# if question:
#     st.success(
#         ask_ai_about_stock(
#             question,
#             row,
#             row["Predicted_Close"],
#             row["Confidence"],
#             row["Stock_Score"],
#             row["Model_Used"]
#         )
#     )


# # -----------------------------
# # Export
# # -----------------------------
# st.subheader("Export")

# st.download_button(
#     "Download Market",
#     convert_df_to_csv(build_market_summary_report(latest_df)),
#     "market.csv"
# )




import time
from pathlib import Path

import pandas as pd
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
from data_loader import (
    get_data,
    get_latest_market_snapshot,
    simulate_live_update,
    load_stored_history
)
from report_generator import (
    build_stock_report,
    build_market_summary_report,
    build_watchlist_report,
    convert_df_to_csv
)
from watchlist_manager import load_watchlist, save_watchlist
from alert_engine import generate_stock_alerts, generate_market_alerts
from chart_utils import create_advanced_chart, filter_by_range

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="NEPSE AI Agent", layout="wide")


def load_css():
    css_path = BASE_DIR / "style.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css()

st.sidebar.header("System Controls")

data_source = st.sidebar.selectbox(
    "Select Data Source",
    ["CSV", "SCRAPER", "API"],
    index=1
)

enable_demo_live = st.sidebar.checkbox("Enable demo live movement", value=False)
auto_refresh = st.sidebar.checkbox("Auto refresh", value=False)
refresh_seconds = st.sidebar.slider("Refresh every (seconds)", 5, 60, 15)
refresh_btn = st.sidebar.button("Refresh Now")

@st.cache_data(ttl=60)
def load_market_data(source):
    return get_data(source)

try:
    if refresh_btn:
        st.cache_data.clear()

    df = load_market_data(data_source)

    if enable_demo_live and data_source == "CSV":
        df = simulate_live_update(df)

except Exception as e:
    st.error(f"Live data loading failed: {e}")
    st.stop()

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

stored_history_df = load_stored_history()
if not stored_history_df.empty:
    stored_history_df["Date"] = pd.to_datetime(stored_history_df["Date"])

all_frames = []
for symbol in df["Symbol"].unique():
    part = df[df["Symbol"] == symbol].copy()
    part = add_indicators(part)
    all_frames.append(part)

df = pd.concat(all_frames, ignore_index=True)
latest_df = get_latest_market_snapshot(df)

predicted_prices = []
confidences = []
models_used = []
scores = []
lr_maes = []
rf_maes = []
final_signals = []

for _, row in latest_df.iterrows():
    symbol = row["Symbol"]

    if not stored_history_df.empty:
        hist = stored_history_df[stored_history_df["Symbol"] == symbol].copy()
        live = df[df["Symbol"] == symbol].tail(1).copy()
        model_df = pd.concat([hist, live], ignore_index=True).drop_duplicates(
            subset=["Date", "Symbol"], keep="last"
        )
    else:
        model_df = df[df["Symbol"] == symbol].copy()

    model_df = model_df.sort_values("Date")

    pred = predict_next_close(model_df)
    signal = pred["signal_override"] if pred.get("signal_override") else get_signal(row)

    temp_row = row.copy()
    temp_row["Signal"] = signal
    score = calculate_stock_score(temp_row, pred["predicted_price"], pred["confidence"])

    predicted_prices.append(pred["predicted_price"])
    confidences.append(pred["confidence"])
    models_used.append(pred["model_used"])
    scores.append(score)
    lr_maes.append(pred["metrics"]["Linear Regression"])
    rf_maes.append(pred["metrics"]["Random Forest"])
    final_signals.append(signal)

latest_df["Predicted_Close"] = predicted_prices
latest_df["Confidence"] = confidences
latest_df["Model_Used"] = models_used
latest_df["Stock_Score"] = scores
latest_df["LR_MAE"] = lr_maes
latest_df["RF_MAE"] = rf_maes
latest_df["Signal"] = final_signals

saved_watchlist = load_watchlist()
symbols = sorted(df["Symbol"].unique())

watchlist = st.sidebar.multiselect(
    "Watchlist",
    symbols,
    default=[s for s in saved_watchlist if s in symbols]
)

if st.sidebar.button("Save Watchlist"):
    save_watchlist(watchlist)

st.markdown("""
<div class="panel-box">
    <h1 style="margin-bottom: 0;">📈 NEPSE AI Agent</h1>
    <div class="small-muted">Live Snapshot + Stored History + Advanced Charting</div>
</div>
""", unsafe_allow_html=True)

ticker_parts = []
for _, row in latest_df.sort_values("Symbol").iterrows():
    change = float(row["Change"]) if pd.notna(row["Change"]) else 0.0
    if change > 0:
        color = "#34d399"
        arrow = "▲"
    elif change < 0:
        color = "#f87171"
        arrow = "▼"
    else:
        color = "#fbbf24"
        arrow = "•"

    ticker_parts.append(
        f"""
        <span style="margin-right: 28px;">
            {row['Symbol']} <strong>{float(row['Close']):.2f}</strong>
            <span style="color:{color};">{arrow} {change:+.2f}</span>
        </span>
        """
    )

ticker_html = "".join(ticker_parts)

components.html(
    f"""
    <div style="
        background:#0f2744;
        padding:10px 16px;
        border-radius:10px;
        white-space:nowrap;
        overflow-x:auto;
        font-weight:600;
        color:#dbeafe;
        margin-bottom: 18px;
    ">
        {ticker_html}
    </div>
    """,
    height=60
)

g1, g2, g3 = st.columns(3)
with g1:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("Top Gainers")
    st.dataframe(
        latest_df.sort_values("Change", ascending=False).head(5)[
            ["Symbol", "Close", "Change", "Signal", "Stock_Score"]
        ],
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with g2:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("Top Losers")
    st.dataframe(
        latest_df.sort_values("Change").head(5)[
            ["Symbol", "Close", "Change", "Signal", "Stock_Score"]
        ],
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with g3:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("Top Opportunities")
    st.dataframe(
        latest_df.sort_values("Stock_Score", ascending=False).head(5)[
            ["Symbol", "Close", "Signal", "Confidence", "Stock_Score"]
        ],
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

selected_symbol = st.selectbox("Select Stock", symbols)
time_range = st.radio("Range", ["1D", "1W", "1M", "3M", "ALL"], horizontal=True)

if not stored_history_df.empty:
    stock_df = stored_history_df[stored_history_df["Symbol"] == selected_symbol].copy()
    live_row = df[df["Symbol"] == selected_symbol].tail(1).copy()
    stock_df = pd.concat([stock_df, live_row], ignore_index=True).drop_duplicates(
        subset=["Date", "Symbol"], keep="last"
    )
else:
    stock_df = df[df["Symbol"] == selected_symbol].copy()

stock_df = stock_df.sort_values("Date")
stock_df = filter_by_range(stock_df, time_range)

row = latest_df[latest_df["Symbol"] == selected_symbol].iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Price", f"Rs. {float(row['Close']):.2f}")
c2.metric("Prediction", f"Rs. {float(row['Predicted_Close']):.2f}")
c3.metric("Signal", row["Signal"])
c4.metric("Confidence", f"{float(row['Confidence']):.1f}%")
c5.metric("Score", f"{float(row['Stock_Score']):.1f}/100")

d1, d2, d3, d4 = st.columns(4)
d1.metric("Open", f"Rs. {float(row['Open']):.2f}" if "Open" in row and pd.notna(row["Open"]) else "N/A")
d2.metric("High", f"Rs. {float(row['High']):.2f}" if "High" in row and pd.notna(row["High"]) else "N/A")
d3.metric("Low", f"Rs. {float(row['Low']):.2f}" if "Low" in row and pd.notna(row["Low"]) else "N/A")
d4.metric("Volume", f"{int(row['Volume']):,}" if "Volume" in row and pd.notna(row["Volume"]) else "N/A")

left, right = st.columns([2.25, 1])

with left:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("Advanced Trading Chart")

    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    if required_cols.issubset(stock_df.columns) and not stock_df.empty:
        fig = create_advanced_chart(stock_df, selected_symbol)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Need OHLCV history for advanced charting. Pull more live snapshots over time.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("Market Alerts")
    for alert in generate_market_alerts(latest_df):
        st.info(alert)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("Stock Alerts")
    for alert in generate_stock_alerts(row):
        st.warning(alert)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("AI Analyst")
    st.write(generate_explanation(
        row,
        row["Predicted_Close"],
        row["Confidence"],
        row["Stock_Score"]
    ))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.subheader("Ask AI About This Stock")
    question = st.text_input("Ask something like: Should I buy this stock?")
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
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="panel-box">', unsafe_allow_html=True)
st.subheader("Export Center")

stock_report_df = build_stock_report(
    row,
    row["Predicted_Close"],
    row["Confidence"],
    row["Model_Used"],
    row["Stock_Score"],
    get_rsi_status(float(row["RSI"]))
)
market_report_df = build_market_summary_report(latest_df)
watchlist_report_df = build_watchlist_report(latest_df, watchlist)

e1, e2, e3 = st.columns(3)
with e1:
    st.download_button(
        label="Download Stock Report",
        data=convert_df_to_csv(stock_report_df),
        file_name=f"{selected_symbol.lower()}_stock_report.csv",
        mime="text/csv"
    )
with e2:
    st.download_button(
        label="Download Market Summary",
        data=convert_df_to_csv(market_report_df),
        file_name="market_summary_report.csv",
        mime="text/csv"
    )
with e3:
    st.download_button(
        label="Download Watchlist Report",
        data=convert_df_to_csv(watchlist_report_df),
        file_name="watchlist_report.csv",
        mime="text/csv"
    )
st.markdown('</div>', unsafe_allow_html=True)

st.warning("⚠️ This dashboard is for educational purposes only and not financial advice.")