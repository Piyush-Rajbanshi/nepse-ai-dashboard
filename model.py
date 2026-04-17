import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error


def compute_rsi(series, period=5):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def add_indicators(stock_df: pd.DataFrame) -> pd.DataFrame:
    stock_df = stock_df.copy().sort_values("Date")

    stock_df["SMA_3"] = stock_df["Close"].rolling(3).mean()
    stock_df["SMA_5"] = stock_df["Close"].rolling(5).mean()
    stock_df["RSI"] = compute_rsi(stock_df["Close"], period=5)
    stock_df["Daily_Return"] = stock_df["Close"].pct_change()
    stock_df["Price_Change"] = stock_df["Close"].diff()

    if "Volume" not in stock_df.columns:
        stock_df["Volume"] = 0

    return stock_df


def get_signal(row: pd.Series) -> str:
    close_price = row.get("Close", np.nan)
    sma_3 = row.get("SMA_3", np.nan)
    sma_5 = row.get("SMA_5", np.nan)
    rsi = row.get("RSI", 50)

    if pd.notna(sma_3) and pd.notna(sma_5):
        if close_price > sma_3 > sma_5 and rsi < 70:
            return "Buy"
        elif close_price < sma_3 < sma_5 and rsi > 30:
            return "Sell"

    # Fallback live snapshot logic
    change = float(row.get("Change", 0) if pd.notna(row.get("Change", 0)) else 0)
    pct_change = float(row.get("Percent_Change", 0) if pd.notna(row.get("Percent_Change", 0)) else 0)

    if pct_change >= 2 or change > 0:
        return "Buy"
    elif pct_change <= -2 or change < 0:
        return "Sell"
    return "Hold"


def get_rsi_status(rsi: float) -> str:
    if rsi >= 70:
        return "Overbought"
    if rsi <= 30:
        return "Oversold"
    return "Neutral"


def prepare_training_data(stock_df: pd.DataFrame):
    df = add_indicators(stock_df).copy()

    feature_cols = ["SMA_3", "SMA_5", "RSI", "Daily_Return", "Price_Change", "Volume"]
    df["Target"] = df["Close"].shift(-1)
    df = df.dropna().copy()

    if len(df) < 8:
        return None, None, None, None, None

    X = df[feature_cols]
    y = df["Target"]

    scaler = MinMaxScaler()
    scaler.fit(X)

    return df, X, y, scaler, feature_cols


def _train_test_split_timeseries(X, y, test_ratio=0.3):
    split_idx = max(1, int(len(X) * (1 - test_ratio)))
    X_train = X[:split_idx]
    X_test = X[split_idx:]
    y_train = y[:split_idx]
    y_test = y[split_idx:]
    return X_train, X_test, y_train, y_test


def compare_models(stock_df: pd.DataFrame):
    prepared = prepare_training_data(stock_df)

    if prepared[0] is None:
        return {
            "best_model_name": "Fallback",
            "best_model": None,
            "scaler": None,
            "feature_cols": None,
            "processed_df": add_indicators(stock_df),
            "metrics": {
                "Linear Regression": None,
                "Random Forest": None
            }
        }

    df, X, y, scaler, feature_cols = prepared
    X_scaled = scaler.transform(X)

    X_train, X_test, y_train, y_test = _train_test_split_timeseries(X_scaled, y.values)

    if len(X_test) == 0:
        X_train, X_test = X_scaled[:-1], X_scaled[-1:]
        y_train, y_test = y.values[:-1], y.values[-1:]

    lr_model = LinearRegression()
    rf_model = RandomForestRegressor(n_estimators=150, max_depth=6, random_state=42)

    lr_model.fit(X_train, y_train)
    rf_model.fit(X_train, y_train)

    lr_pred = lr_model.predict(X_test)
    rf_pred = rf_model.predict(X_test)

    lr_mae = mean_absolute_error(y_test, lr_pred)
    rf_mae = mean_absolute_error(y_test, rf_pred)

    if rf_mae <= lr_mae:
        best_model_name = "Random Forest"
        best_model = rf_model
    else:
        best_model_name = "Linear Regression"
        best_model = lr_model

    return {
        "best_model_name": best_model_name,
        "best_model": best_model,
        "scaler": scaler,
        "feature_cols": feature_cols,
        "processed_df": df,
        "metrics": {
            "Linear Regression": round(float(lr_mae), 4),
            "Random Forest": round(float(rf_mae), 4)
        }
    }


def fallback_live_prediction(stock_df: pd.DataFrame):
    """
    Used when there is not enough historical data for ML.
    Generates a practical live-market estimate instead of flat 50% Hold.
    """
    df = add_indicators(stock_df).copy()
    latest = df.iloc[-1]

    current_price = float(latest["Close"])
    open_price = float(latest["Open"]) if "Open" in df.columns and pd.notna(latest.get("Open")) else current_price
    high_price = float(latest["High"]) if "High" in df.columns and pd.notna(latest.get("High")) else current_price
    low_price = float(latest["Low"]) if "Low" in df.columns and pd.notna(latest.get("Low")) else current_price
    prev_close = float(latest["Prev_Close"]) if "Prev_Close" in df.columns and pd.notna(latest.get("Prev_Close")) else current_price
    change = float(latest["Change"]) if "Change" in df.columns and pd.notna(latest.get("Change")) else current_price - prev_close
    pct_change = float(latest["Percent_Change"]) if "Percent_Change" in df.columns and pd.notna(latest.get("Percent_Change")) else 0.0
    rsi = float(latest["RSI"]) if pd.notna(latest.get("RSI")) else 50.0

    intraday_strength = 0.0
    if high_price > low_price:
        intraday_strength = (current_price - low_price) / (high_price - low_price)

    predicted_price = current_price

    if pct_change > 0:
        predicted_price = current_price * (1 + min(0.015, pct_change / 1000))
    elif pct_change < 0:
        predicted_price = current_price * (1 - min(0.015, abs(pct_change) / 1000))

    if current_price > open_price:
        predicted_price += abs(current_price - open_price) * 0.10
    elif current_price < open_price:
        predicted_price -= abs(current_price - open_price) * 0.10

    signal_score = 0

    if pct_change > 1:
        signal_score += 2
    elif pct_change > 0:
        signal_score += 1
    elif pct_change < -1:
        signal_score -= 2
    elif pct_change < 0:
        signal_score -= 1

    if current_price > open_price:
        signal_score += 1
    elif current_price < open_price:
        signal_score -= 1

    if intraday_strength >= 0.7:
        signal_score += 1
    elif intraday_strength <= 0.3:
        signal_score -= 1

    if rsi >= 65:
        signal_score -= 1
    elif rsi <= 35:
        signal_score += 1

    if signal_score >= 2:
        signal = "Buy"
        confidence = min(88.0, 58 + abs(pct_change) * 6 + intraday_strength * 10)
    elif signal_score <= -2:
        signal = "Sell"
        confidence = min(88.0, 58 + abs(pct_change) * 6 + (1 - intraday_strength) * 10)
    else:
        signal = "Hold"
        confidence = min(72.0, 52 + abs(pct_change) * 3)

    return {
        "predicted_price": round(float(predicted_price), 2),
        "confidence": round(float(confidence), 1),
        "model_used": "Live Rule Engine",
        "processed_df": df,
        "metrics": {
            "Linear Regression": None,
            "Random Forest": None
        },
        "signal_override": signal
    }


def predict_next_close(stock_df: pd.DataFrame):
    comparison = compare_models(stock_df)

    if comparison["best_model"] is None:
        return fallback_live_prediction(stock_df)

    model = comparison["best_model"]
    scaler = comparison["scaler"]
    processed_df = comparison["processed_df"]
    feature_cols = comparison["feature_cols"]

    latest_features = processed_df[feature_cols].iloc[-1:]
    latest_scaled = scaler.transform(latest_features)

    predicted_price = float(model.predict(latest_scaled)[0])
    current_price = float(processed_df["Close"].iloc[-1])
    rsi = float(processed_df["RSI"].iloc[-1])

    upside_pct = ((predicted_price - current_price) / current_price) * 100
    latest_signal = get_signal(processed_df.iloc[-1])

    if latest_signal == "Buy":
        confidence = 60 + min(25, abs(upside_pct) * 4) + max(0, (65 - rsi) * 0.25)
    elif latest_signal == "Sell":
        confidence = 60 + min(25, abs(upside_pct) * 4) + max(0, (rsi - 35) * 0.25)
    else:
        confidence = 50 + min(20, abs(upside_pct) * 2)

    confidence = max(50, min(95, round(confidence, 1)))

    return {
        "predicted_price": round(predicted_price, 2),
        "confidence": confidence,
        "model_used": comparison["best_model_name"],
        "processed_df": processed_df,
        "metrics": comparison["metrics"],
        "signal_override": None
    }


def calculate_stock_score(latest_row: pd.Series, predicted_price: float, confidence: float) -> float:
    current_price = float(latest_row["Close"])
    rsi = float(latest_row.get("RSI", 50))
    signal = latest_row["Signal"]

    upside_pct = ((predicted_price - current_price) / current_price) * 100 if current_price != 0 else 0

    score = 50.0

    if signal == "Buy":
        score += 20
    elif signal == "Sell":
        score -= 15

    score += min(15, upside_pct * 2)

    if 40 <= rsi <= 65:
        score += 10
    elif rsi > 75:
        score -= 8
    elif rsi < 25:
        score += 4

    score += (confidence - 50) * 0.4

    return round(max(0, min(100, score)), 1)