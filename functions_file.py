from binance.client import Client
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pandas import DataFrame
import time, dateparser, json, sys, os, requests

#........................................................................................#
# Function to get milliseconds of a specific date
def date_to_milliseconds(date_str):
    milliseconds = int(round(date_str.timestamp() * 1000))
    return milliseconds

#........................................................................................#
# Function to get the intervals to milliseconds
def interval_to_milliseconds(interval):
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60}
    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms

#........................................................................................#
# Z-function
def z_funct(field, n):
    z_mean = field.rolling(n).mean()
    z_std = field.rolling(n).std(ddof=0)
    z_result = (field - z_mean)/z_std
    return z_result

#........................................................................................#
# Main function for the API search
def get_historical_klines(symbol, interval, start_str, end_str=None):
    # create the Binance client, no need for api key
    client = Client("", "")

    # init our list
    output_data = []

    # setup the max limit
    limit = 500

    # convert interval to useful value in seconds
    timeframe = interval_to_milliseconds(interval)

    # convert our date strings to milliseconds
    start_ts = date_to_milliseconds(start_str)

    # if an end time was passed convert it
    end_ts = None
    if end_str:
        end_ts = date_to_milliseconds(end_str)

    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 500 entries or the end_ts if set
        temp_data = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            startTime=start_ts,
            endTime=end_ts
        )

        # handle the case where our start date is before the symbol pair listed on Binance
        if not symbol_existed and len(temp_data):
            symbol_existed = True

        if symbol_existed:
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        else:
            # it wasn't listed yet, increment our start date
            start_ts += timeframe

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind with the API
        if idx % 3 == 0:
            time.sleep(1)
            print('..Waiting for the API..')
    return output_data

#........................................................................................#
# Fetch the data and make it into a dataframe
def coin_data_function(coin, start = datetime.now() + timedelta(days = -1),
                        end = datetime.now(), tf='1H'):
    symbol = coin + 'USDT'

    '''For the bot one could check only few days before
    #d = timedelta(days = -1) # Change accordingly
    #start = datetime.now() + d # Y, M, D
    '''
    if tf == '1m':
        interval = Client.KLINE_INTERVAL_1MINUTE
    elif tf == '5m':
        interval = Client.KLINE_INTERVAL_5MINUTE
    elif tf == '15m':
        interval = Client.KLINE_INTERVAL_15MINUTE
    elif tf == '30m':
        interval = Client.KLINE_INTERVAL_30MINUTE
    elif tf == '1H':
        interval = Client.KLINE_INTERVAL_1HOUR
    elif tf == '2H':
        interval = Client.KLINE_INTERVAL_2HOUR
    elif tf == '4H':
        interval = Client.KLINE_INTERVAL_4HOUR
    elif tf == '12H':
        interval = Client.KLINE_INTERVAL_12HOUR
    elif tf == '1D':
        interval = Client.KLINE_INTERVAL_1DAY
    elif tf == '3D':
        interval = Client.KLINE_INTERVAL_3DAY
    elif tf == '1W':
        interval = Client.KLINE_INTERVAL_1WEEK
    else:
        interval = Client.KLINE_INTERVAL_1HOUR
    
    # Run the script
    try:
        klines = get_historical_klines(symbol, interval, start, end)
    except:
        msg = 'Connection lost - ' + str(datetime.now().strftime("%d %b %Y %H:%M:%S"))
        print(msg)
        sys.exit()

    # Create a dataframe from the list
    labels = ['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time',
    'USD volume', 'Number of trades', 'Buy volume', 'USD buy volume', 'Ignore']
    df = DataFrame.from_records(klines, columns = labels)
    df.drop(['Close time', 'Ignore'], axis = 1, inplace=True)
    df = df.astype(float)

    # Human readable
    cols = ['USD volume', 'USD buy volume']
    
    for col in cols:
        df[col] = df[col].values/1000 # Show in thousands

    # Convert miliseconds to readable
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    df['Open time'] = df['Open time'].dt.tz_localize('UTC')

    # Check your Time Zone. In Madrid it's 1 hours more than UTC time
    df['Open time'] = df['Open time'] + pd.Timedelta(hours=1)
    df['Open time'] = df['Open time'].dt.tz_localize(None)
    
    # Return
    return df
#........................................................................................#
# SMAs
def sma(df, field='Close'):

	# Binance defaults
	mm_list = [7, 25, 99]
	mms_list = ['SMA7', 'SMA25', 'SMA99']

	for mm, mms in zip(mm_list, mms_list):
		df[mms] = df[field].rolling(mm).mean()

#........................................................................................#
# RSI function
def RSI(field, period = 14):
    delta = field.diff()
    up, down = delta.copy(), delta.copy()

    up[up < 0], down[down > 0] = 0, 0

    rUp = up.ewm(com=period - 1,  adjust=False).mean()
    rDown = down.ewm(com=period - 1, adjust=False).mean().abs()

    rsi = 100 - 100 / (1 + rUp / rDown)   
    return rsi
#........................................................................................#
# SMA_value
def sma_value(coin, df_close, mas, actual_price):
    ma_list = []

    # Pop the current date - to be erased in the main code ---------------------#
    close_array = np.delete(df_close, -1)

    # List of MAs
    for ma in mas:
        # Add the current price
        ma_array = np.append(close_array, actual_price)[-ma:]

        # Get value
        ma_value = np.average(ma_array)

        # Append to the list
        ma_list.append(ma_value)   
    
    # Return ma_list
    return ma_list

#........................................................................................#

# Get the actual price --------------------------------------------------------
def actual_price(coin):
    # Get the coin price
    url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + coin + 'USDT'
    response = requests.get(url).text
    value = json.loads(response)
    actual_price = float(value['price'])

    return actual_price