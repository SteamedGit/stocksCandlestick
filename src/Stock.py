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
        # Print latest entry date and get data from api if the latest entry is not today's date
        today = datetime.today().strftime("%Y-%m-%d")
        c.execute(f"SELECT date FROM {self.tableName} ORDER BY date DESC LIMIT 1")
        lastUpdate = c.fetchone()[0][:10]
        print(f"Latest Entry: {lastUpdate}")

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

            # Any date that is more recent than the latest entry in the db corresponds to a row of new data that must be inserted
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

        IEXData = rIEX.json()
        if IEXData:
            IEXData = IEXData[0]
            stockUpdated = datetime.fromtimestamp(
                IEXData["lastUpdated"] / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")

            latestStock = IEXData["lastSalePrice"]
            print(
                f"{self.stockName} Latest: {stockUpdated} Last Sale Price {latestStock} "
            )
        else:
            print(f"{self.stockName} has no live data.")
        # IEXData = rIEX.json()
        # print(IEXData)

    """ Prints the latest daily entry and creates a candlestick plot with macd and volume."""

    def candlestickDaily(self, conn):
        # Load data from db into pandas dataframe
        df = pd.read_sql(
            f"SELECT * FROM {self.tableName}",
            conn,
            index_col="date",
            parse_dates=["date"],
            columns=["open", "close", "high", "low", "volume"],
        )

        # Print latest entry
        todayDate = pd.Timestamp.to_pydatetime(df.index.array[-1]).strftime("%Y-%m-%d")
        todayOpen = df.iloc[-1][0]
        todayClose = df.iloc[-1][1]
        todayHigh = df.iloc[-1][2]
        todayLow = df.iloc[-1][3]
        todayVolume = int(df.iloc[-1][4])

        print(
            f"{self.stockName} Daily: {todayDate} Open {round(todayOpen,3)} "
            f"Close {round(todayClose,3)} High {round(todayHigh,3)} Low {round(todayLow,3)} "
            f"Volume {round(todayVolume,3)}"
        )

        # Create candlestick plot with daily volume and a corresponding macd + signal plot
        ax1, ax2 = fplt.create_plot(f"{self.stockName} Daily Adjusted", rows=2)
        macd = df.Close.ewm(span=12).mean() - df.Close.ewm(span=26).mean()
        signal = macd.ewm(span=9).mean()
        df["macd_diff"] = macd - signal
        fplt.volume_ocv(
            df[["Open", "Close", "macd_diff"]],
            ax=ax2,
            colorfunc=fplt.strength_colorfilter,
        )
        fplt.plot(macd, ax=ax2, legend="MACD")
        fplt.plot(signal, ax=ax2, legend="Signal")
        fplt.candlestick_ochl(df[["Open", "Close", "High", "Low"]], ax=ax1)
        axo = ax1.overlay()
        fplt.volume_ocv(df[["Open", "Close", "Volume"]], ax=axo)
        fplt.show()

    """ Gets the table entry corresponding to a string date in the form %Y-%m-%d. If not found returns None and prints custom error message."""

    def getDay(self, c, date):
        date += " 00:00:00"
        date = str(pd.to_datetime(date))
        c.execute(f"SELECT * FROM {self.tableName} WHERE date='{date}'")
        raw = c.fetchall()
        if len(raw) > 0:
            row = raw[0]
            return (
                f"Date: {row[0][:10]} Open: {round(row[1],3)} Close: {round(row[2],3)} "
                f"High: {round(row[3],3)} Low: {round(row[4],3)} Volume: {round(row[5],3)}"
            )

        else:
            print(
                "Day is not in database. Either no trading occured on that date or it is out of range of the database."
            )

    """ Gets the percentage change in stock price in the inclusive range of two %Y-%m-%d dates. If no date range specified it gets the change between 
    the latest two dates. If date range is out of db range returns None and prints custom error message """

    def getPercentageChange(self, c, dateRange=[None, None]):
        if (dateRange[0] == None) & (dateRange[1] == None):
            c.execute(
                f"SELECT date, close FROM {self.tableName} ORDER BY date DESC LIMIT 2"
            )
            toData = c.fetchone()
            fromData = c.fetchone()
            change = round((toData[1] - fromData[1]) / fromData[1] * 100, 3)
            if change > 0:
                change = "+" + str(change)
            return f"Percentage change from {fromData[0][:10]} to {toData[0][:10]} is {change}% "
        else:
            # Get first and last entry in db so we can check that date range is in db date range
            c.execute(f"SELECT date FROM {self.tableName} ORDER BY date ASC LIMIT 1")
            earliestDate = c.fetchone()[0][:10]
            c.execute(f"SELECT date FROM {self.tableName} ORDER BY date DESC LIMIT 1")
            latestDate = c.fetchone()[0][:10]
            if (
                np.datetime64(dateRange[0]) - np.datetime64(earliestDate)
                >= np.timedelta64(0, "D")
            ) & (
                np.datetime64(dateRange[1]) - np.datetime64(latestDate)
                <= np.timedelta64(0, "D")
            ):
                fromDate = str(pd.to_datetime(dateRange[0] + " 00:00:00"))
                toDate = str(pd.to_datetime(dateRange[1] + " 00:00:00"))

                # Find closest dates to inclusive lower and upper bounds of date range and calculate change
                c.execute(
                    f"SELECT date, close FROM {self.tableName} WHERE date >= '{fromDate}' AND date < '{toDate}' ORDER BY date ASC LIMIT 1 "
                )
                fromClose = c.fetchone()
                c.execute(
                    f"SELECT date, close FROM {self.tableName} WHERE date > '{fromDate}' AND date <= '{toDate}' ORDER BY date DESC LIMIT 1"
                )
                toClose = c.fetchone()
                change = round((toClose[1] - fromClose[1]) / fromClose[1] * 100, 3)
                if change > 0:
                    change = "+" + str(change)
                return f"Percentage change from {fromClose[0][:10]} to {toClose[0][:10]} is {change}%"
            else:
                print("Out of range of stored dates.")