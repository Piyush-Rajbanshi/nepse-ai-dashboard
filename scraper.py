from io import StringIO
import re

import pandas as pd
import requests

LIVE_SOURCE_URL = "https://www.sharesansar.com/live-trading"


def fetch_sharesansar_live_data() -> pd.DataFrame:
    """
    Fetch live market data from Sharesansar and normalize it to the app schema.

    Output columns:
    Date, Symbol, Close, Open, High, Low, Volume, Prev_Close, Change, Percent_Change
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(LIVE_SOURCE_URL, headers=headers, timeout=25)
    response.raise_for_status()
    html = response.text

    tables = pd.read_html(StringIO(html))
    if not tables:
        raise ValueError("No HTML tables found on the live market page.")

    live_table = None
    for table in tables:
        if isinstance(table.columns, pd.MultiIndex):
            flat_cols = [
                " ".join([str(x).strip() for x in col if str(x).strip()])
                for col in table.columns
            ]
        else:
            flat_cols = [str(c).strip() for c in table.columns]

        col_text = " | ".join(col.lower() for col in flat_cols)

        if ("symbol" in col_text or "symbols" in col_text) and ("ltp" in col_text or "close" in col_text):
            live_table = table.copy()
            break

    if live_table is None:
        raise ValueError("Could not find the live market table.")

    if isinstance(live_table.columns, pd.MultiIndex):
        live_table.columns = [
            " ".join([str(x).strip() for x in col if str(x).strip()])
            for col in live_table.columns
        ]
    else:
        live_table.columns = [str(c).strip() for c in live_table.columns]

    rename_map = {}
    for col in live_table.columns:
        low = col.lower()

        if "symbol" in low:
            rename_map[col] = "Symbol"
        elif "ltp" in low or low == "close":
            rename_map[col] = "Close"
        elif "point change" in low or low == "change":
            rename_map[col] = "Change"
        elif "% change" in low or "percent change" in low:
            rename_map[col] = "Percent_Change"
        elif low == "open":
            rename_map[col] = "Open"
        elif low == "high":
            rename_map[col] = "High"
        elif low == "low":
            rename_map[col] = "Low"
        elif "volume" in low:
            rename_map[col] = "Volume"
        elif "prev" in low:
            rename_map[col] = "Prev_Close"

    live_table = live_table.rename(columns=rename_map)

    required_cols = ["Symbol", "Close"]
    missing = [col for col in required_cols if col not in live_table.columns]
    if missing:
        raise ValueError(f"Missing required columns after parsing: {missing}")

    keep_cols = [
        "Symbol",
        "Close",
        "Change",
        "Percent_Change",
        "Open",
        "High",
        "Low",
        "Volume",
        "Prev_Close",
    ]
    keep_cols = [col for col in keep_cols if col in live_table.columns]

    df = live_table[keep_cols].copy()

    numeric_cols = [col for col in df.columns if col != "Symbol"]
    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Symbol"] = df["Symbol"].astype(str).str.strip()
    df = df[df["Symbol"].ne("") & df["Close"].notna()].copy()

    timestamp_match = re.search(
        r"As of\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9:]{8})",
        html,
        flags=re.IGNORECASE
    )

    if timestamp_match:
        as_of = pd.to_datetime(timestamp_match.group(1), errors="coerce")
    else:
        as_of = pd.Timestamp.now()

    df["Date"] = as_of

    if "Volume" not in df.columns:
        df["Volume"] = 0

    ordered_cols = [
        "Date",
        "Symbol",
        "Close",
        "Open",
        "High",
        "Low",
        "Volume",
        "Prev_Close",
        "Change",
        "Percent_Change",
    ]
    ordered_cols = [col for col in ordered_cols if col in df.columns]

    df = df[ordered_cols].copy()
    return df.sort_values("Symbol").reset_index(drop=True)