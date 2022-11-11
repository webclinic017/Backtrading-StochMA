import yfinance as yf
import configparser
import binance as bn
import csv


def get_history_binance(ticker, interval):
    config = configparser.ConfigParser()
    config.read('api.ini')
    client = bn.Client(
        testnet=False, api_key=config['BINANCE']['apikey'],
        api_secret=config['BINANCE']['apisecret'], )
    raw_data = client.get_historical_klines(symbol=ticker, interval=interval, klines_type=binance.enums.HistoricalKlinesType.FUTURES)
    return raw_data


def get_history_yf(ticker, tf):
    tick = yf.Ticker(ticker=ticker)
    history = tick.history(interval=tf)
    return history


def save_csv(name, tf, data):
    header = ['timestamp', 'open', 'high', 'low', 'close',
              'volume', 'close time', 'quote asset volume',
              'number of trades', 'taker buy base asset volume',
              'taker buy quote asset volume', 'can be ignored']
    with open('./binance/' + tf + '/' + name + '.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)


def read_binance_history(ticker, tf, t):
    path = './binance/'+ tf + '-' + t + '/' + ticker + '.csv'
    with open(path, 'r') as f:
        raw_data = csv.reader(f)
        raw_data = list(raw_data)
    return raw_data
