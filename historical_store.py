from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
STORE_FILE = BASE_DIR / "market_history.csv"


def load_market_history() -> pd.DataFrame:
    if not STORE_FILE.exists():
        return pd.DataFrame(
            columns=[
                "Date", "Symbol", "Open", "High", "Low", "Close",
                "Volume", "Prev_Close", "Change", "Percent_Change"
            ]
        )

    df = pd.read_csv(STORE_FILE)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
    return df


def append_market_snapshot(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    history_df = load_market_history()

    snapshot_df = snapshot_df.copy()
    snapshot_df["Date"] = pd.to_datetime(snapshot_df["Date"])

    combined = pd.concat([history_df, snapshot_df], ignore_index=True)

    # Deduplicate exact same timestamp + symbol pulls
    combined = combined.drop_duplicates(subset=["Date", "Symbol"], keep="last")

    combined = combined.sort_values(["Symbol", "Date"]).reset_index(drop=True)
    combined.to_csv(STORE_FILE, index=False)
    return combined


def get_symbol_history(symbol: str) -> pd.DataFrame:
    history_df = load_market_history()
    if history_df.empty:
        return history_df

    df = history_df[history_df["Symbol"] == symbol].copy()
    return df.sort_values("Date").reset_index(drop=True)