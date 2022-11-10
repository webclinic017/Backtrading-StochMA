import binance.enums

import binance as bn
import csv
import configparser
import time


def get_history_binance(ticker, interval):
    config = configparser.ConfigParser()
    config.read('api.ini')
    client = bn.Client(
        testnet=False, api_key=config['BINANCE']['apikey'],
        api_secret=config['BINANCE']['apisecret'], )
    raw_data = client.get_historical_klines(symbol=ticker, interval=interval, klines_type=binance.enums.HistoricalKlinesType.FUTURES)
    return raw_data


def save_csv(name, tf, data):
    header = ['timestamp', 'open', 'high', 'low', 'close',
              'volume', 'close time', 'quote asset volume',
              'number of trades', 'taker buy base asset volume',
              'taker buy quote asset volume', 'can be ignored']
    with open('./binance/' + tf + '/' + name + '.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)


def main():
    tf = '1h'
    errors = []
    ok = []
    with open('./binancefuturesd_coin_perpetual_futures.txt') as f:
        reader = f.read()
        reader = reader.split('\n')
        reader = list(set(reader))
        for tick in reader:
            if tick == '':
                continue
            #tick = tick.replace('BINANCE:', '')
            #tick = tick.replace('PERP', '')
            tick = 'BNBRUNE'
            print(tick)
            try:
                data = get_history_binance(tick, tf)
                save_csv(tick, tf, data)
                ok.append(tick)
                print('Ok!')
            except:
                time.sleep(60)
                try:
                    print('Вторая попытка')
                    data = get_history_binance(tick, tf)
                    save_csv(tick, tf, data)
                    ok.append(tick)
                    print('Ok!')
                except:
                    errors.append(tick)
                    print('Ваще никак')
            time.sleep(5)
    print('Ok:')
    for n in ok:
        print(n)
    print(len(ok))
    print('Error:')
    for n in errors:
        print(n)
    print(len(errors))


if __name__ == "__main__":
    main()