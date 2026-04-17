def generate_explanation(row, predicted_price, confidence, stock_score):
    signal = row["Signal"]
    close_price = row["Close"]
    sma_3 = row.get("SMA_3", None)
    sma_5 = row.get("SMA_5", None)
    rsi = row.get("RSI", 50)

    sma_part = ""
    if sma_3 is not None and sma_5 is not None:
        try:
            sma_part = f"SMA 3 is {float(sma_3):.2f} and SMA 5 is {float(sma_5):.2f}. "
        except Exception:
            sma_part = ""

    if signal == "Buy":
        return (
            f"The stock looks relatively strong. Current price is {close_price:.2f}. "
            f"{sma_part}RSI is {float(rsi):.2f}. "
            f"The predicted next close is {predicted_price:.2f}, with {confidence}% confidence "
            f"and a stock score of {stock_score}/100."
        )

    if signal == "Sell":
        return (
            f"The stock looks relatively weak. Current price is {close_price:.2f}. "
            f"{sma_part}RSI is {float(rsi):.2f}. "
            f"The predicted next close is {predicted_price:.2f}, with {confidence}% confidence "
            f"and a stock score of {stock_score}/100."
        )

    return (
        f"The stock is currently neutral. Current price is {close_price:.2f}. "
        f"{sma_part}RSI is {float(rsi):.2f}. "
        f"The predicted next close is {predicted_price:.2f}, with {confidence}% confidence "
        f"and a stock score of {stock_score}/100."
    )


def ask_ai_about_stock(question, row, predicted_price, confidence, stock_score, model_used):
    q = question.lower().strip()

    symbol = row.get("Symbol", "this stock")
    signal = row.get("Signal", "Hold")
    rsi = float(row.get("RSI", 50))
    close_price = float(row.get("Close", 0))
    change = float(row.get("Change", 0)) if row.get("Change", 0) is not None else 0.0
    pct_change = float(row.get("Percent_Change", 0)) if row.get("Percent_Change", 0) is not None else 0.0

    if "should i buy" in q or "buy" in q:
        if signal == "Buy":
            return (
                f"{symbol} currently looks like a BUY candidate. "
                f"Confidence is {confidence}%, predicted next close is {predicted_price:.2f}, "
                f"and stock score is {stock_score}/100."
            )
        elif signal == "Hold":
            return (
                f"{symbol} is currently more of a HOLD than a buy. "
                f"The signal is not strong enough yet. Confidence is {confidence}%."
            )
        else:
            return (
                f"{symbol} does not currently look like a buy based on the dashboard. "
                f"Current signal is SELL with {confidence}% confidence."
            )

    if "should i sell" in q or "sell" in q:
        if signal == "Sell":
            return (
                f"{symbol} currently leans toward SELL. "
                f"Confidence is {confidence}% and the stock score is {stock_score}/100."
            )
        elif signal == "Hold":
            return (
                f"{symbol} is currently in HOLD territory, not a strong sell setup."
            )
        else:
            return (
                f"{symbol} is not currently showing a sell setup. "
                f"The dashboard leans BUY with {confidence}% confidence."
            )

    if "hold" in q:
        return (
            f"{symbol} is currently rated {signal.upper()}. "
            f"The dashboard confidence is {confidence}% and the stock score is {stock_score}/100."
        )

    if "why" in q:
        return (
            f"{symbol} is rated {signal.upper()} because the dashboard combines latest price action, "
            f"RSI, recent momentum, and prediction logic. Current price is {close_price:.2f}, "
            f"change is {change:+.2f}, percent change is {pct_change:+.2f}%, "
            f"predicted next close is {predicted_price:.2f}, and the active model is {model_used}."
        )

    if "rsi" in q:
        return (
            f"{symbol} has an RSI of {rsi:.2f}. "
            f"Above 70 often suggests overbought conditions, and below 30 often suggests oversold conditions."
        )

    if "prediction" in q or "predicted" in q or "next close" in q:
        return (
            f"The predicted next closing price for {symbol} is {predicted_price:.2f}."
        )

    if "model" in q:
        return f"The model currently used for {symbol} is {model_used}."

    if "score" in q or "rank" in q:
        return (
            f"{symbol} currently has a stock score of {stock_score}/100. "
            f"Higher scores indicate stronger overall setups in this dashboard."
        )

    if "change" in q or "today" in q or "movement" in q:
        return (
            f"{symbol} is currently at {close_price:.2f} with a latest change of {change:+.2f} "
            f"and percent change of {pct_change:+.2f}%."
        )

    return (
        f"For {symbol}, you can ask things like: "
        f"'Should I buy this stock?', 'Should I sell?', 'Why is it {signal.lower()}?', "
        f"'What is the prediction?', 'What is the RSI?', or 'What model is used?'"
    )