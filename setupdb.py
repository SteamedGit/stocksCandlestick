import sqlite3
import json
import os
import numpy as np
import requests
import pandas as pd
import finplot as fplt
from datetime import datetime
import pandas as pd


ALPHA_VANTAGE = "https://www.alphavantage.co/query?"
FUNCTION = "function=TIME_SERIES_DAILY_ADJUSTED"
OUTPUT_SIZE = "outputsize=compact"
ALPHA_VANTAGE_API = "apikey=" + os.environ.get("ALPHA_VANTAGE_API_KEY")
d = os.getcwd()
conn = sqlite3.connect(d + "/db/data.db")

c = conn.cursor()

"""Apple data adjusted and then added to db in a table"""
r1 = requests.get(
    ALPHA_VANTAGE
    + FUNCTION
    + "&"
    + "symbol="
    + "AAPL"
    + "&"
    + OUTPUT_SIZE
    + "&"
    + ALPHA_VANTAGE_API
)
data = r1.json()["Time Series (Daily)"]

dates = [np.datetime64(date) for date in data.keys()][::-1]

# there was a stock split on 2020-08-28
datesToAdjust = [
    date
    for date in data.keys()
    if np.datetime64("2020-08-31") - np.datetime64(date) > np.timedelta64(0, "D")
][::-1]
correctDates = [
    date
    for date in data.keys()
    if np.datetime64("2020-08-31") - np.datetime64(date) <= np.timedelta64(0, "D")
][::-1]

adjustedOpens = [np.float32(data[date]["1. open"]) / 4 for date in datesToAdjust]
adjustedHighs = [np.float32(data[date]["2. high"]) / 4 for date in datesToAdjust]
adjustedLows = [np.float32(data[date]["3. low"]) / 4 for date in datesToAdjust]


correctOpens = [np.float32(data[date]["1. open"]) for date in correctDates]
correctHighs = [np.float32(data[date]["2. high"]) for date in correctDates]
correctLows = [np.float32(data[date]["3. low"]) for date in correctDates]

closes = [np.float32(data[date]["5. adjusted close"]) for date in data][
    ::-1
]  # these are already adjusted
volumes = [np.int32(data[date]["6. volume"]) for date in data][::-1]

opens = adjustedOpens + correctOpens
highs = adjustedHighs + correctHighs
lows = adjustedLows + correctLows
ohlc1 = {"Open": opens, "Close": closes, "High": highs, "Low": lows, "Volume": volumes}
df1 = pd.DataFrame(ohlc1, index=dates)


df1.to_sql(
    "apple_daily_adjusted", conn, if_exists="replace", index=True, index_label="date"
)


""" Microsoft data added as table in db"""

r2 = requests.get(
    ALPHA_VANTAGE
    + FUNCTION
    + "&"
    + "symbol="
    + "MSFT"
    + "&"
    + OUTPUT_SIZE
    + "&"
    + ALPHA_VANTAGE_API
)
data = r2.json()["Time Series (Daily)"]
dates = [np.datetime64(date) for date in data.keys()][::-1]
opens = [np.float32(data[date]["1. open"]) for date in data][::-1]
closes = [np.float32(data[date]["5. adjusted close"]) for date in data][::-1]
highs = [np.float32(data[date]["2. high"]) for date in data][::-1]
lows = [np.float32(data[date]["3. low"]) for date in data][::-1]
volumes = [np.int32(data[date]["6. volume"]) for date in data][::-1]
ohlc2 = {"Open": opens, "Close": closes, "High": highs, "Low": lows, "Volume": volumes}
df2 = pd.DataFrame(ohlc2, index=dates)
df2.to_sql(
    "microsoft_daily_adjusted",
    conn,
    if_exists="replace",
    index=True,
    index_label="date",
)


"""S&P500 ETF data added as table in db"""
r3 = requests.get(
    ALPHA_VANTAGE
    + FUNCTION
    + "&"
    + "symbol="
    + "SPY"
    + "&"
    + OUTPUT_SIZE
    + "&"
    + ALPHA_VANTAGE_API
)
data = r3.json()["Time Series (Daily)"]


dates = [np.datetime64(date) for date in data.keys()][::-1]
opens = [np.float32(data[date]["1. open"]) for date in data][::-1]
closes = [np.float32(data[date]["5. adjusted close"]) for date in data][::-1]
highs = [np.float32(data[date]["2. high"]) for date in data][::-1]
lows = [np.float32(data[date]["3. low"]) for date in data][::-1]
volumes = [np.int32(data[date]["6. volume"]) for date in data][::-1]
ohlc = {"Open": opens, "Close": closes, "High": highs, "Low": lows, "Volume": volumes}
df = pd.DataFrame(ohlc, index=dates)
df.to_sql(
    "snp500_etf_daily",
    conn,
    if_exists="replace",
    index=True,
    index_label="date",
)

conn.commit()
print("Testing apple table:")
c.execute("SELECT * FROM apple_daily_adjusted")
print(c.fetchall())
print("Testing microsoft table:")
c.execute("SELECT * FROM microsoft_daily_adjusted")
print(c.fetchall())
print("Testing S&P 500 ETF")
c.execute("SELECT * FROM snp500_etf_daily")
print(c.fetchall())
conn.close()