import pandas as pd


def build_stock_report(selected_row, predicted_close, confidence, model_used, stock_score, rsi_status):
    current_price = float(selected_row["Close"])
    price_gap = predicted_close - current_price
    price_gap_pct = (price_gap / current_price) * 100 if current_price != 0 else 0

    rows = [
        {"Metric": "Symbol", "Value": selected_row["Symbol"]},
        {"Metric": "Current Price", "Value": round(current_price, 2)},
        {"Metric": "Predicted Next Close", "Value": round(predicted_close, 2)},
        {"Metric": "Expected Change", "Value": round(price_gap, 2)},
        {"Metric": "Expected Change %", "Value": round(price_gap_pct, 2)},
        {"Metric": "Signal", "Value": selected_row["Signal"]},
        {"Metric": "Confidence %", "Value": confidence},
        {"Metric": "RSI", "Value": round(float(selected_row["RSI"]), 2)},
        {"Metric": "RSI Status", "Value": rsi_status},
        {"Metric": "Model Used", "Value": model_used},
        {"Metric": "Stock Score", "Value": stock_score},
    ]

    return pd.DataFrame(rows)


def build_market_summary_report(latest_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Symbol", "Close", "Change", "Signal", "Confidence",
        "Predicted_Close", "Stock_Score", "Model_Used", "RSI"
    ]
    available_cols = [c for c in cols if c in latest_df.columns]

    report_df = latest_df[available_cols].copy()
    if "Stock_Score" in report_df.columns:
        report_df = report_df.sort_values("Stock_Score", ascending=False)

    return report_df.reset_index(drop=True)


def build_watchlist_report(latest_df: pd.DataFrame, watchlist: list[str]) -> pd.DataFrame:
    if not watchlist:
        return pd.DataFrame(columns=["Symbol", "Close", "Signal", "Confidence", "Stock_Score"])

    watchlist_df = latest_df[latest_df["Symbol"].isin(watchlist)].copy()

    cols = ["Symbol", "Close", "Signal", "Confidence", "Stock_Score", "Model_Used", "RSI"]
    available_cols = [c for c in cols if c in watchlist_df.columns]

    if "Stock_Score" in watchlist_df.columns:
        watchlist_df = watchlist_df.sort_values("Stock_Score", ascending=False)

    return watchlist_df[available_cols].reset_index(drop=True)


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")