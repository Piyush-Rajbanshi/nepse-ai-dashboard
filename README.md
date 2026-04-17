# 📈 NEPSE AI Stock Dashboard

An AI-powered stock analytics dashboard for the Nepal Stock Exchange (NEPSE) that combines live market data, historical storage, technical indicators, and machine learning.

---

## 🚀 Features

- 📡 Live market data scraping
- 🗂️ Historical data storage system (time-series build-up)
- 📊 Candlestick trading charts with volume
- 📈 Technical indicators:
  - SMA (Moving Averages)
  - RSI
  - MACD
  - Bollinger Bands
- 🎯 Buy / Sell / Hold signal generation
- 🤖 ML-based prediction (Linear Regression, Random Forest)
- 📉 Confidence scoring and stock ranking
- 🔍 Zoomable charts with time filters (1D, 1W, 1M)
- 🚨 Alert system for trading insights
- 🧠 AI-based query assistant
- ⭐ Watchlist tracking
- 📥 Exportable reports

---

## 🧠 Architecture Overview

The system is designed using a modular architecture:

- **Data Ingestion Layer** → Scraper + CSV loader  
- **Storage Layer** → Historical market data (`market_history.csv`)  
- **Processing Layer** → Indicator calculation (SMA, RSI, MACD, BB)  
- **Prediction Engine** → ML + rule-based fallback  
- **Visualization Layer** → Streamlit dashboard with Plotly charts  

---

## 📊 Trading Chart Features

- Candlestick chart (OHLC)
- Volume bars
- Bollinger Bands
- MACD (Histogram + Signal lines)
- SMA overlays
- Zoomable range selection (1D / 1W / 1M / 3M)

---


## ▶️ How to Run

pip install -r requirements.txt
streamlit run app.py

⚠️ Disclaimer

This project is for educational purposes only and does not provide financial advice.
