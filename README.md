# stocksCandlestick

## Overview
Store, plot and do calculations with data about stocks/indexes from AlphaVantage and IEXCloud public apis. Daily data from AlphaVantage stored in a Sqlite3 database. Live data from IEXCloud is not stored. Create candlestick plots with macd from daily data. Calculate percentage change over specified intervals. Search for data corresponding to specific dates stored in database.


## How to use 
* Get api keys from AlphaVantage and IEXCloud
* Install packages listed in requirements.txt
* Create /db in base dir. 
* Run the setupdb.py to create a sqlite database with tables for apple, microsoft and snp500 etf. (Last 100 days of data for simplicity sake. Larger sets of data are more likely to require adjustments.) 
* Database will be in /db.
* Running apple.py, microsoft.py or snp500.py in src will update its data, print out last daily entry and print latest data about stock sale price from IEXCloud.

## How to add other stocks
In theory any stock available from AlphaVantage and IEXCloud should be easy to add, you need:
  * A database table for the stock, this can be achieved by adding to setupdb.py or manually adding it to the db.
  * A stock object that you call methods from:
  ``` 
  some_stock = stock(<stock_name>, <stock_symbol>, <stock_table_name_in_db>) 
  ```
  For example: 
  ``` 
  apple = stock("Apple", "AAPL", "apple_daily_adjusted")
  apple.getLatestLiveData() 
  ```
  

Updating, getting data and plotting are done via the stock class and apple.py, microsoft.py, and snp500.py are examples of how to use the stock class.

### Potential issue with adding stocks
Some stocks have undergone stock splits or other such disruptions, whilst AlphaVantage provides adjusted closing prices, the other values are unadjusted. 
This means that data may have to be adjusted. (See setupdb.py for how Apple's data had to be adjusted due to a recent stock split.)

## Examples
![](examples/apple_plot_example.png)


![](examples/apple_terminal_example.png)

## OS Support
Paths in the examples apple.py etc... are for a linux filesystem.
Adjust for your own OS accordingly.

## Disclaimer 
This is intended for non-commerical use.
Data attributed to AlphaVantage and IEXCloud.
