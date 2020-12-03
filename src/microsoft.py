import sqlite3
import os
import os.path
from Stock import stock

d = os.getcwd()
conn = sqlite3.connect(d + "/db/data.db")
with conn:
    c = conn.cursor()
    microsoft = stock("Microsoft", "MSFT", "microsoft_daily_adjusted")
    microsoft.update(conn, c)
    microsoft.getLatestLiveData()
    microsoft.candlestickDaily(conn)
