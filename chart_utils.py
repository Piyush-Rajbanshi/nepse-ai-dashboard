import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def add_chart_indicators(stock_df: pd.DataFrame) -> pd.DataFrame:
    df = stock_df.copy().sort_values("Date")

    # SMA
    df["SMA_3"] = df["Close"].rolling(3).mean()
    df["SMA_5"] = df["Close"].rolling(5).mean()

    # Bollinger Bands
    df["BB_MA20"] = df["Close"].rolling(20).mean()
    df["BB_STD20"] = df["Close"].rolling(20).std()
    df["BB_UPPER"] = df["BB_MA20"] + 2 * df["BB_STD20"]
    df["BB_LOWER"] = df["BB_MA20"] - 2 * df["BB_STD20"]

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

    return df


def filter_by_range(stock_df: pd.DataFrame, range_label: str) -> pd.DataFrame:
    df = stock_df.copy().sort_values("Date")
    if df.empty:
        return df

    last_date = df["Date"].max()

    if range_label == "1D":
        return df[df["Date"] >= last_date - pd.Timedelta(days=1)]
    if range_label == "1W":
        return df[df["Date"] >= last_date - pd.Timedelta(days=7)]
    if range_label == "1M":
        return df[df["Date"] >= last_date - pd.Timedelta(days=30)]
    if range_label == "3M":
        return df[df["Date"] >= last_date - pd.Timedelta(days=90)]

    return df


def create_advanced_chart(stock_df: pd.DataFrame, symbol: str):
    df = add_chart_indicators(stock_df)

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.60, 0.18, 0.22],
        subplot_titles=(f"{symbol} Candlestick Chart", "Volume", "MACD")
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        ),
        row=1, col=1
    )

    # SMA overlays
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["SMA_3"], mode="lines", name="SMA 3"),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["SMA_5"], mode="lines", name="SMA 5"),
        row=1, col=1
    )

    # Bollinger Bands
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["BB_UPPER"], mode="lines", name="BB Upper"),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["BB_LOWER"], mode="lines", name="BB Lower"),
        row=1, col=1
    )

    # Volume
    volume_colors = [
        "#22c55e" if c >= o else "#ef4444"
        for o, c in zip(df["Open"], df["Close"])
    ]
    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Volume"],
            name="Volume",
            marker_color=volume_colors,
            opacity=0.75
        ),
        row=2, col=1
    )

    # MACD
    macd_colors = ["#22c55e" if v >= 0 else "#ef4444" for v in df["MACD_HIST"]]
    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["MACD_HIST"],
            name="MACD Hist",
            marker_color=macd_colors
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["MACD"], mode="lines", name="MACD"),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["MACD_SIGNAL"], mode="lines", name="Signal"),
        row=3, col=1
    )

    fig.update_layout(
        height=950,
        paper_bgcolor="#1f2937",
        plot_bgcolor="#1f2937",
        font=dict(color="white"),
        legend=dict(font=dict(color="white")),
        xaxis_rangeslider_visible=True,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    fig.update_xaxes(gridcolor="#374151", showline=True, linecolor="#475569")
    fig.update_yaxes(gridcolor="#374151", showline=True, linecolor="#475569")

    return fig