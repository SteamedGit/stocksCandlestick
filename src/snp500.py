import sqlite3
import os
import os.path
from Stock import stock

d = os.getcwd()
conn = sqlite3.connect(d + "/db/data.db")
with conn:
    c = conn.cursor()
    snp500 = stock("S&P 500 ETF", "SPY", "snp500_etf_daily")
    snp500.update(conn, c)
    snp500.getLatestLiveData()
    print(snp500.getPercentageChange(c))
    snp500.candlestickDaily(conn)
