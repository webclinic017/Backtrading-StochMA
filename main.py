import datetime
import backtrader as bt
import pandas as pd
import history


class TestStrategy(bt.Strategy):
    params = (('exitbars', 5),
              ('maperiod', 14),
              ('doprint', False),
              ('matype', 'SMA'),
              ('fastk_period', 5),
              ('slowk_period', 3),
              ('slowk_matype', 0),
              ('slowd_period', 3),
              ('slowd_matype', 0),
              ('stoch_top', 80),
              ('stoch_bottom', 20),
              ('sl', 0.01),
              ('ppperiod', 8))

    def log(self, txt, dt=None, doprint=True,):
        if self.params.doprint or doprint:
            time = dt or self.datas[0].datetime.time()
            date = dt or self.datas[0].datetime.date()
            position = self.position.size
            print("%s - %s %s" % (date, time, txt))
            print('Position: %s' % position)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.bar_executed = None

        if self.params.matype == 'SMA':
            self.ma = bt.indicators.SMA(self.datas[0], period=self.params.maperiod)
        elif self.params.matype == 'EMA':
            self.ma = bt.talib.EMA(self.datas[0], timeperiod=self.params.maperiod)
        elif self.params.matype == 'DEMA':
            self.ma = bt.indicators.DEMA(self.datas[0], period=self.params.maperiod)
        elif self.params.matype == 'KAMA':
            self.ma = bt.indicators.KAMA(self.datas[0], period=self.params.maperiod)
        elif self.params.matype == 'TEMA':
            self.ma = bt.indicators.TEMA(self.datas[0], period=self.params.maperiod)
        elif self.params.matype == 'WMA':
            self.ma = bt.indicators.WMA(self.datas[0], period=self.params.maperiod)

        self.stochK = bt.indicators.StochasticFast(self.datas[0])

        self.kcrossbottom = bt.indicators.CrossOver(self.stochK.percK, self.p.stoch_bottom)
        self.kcrosstop = bt.indicators.CrossOver(self.stochK.percK, self.p.stoch_top)
        self.dcrossbottom = bt.indicators.CrossOver(self.stochK.percD, self.p.stoch_bottom)
        self.dcrosstop = bt.indicators.CrossOver(self.stochK.percD, self.p.stoch_top)
        self.macross = bt.indicators.CrossOver(self.dataclose, self.ma)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' % (order.executed.price,
                                                                           order.executed.value,
                                                                           order.executed.comm,)
                    )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' % (order.executed.price,
                                                                            order.executed.value,
                                                                            order.executed.comm,)
                    )
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm), doprint=False)

        if trade.justopened:
            print(f'New trade {trade.tradeid} opened')
        elif trade.isclosed:
            print(f'Trade {trade.tradeid} recently closed')

    def long_in(self):
        self.log('BUY CREATE, %.2f' % self.dataclose[0])
        minimum = self.get_lowest()
        sl = minimum * (1 - self.params.sl)
        self.order = self.buy(
            exectype=bt.Order.Limit,
            valid=datetime.datetime.now() + datetime.timedelta(days=1),
            price=self.data.close[0],
            stopprice=sl,
            )

    def long_out(self):
        self.log('LONG OUT, %.2f' % self.dataclose[0])
        print(self.trade)
        self.order = self.sell(
            exectype=bt.Order.Limit,
            valid=datetime.datetime.now() + datetime.timedelta(days=1),
            price=self.data.close[0],
            )

    def short_in(self):
        self.log('SHORT IN, %.2f' % self.dataclose[0])
        print(self.position)
        maximum = self.get_highest()
        sl = maximum * (1 - self.params.sl)
        self.order = self.sell(
            exectype=bt.Order.Limit,
            valid=datetime.datetime.now() + datetime.timedelta(days=1),
            price=self.data.close[0],
            stopprice=sl,
            )

    def short_out(self):
        self.log('SHORT OUT, %.2f' % self.dataclose[0])
        print(self.position)
        self.order = self.buy(
            exectype=bt.Order.Limit,
            valid=datetime.datetime.now() + datetime.timedelta(days=1),
            price=self.data.close[0],
            )
        pass

    def get_lowest(self):
        minimum = self.datas[0].low[0]
        i = 0
        for low in self.datas[0].low:
            if low < minimum:
                minimum = low
            i += 1
            if i == self.params.ppperiod:
                return minimum
        return minimum

    def get_highest(self):
        maximum = 0
        i = 0
        for high in self.datas[0].high:
            if high < maximum:
                high = maximum
            i += 1
            if i == self.params.ppperiod:
                return maximum
        return maximum

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
        if self.order:
            return
        if self.macross > 0 and self.kcrossbottom > 0:
             self.long_in()
        # if self.position.size == 0:
        #     if self.macross > 0 and self.kcrossbottom > 0:
        #         self.long_in()
        # elif self.position.size > 0:
        #     if self.macross < 0 and self.kcrosstop < 0:
        #         self.long_out()
        # elif self.position.size < 0:
        #     pass


def data_print(mas):
    print('Stat:')
    print('---------------------')
    print('Total order')
    total = mas['total']
    print('Total: %d. Open: %d, Closed: %d' % (total['total'], total['open'], total['closed'],))
    print('---------------------')
    print('Streak:')
    streak = mas['streak']
    print(
        'Won\n\tCurrent: %d. Longest: %d.\nLost\n\tCurrent: %d. Longest: %d.' % (streak['won']['current'],
                                                                                 streak['won']['longest'],
                                                                                 streak['lost']['current'],
                                                                                 streak['lost']['longest'],)
        )
    print('---------------------')
    print('PnL: ')
    pnl = mas['pnl']
    print(
        'Gross\n\tTotal: %d. Average: %d.\nNet\n\tTotal: %d. Average: %d' % (pnl['gross']['total'],
                                                                             pnl['gross']['average'],
                                                                             pnl['net']['total'],
                                                                             pnl['net']['average'],)
        )
    print('---------------------')
    print('Won: ')
    won = mas['won']
    print(
        '\tTotal: %d.\nPnl:\n\tTotal: %d. Average: %d. Max: %d' % (won['total'], won['pnl']['total'],
                                                                   won['pnl']['average'], won['pnl']['max'],)
        )
    print('---------------------')
    print('Lost: ')
    lost = mas['lost']
    print(
        '\tTotal: %d.\nPnL:\n\tTotal: %d. Average: %d. Max: %d.' % (lost['total'], lost['pnl']['total'],
                                                                    lost['pnl']['average'], lost['pnl']['max'],)
        )
    print('---------------------')
    print('Long: ')
    long = mas['long']
    print(
        '\tTotal: %d.\nPnl:\n\tTotal: %d. Average: %d.\n'
        'Won:\n\tTotal: %d. Average: %d. Max: %d.\n'
        'Lost:\n\tTotal: %d. Average: %d. Max: %d.\n'
        'Won: %d. Lost: %d.' % (long['total'], long['pnl']['total'],
                                long['pnl']['average'], long['pnl']['won']['total'],
                                long['pnl']['won']['average'], long['pnl']['won']['max'],
                                long['pnl']['lost']['total'], long['pnl']['lost']['average'],
                                long['pnl']['lost']['max'], long['won'], long['lost'],
                                )
        )
    print('---------------------')
    print('Short: ')
    short = mas['short']
    print(
        '\tTotal: %d.\nPnl:\n\tTotal: %d. Average: %d.\n'
        'Won:\n\tTotal: %d. Average: %d. Max: %d.\n'
        'Lost:\n\tTotal: %d. Average: %d. Max: %d.\n'
        'Won: %d. Lost: %d.' % (short['total'], short['pnl']['total'],
                                short['pnl']['average'], short['pnl']['won']['total'],
                                short['pnl']['won']['average'], short['pnl']['won']['max'],
                                short['pnl']['lost']['total'], short['pnl']['lost']['average'],
                                short['pnl']['lost']['max'], short['won'], short['lost'],
                                )
        )
    print('---------------------')
    print('Len: ')
    in_market = mas['len']
    print(
        '\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['total'], in_market['average'],
                                                         in_market['max'], in_market['min'],)
        )
    print(
        'Won:\n\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['won']['total'],
                                                               in_market['won']['average'],
                                                               in_market['won']['max'],
                                                               in_market['won']['min'],)
        )
    # print(
    #     'Won:\n\tTotal: %d. Average: %d. Max: %d. Min: ???' % (in_market['won']['total'],
    #                                                            in_market['won']['average'],
    #                                                            in_market['won']['max'],)
    #     )
    print(
        'Lost:\n\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['lost']['total'],
                                                                in_market['lost']['average'],
                                                                in_market['lost']['max'],
                                                                in_market['lost']['min'],)
        )
    print(
        'Long:\n\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['long']['total'],
                                                                in_market['long']['average'],
                                                                in_market['long']['max'],
                                                                in_market['long']['min'],)
        )
    print(
        '\tWon:\n\t\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['long']['won']['total'],
                                                                   in_market['long']['won']['average'],
                                                                   in_market['long']['won']['max'],
                                                                   in_market['long']['won']['min'],)
        )
    print(
        '\tLost:\n\t\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['long']['lost']['total'],
                                                                    in_market['long']['lost']['average'],
                                                                    in_market['long']['lost']['max'],
                                                                    in_market['long']['lost']['min'],)
        )
    print(
        'Short:\n\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['short']['total'],
                                                                 in_market['short']['average'],
                                                                 in_market['short']['max'],
                                                                 in_market['short']['min'],)
        )
    print(
        '\tWon:\n\t\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['short']['won']['total'],
                                                                   in_market['short']['won']['average'],
                                                                   in_market['short']['won']['max'],
                                                                   in_market['short']['won']['min'],)
        )
    print(
        '\tLost:\n\t\tTotal: %d. Average: %d. Max: %d. Min: %d.' % (in_market['short']['lost']['total'],
                                                                    in_market['short']['lost']['average'],
                                                                    in_market['short']['lost']['max'],
                                                                    in_market['short']['lost']['min'],)
        )


def convert_data(raw_data):
    data = pd.DataFrame(
        raw_data[1::],
        columns=['timestamp', 'open', 'high', 'low', 'close',
                 'volume', 'close time', 'quote asset volume',
                 'number of trades', 'taker buy base asset volume',
                 'taker buy quote asset volume', 'can be ignored']
        )
    data = data.iloc[:, :6]
    data = data.astype(float)
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

    df = bt.feeds.PandasData(dataname=data,
                             datetime="timestamp",
                             open="open",
                             high="high",
                             low="low",
                             close="close",
                             volume="volume",
                             openinterest=None,)
    return df


def start_test(data, matype='SMA', period=30):
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcommission(commission=0.0004)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='TradeAnalyzer')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')
    cerebro.addanalyzer(bt.analyzers.Calmar, _name='Calmar')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='TimeDrawDown')
    cerebro.addanalyzer(bt.analyzers.GrossLeverage, _name='GrossLeverage')
    cerebro.addanalyzer(bt.analyzers.PositionsValue, _name='PositionsValue')
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')
    cerebro.addanalyzer(bt.analyzers.LogReturnsRolling, _name='LogReturnsRolling')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='Returns')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='SharpeRatio_A')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='SQN')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='TimeReturn')
    cerebro.addanalyzer(bt.analyzers.VWR, _name='VWR')

    cerebro.addstrategy(TestStrategy, matype=matype, maperiod=period)
    cerebro.broker.setcash(100000)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    result = cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()
    return result


def main():
    ma_types = ['SMA', 'EMA', 'DEMA', 'KAMA', 'TEMA', 'WMA']

    df = history.read_csv('BTCUSDT', '1h', 'futures', 'binance',)
    data = convert_data(df)

    # data = history.get_history_binance('BTCUSDT', '1h')

    result = start_test(data=data, matype='SMA', period=4,)

    trade_analyzer = result[0].analyzers.getbyname('TradeAnalyzer').get_analysis()
    # annual_return = result[0].analyzers.getbyname('TradeAnalyzer').get_analysis()

    data_print(trade_analyzer)
    # print(annual_return)


if __name__ == '__main__':
    main()
