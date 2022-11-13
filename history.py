import csv
import configparser
import yfinance as yf
import binance as bn


def get_history_binance(ticker: str, interval: str, market: str) -> list:
    """
    Get historical market data from Binance.
    :param ticker: Name of symbol pair
    :param interval: Time interval klines
    :param market: Market type. 'future' or 'spot'
    :return: list of OHLCV values (Open time, Open, High,
    Low, Close, Volume, Close time, Quote asset volume,
    Number of trades, Taker buy base asset volume,
    Taker buy quote asset volume, Ignore).
    """
    config = configparser.ConfigParser()
    config.read('api.ini')
    client = bn.Client(
        testnet=False, api_key=config['BINANCE']['apikey'],
        api_secret=config['BINANCE']['apisecret'], )
    if market == 'futures':
        klines_type = bn.enums.HistoricalKlinesType.FUTURES
    elif market == 'spot':
        klines_type = bn.enums.HistoricalKlinesType.SPOT
    else:
        raise ValueError
    raw_data = client.get_historical_klines(symbol=ticker, interval=interval,
                                            klines_type=klines_type)
    return raw_data


def get_history_yf(ticker: str, interval: str):
    """
    Get historical market data from Yahoo! Finance.
    :param ticker: Name of symbol
    :param interval: Time interval klines
    :return: OHLC in Pandas DataFrame format
    """
    tick = yf.Ticker(ticker=ticker)
    history = tick.history(interval=interval)
    return history


def save_csv(name: str, interval: str, data: str, data_source: str = 'binance',) -> None:
    """
    Save input data, in csv file. Format path to create files './data_source/interval/name.csv'.
    :param name: Name of symbol or pair
    :param interval: Time interval klines
    :param data: Market data
    :param data_source: Source data
    :return: None
    """
    header = ['timestamp', 'open', 'high', 'low', 'close',
              'volume', 'close time', 'quote asset volume',
              'number of trades', 'taker buy base asset volume',
              'taker buy quote asset volume', 'can be ignored']
    path = './' + data_source + '/' + interval + '/' + name + '.csv'
    with open(path, 'w', encoding='utf=8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)


def read_csv(ticker: str, interval: str, market_type: str, data_source: str = 'binance',) -> list:
    """
    Get market data from saved csv file.
    :param ticker: Name of symbol or pair
    :param interval: Time interval klines
    :param market_type: Market type. 'future' or 'spot'
    :param data_source: Source data
    :return: List data
    """
    path = './' + data_source + '/'+ interval + '-' + market_type + '/' + ticker + '.csv'
    with open(path, 'r', encoding='utf-8') as out:
        raw_data = csv.reader(out)
        raw_data = list(raw_data)
    return raw_data
