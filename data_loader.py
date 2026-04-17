from pathlib import Path

import numpy as np
import pandas as pd

from scraper import fetch_sharesansar_live_data

BASE_DIR = Path(__file__).resolve().parent


def load_csv_data(filename="nepse_sample_data.csv") -> pd.DataFrame:
    file_path = BASE_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])

    required_cols = ["Date", "Symbol", "Close"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df.sort_values(["Symbol", "Date"]).reset_index(drop=True)
    return df


def load_api_data() -> pd.DataFrame:
    raise NotImplementedError("API mode is not connected yet.")


def load_scraped_data() -> pd.DataFrame:
    return fetch_sharesansar_live_data()


def get_data(source="CSV") -> pd.DataFrame:
    source = source.upper()

    if source == "CSV":
        return load_csv_data()
    if source == "API":
        return load_api_data()
    if source == "SCRAPER":
        return load_scraped_data()

    raise ValueError(f"Unsupported data source: {source}")


def get_latest_market_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    latest_df = df.sort_values("Date").groupby("Symbol").tail(1).copy()
    prev_df = df.sort_values("Date").groupby("Symbol").nth(-2).reset_index()

    latest_df = latest_df.merge(
        prev_df[["Symbol", "Close"]],
        on="Symbol",
        how="left",
        suffixes=("", "_Prev")
    )

    latest_df["Close_Prev"] = latest_df["Close_Prev"].fillna(latest_df["Close"])

    if "Change" not in latest_df.columns:
        latest_df["Change"] = latest_df["Close"] - latest_df["Close_Prev"]
    else:
        latest_df["Change"] = latest_df["Change"].fillna(latest_df["Close"] - latest_df["Close_Prev"])

    return latest_df


def simulate_live_update(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    latest_idx = df.groupby("Symbol")["Date"].idxmax()
    noise = np.random.uniform(-3, 3, size=len(latest_idx))

    df.loc[latest_idx, "Close"] = (df.loc[latest_idx, "Close"].values + noise).round(2)

    if "Volume" in df.columns:
        vol_noise = np.random.randint(-500, 500, size=len(latest_idx))
        new_vol = df.loc[latest_idx, "Volume"].values + vol_noise
        df.loc[latest_idx, "Volume"] = np.maximum(new_vol, 0)

    return df