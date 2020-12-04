import sqlite3
import os
import os.path
from Stock import stock


d = os.getcwd()
conn = sqlite3.connect(d + "/db/data.db")
with conn:
    c = conn.cursor()
    apple = stock("Apple", "AAPL", "apple_daily_adjusted")
    apple.update(conn, c)
    apple.getLatestLiveData()
    print(apple.getPercentageChange(c))
    apple.candlestickDaily(conn)
