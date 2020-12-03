import requests
import os
import numpy as np
import pandas as pd
import finplot as fplt
from datetime import datetime
import json
import sqlite3


class stock:
    IEX = "https://cloud.iexapis.com/stable/tops?"
    ALPHA_VANTAGE = "https://www.alphavantage.co/query?"
    FUNCTION = "function=TIME_SERIES_DAILY_ADJUSTED"
    OUTPUT_SIZE = "outputsize=compact"
    IEX_API = "token=" + os.environ.get("IEX_API_KEY")
    ALPHA_VANTAGE_API = "apikey=" + os.environ.get("ALPHA_VANTAGE_API_KEY")

    def __init__(self, stockName, stockSymbol, tableName):
        self.stockName = stockName
        self.stockSymbol = stockSymbol
        self.tableName = tableName

    """ Takes a database connection and cursor. Gets the latest entry in the database and if it is older than the current date, get data from ALPHA_VANTAGE.
    If any of the dates in the newly acquired data are 1 day(or more) more recent than the last update then write these to the db."""

    def update(self, conn, c):
        today = datetime.today().strftime("%Y-%m-%d")
        c.execute(f"SELECT date FROM {self.tableName} ORDER BY date DESC LIMIT 1")
        lastUpdate = c.fetchone()[0][:10]
        print(f"Last Updated: {lastUpdate}")

        if today != lastUpdate:
            print("FETCHING NEW DATA")
            r1 = requests.get(
                self.ALPHA_VANTAGE
                + self.FUNCTION
                + "&"
                + "symbol="
                + self.stockSymbol
                + "&"
                + self.OUTPUT_SIZE
                + "&"
                + self.ALPHA_VANTAGE_API
            )
            data = r1.json()["Time Series (Daily)"]
            newDates = [
                date
                for date in data.keys()
                if np.datetime64(date) - np.datetime64(lastUpdate)
                > np.timedelta64(0, "D")
            ][::-1]
            newOpens = [np.float32(data[date]["1. open"]) for date in newDates]
            newCloses = [
                np.float32(data[date]["5. adjusted close"]) for date in newDates
            ]
            newHighs = [np.float32(data[date]["2. high"]) for date in newDates]
            newLows = [np.float32(data[date]["3. low"]) for date in newDates]
            newVolumes = [np.int32(data[date]["6. volume"]) for date in newDates]
            newDates = [np.datetime64(date) for date in newDates]
            newOCHL = {
                "Open": newOpens,
                "Close": newCloses,
                "High": newHighs,
                "Low": newLows,
                "Volume": newVolumes,
            }
            dfNew = pd.DataFrame(newOCHL, index=newDates)
            dfNew.to_sql(
                self.tableName,
                conn,
                if_exists="append",
                index=True,
                index_label="date",
            )
            conn.commit()

    """ Get the latest stock sale price from IEX Cloud. Not the most accurate service, but good enough."""

    def getLatestLiveData(self):
        rIEX = requests.get(
            self.IEX + self.IEX_API + "&" + "symbols=" + self.stockSymbol.lower()
        )

        IEXData = rIEX.json()[0]

        stockUpdated = datetime.fromtimestamp(IEXData["lastUpdated"] / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        latestStock = IEXData["lastSalePrice"]
        print(f"{self.stockName} Latest: {stockUpdated} Last Sale Price {latestStock} ")

    """ Prints the latest daily entry and creates a candlestick plot with macd and volume."""

    def candlestickDaily(self, conn):
        df = pd.read_sql(
            f"SELECT * FROM {self.tableName}",
            conn,
            index_col="date",
            parse_dates=["date"],
            columns=["open", "close", "high", "low", "volume"],
        )

        todayDate = pd.Timestamp.to_pydatetime(df.index.array[-1]).strftime("%Y-%m-%d")
        todayOpen = df.iloc[-1][0]
        todayClose = df.iloc[-1][1]
        todayHigh = df.iloc[-1][2]
        todayLow = df.iloc[-1][3]
        todayVolume = df.iloc[-1][4]

        print(
            f"{self.stockName} Daily: {todayDate} Open {todayOpen} Close {todayClose} High {todayHigh} Low {todayLow} Volume {todayVolume}"
        )

        ax2, ax3 = fplt.create_plot(f"{self.stockName} Daily Adjusted", rows=2)
        macd = df.Close.ewm(span=12).mean() - df.Close.ewm(span=26).mean()
        signal = macd.ewm(span=9).mean()
        df["macd_diff"] = macd - signal
        fplt.volume_ocv(
            df[["Open", "Close", "macd_diff"]],
            ax=ax3,
            colorfunc=fplt.strength_colorfilter,
        )
        fplt.plot(macd, ax=ax3, legend="MACD")
        fplt.plot(signal, ax=ax3, legend="Signal")
        fplt.candlestick_ochl(df[["Open", "Close", "High", "Low"]], ax=ax2)
        axo = ax2.overlay()
        fplt.volume_ocv(df[["Open", "Close", "Volume"]], ax=axo)
        fplt.show()
