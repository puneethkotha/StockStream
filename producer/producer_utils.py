import sys
# append the path of the parent directory
sys.path.append("./")

import yfinance as yf
import pandas as pd
import numpy as np

import json
from datetime import datetime, timedelta, time, timezone
from dotenv import load_dotenv
import time as t

load_dotenv()

def send_to_kafka(producer, topic, key, partition, message):
    # print("sent to kafka", message)
    producer.produce(topic, key=key, partition=partition, value=json.dumps(message).encode("utf-8"))
    producer.flush()

def retrieve_historical_data(producer, stock_symbol, kafka_topic, logger):
    # Define the date range for historical data
    stock_symbols = stock_symbol.split(",") if stock_symbol else []
    if not stock_symbols:
        logger.error("No stock symbols provided in the environment variable.")
        exit(1)

    # Define the date range
    end_date = datetime.now()
    start_date = (yf.Ticker(stock_symbols[0]).history(period="1mo").index[0]).strftime('%Y-%m-%d')

    for symbol_index, stock_symbol in enumerate(stock_symbols):
        try:
            # Fetch historical data
            historical_data = yf.download(
                stock_symbol, start=start_date, end=end_date, interval="2m", prepost=False
            )
            # print(f"Downloaded data for {stock_symbol}:\n{historical_data.head()}")

            # Handle MultiIndex columns if present
            if isinstance(historical_data.columns, pd.MultiIndex):
                historical_data.columns = [f"{col[0]}_{col[1]}" for col in historical_data.columns]


            # Check if DataFrame is empty
            if historical_data.empty:
                logger.warning(f"No data available for {stock_symbol}. Skipping...")
                continue

            print(f"Processed data for {stock_symbol}:\n{historical_data.head()}")

            # print(historical_data.loc[historical_data["Volume"] == 0])

            # Replace rows where Volume is zero
            # if f"Volume_{stock_symbol}" in historical_data.columns:
            #      historical_data.loc[
            #           historical_data[f"Volume_{stock_symbol}"] == 0,
            #           [f"Open_{stock_symbol}", f"High_{stock_symbol}", f"Low_{stock_symbol}", f"Close_{stock_symbol}", f"Adj Close_{stock_symbol}", f"Volume_{stock_symbol}"]
            #           ] = None  # or np.nan
            #      print(historical_data.head())


            # Convert and send historical data to Kafka
            for index, row in historical_data.iterrows():
                historical_data_point = {
                    "stock": stock_symbol,
                    "date": index.isoformat(),  # Convert index (datetime) to ISO format
                    "open": row[f"Open_{stock_symbol}"],  # Access value for current row
                    "high": row[f"High_{stock_symbol}"],
                    "low": row[f"Low_{stock_symbol}"],
                    "close": row[f"Close_{stock_symbol}"],
                    "volume": row[f"Volume_{stock_symbol}"]
                    }
                if historical_data_point['volume'] == 0:
                    historical_data_point = {
                    "stock": stock_symbol,
                    "date": index.isoformat(),  # Convert index (datetime) to ISO format
                    "open": None,  # Access value for current row
                    "high": None,
                    "low": None,
                    "close": None,
                    "volume": None
                    }
                send_to_kafka(producer, kafka_topic, stock_symbol, symbol_index, historical_data_point)
                print(f"Historical data sent to kafka {historical_data_point}")

        except Exception as e:
            logger.error(f"Error retrieving data for {stock_symbol}: {str(e)}")


def retrieve_real_time_data(producer, stock_symbol, kafka_topic, logger):
    retrieve_historical_data(producer, stock_symbol, kafka_topic, logger)

    stock_symbols = stock_symbol.split(",") if stock_symbol else []
    if not stock_symbols:
        logger.error("No stock symbols provided in the environment variable.")
        exit(1)

    while True:
        try:
            # Fetch real-time data
            current_time = datetime.now()
            is_market_open_bool = is_stock_market_open(current_time)
            # is_market_open_bool = True

            if is_market_open_bool:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=5)

                for symbol_index, stock_symbol in enumerate(stock_symbols):
                    real_time_data = yf.download(
                        stock_symbol, start=start_time, end=end_time, interval="15m"
                    )
                    if real_time_data.empty:
                        logger.warning(f"No real-time data for {stock_symbol}. Skipping...")
                        continue

                    # Convert and send the latest real-time data point to Kafka
                    latest_data_point = real_time_data.iloc[-1]
                    real_time_data_point = {
                        "stock": stock_symbol,
                        "date": latest_data_point.name.isoformat(),
                        "open": latest_data_point.get("Open"),
                        "high": latest_data_point.get("High"),
                        "low": latest_data_point.get("Low"),
                        "close": latest_data_point.get("Close"),
                        "volume": latest_data_point.get("Volume"),
                    }
                    send_to_kafka(producer, kafka_topic, stock_symbol, symbol_index, real_time_data_point)
                    logger.info(f"Real-time stock value pushed to Kafka topic {kafka_topic}")
            else:
                print("Market is closed. Sending null data.")
                for symbol_index, stock_symbol in enumerate(stock_symbols):
                    null_data_point = {
                        "stock": stock_symbol,
                        "date": current_time.isoformat(),
                        "open": None,
                        "high": None,
                        "low": None,
                        "close": None,
                        "volume": None,
                    }
                    send_to_kafka(producer, kafka_topic, stock_symbol, symbol_index, null_data_point)

            t.sleep(3)

        except Exception as e:
            logger.error(f"Error in real-time data retrieval: {str(e)}")


def get_stock_details(stock_symbol, logger):
    stock_symbols = stock_symbol.split(",") if stock_symbol else []
    print(stock_symbols)
    logger.info(stock_symbols)
    if not stock_symbols:
        logger.error(f"No stock symbols provided in the environment variable.")
        exit(1)
    # Create a Ticker object for the specified stock symbol
    stock_details = []
    for stock_symbol in stock_symbols:
        try:
        # Create a Ticker object for the specified stock symbol
            ticker = yf.Ticker(stock_symbol)

            # Retrieve general stock information
            stock_info = {
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Symbol': stock_symbol,
                'ShortName': ticker.info['shortName'],
                'LongName': ticker.info['longName'],
                'Industry': ticker.info['industry'],
                'Sector': ticker.info['sector'],
                'MarketCap': ticker.info['marketCap'],
                'ForwardPE': ticker.info['forwardPE'],
                'TrailingPE': ticker.info['trailingPE'],
                'Currency': ticker.info['currency'],
                'FiftyTwoWeekHigh': ticker.info['fiftyTwoWeekHigh'],
                'FiftyTwoWeekLow': ticker.info['fiftyTwoWeekLow'],
                'FiftyDayAverage': ticker.info['fiftyDayAverage'],
                'Exchange': ticker.info['exchange'],
                'ShortRatio': ticker.info['shortRatio']
            }
            stock_details.append(stock_info)
        except Exception as e:
            logger.info(f"Error fetching stock details for {stock_symbol}: {str(e)}")

    return stock_details

def is_stock_market_open(current_datetime=None):
    # If no datetime is provided, use the current datetime
    if current_datetime is None:
        current_datetime = datetime.now()

    # Define NYSE trading hours in Eastern Time Zone
    market_open_time = time(9, 30)
    market_close_time = time(16, 0)

    # Convert current_datetime to Eastern Time Zone
    current_time_et = current_datetime.astimezone(timezone(timedelta(hours=-5)))  # EDT (UTC-4)

    # Check if it's a weekday and within trading hours
    if current_time_et.weekday() < 5 and market_open_time <= current_time_et.time() < market_close_time:
        return True
    else:
        return False


