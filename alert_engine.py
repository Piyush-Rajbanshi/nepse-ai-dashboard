import pandas as pd


def generate_stock_alerts(row: pd.Series) -> list[str]:
    alerts = []

    signal = row.get("Signal", "Hold")
    confidence = float(row.get("Confidence", 0))
    rsi = float(row.get("RSI", 50))
    change = float(row.get("Change", 0))
    score = float(row.get("Stock_Score", 0))

    if signal == "Buy" and confidence >= 70:
        alerts.append(f"Strong BUY signal with {confidence:.1f}% confidence.")

    if signal == "Sell" and confidence >= 70:
        alerts.append(f"Strong SELL signal with {confidence:.1f}% confidence.")

    if rsi >= 70:
        alerts.append(f"RSI is {rsi:.2f} — stock may be overbought.")

    if rsi <= 30:
        alerts.append(f"RSI is {rsi:.2f} — stock may be oversold.")

    if abs(change) >= 10:
        alerts.append(f"Large latest price move detected: {change:+.2f}")

    if score >= 75:
        alerts.append(f"High stock score: {score:.1f}/100")

    if not alerts:
        alerts.append("No major alert triggered for this stock.")

    return alerts


def generate_market_alerts(latest_df: pd.DataFrame) -> list[str]:
    alerts = []

    if latest_df.empty:
        return ["No market data available."]

    advancing = int((latest_df["Change"] > 0).sum())
    declining = int((latest_df["Change"] < 0).sum())

    if advancing > declining * 1.5:
        alerts.append("Market breadth is strongly positive.")
    elif declining > advancing * 1.5:
        alerts.append("Market breadth is strongly negative.")
    else:
        alerts.append("Market breadth is relatively balanced.")

    strong_buy_count = int(((latest_df["Signal"] == "Buy") & (latest_df["Confidence"] >= 70)).sum())
    strong_sell_count = int(((latest_df["Signal"] == "Sell") & (latest_df["Confidence"] >= 70)).sum())

    alerts.append(f"Strong buy setups: {strong_buy_count}")
    alerts.append(f"Strong sell setups: {strong_sell_count}")

    top_score = latest_df["Stock_Score"].max() if "Stock_Score" in latest_df.columns else None
    if top_score is not None:
        alerts.append(f"Highest stock score in market view: {top_score:.1f}/100")

    return alerts