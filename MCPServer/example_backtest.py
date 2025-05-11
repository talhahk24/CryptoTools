from backtesting import Backtest, Strategy
from backtesting.test import GOOG
from backtesting.lib import crossover
import talib

#series is the list of stats you get after running the backtest
def optim_func(series):


    #basically we are filtering out backtests with less than 10 trades
    if series['# Trades'] < 10:
        return -1

    return series['Equity Final [$]'] / series['Exposure Time [%]']

class RsiOscillator(Strategy):


    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    #runs one time at initialisation
    def init(self):

        #the first parameter is a function that actually calculates the indicator
        #second one is the data used to calculate the indicator
        #any other arguments are gonna get passed into the function in the first argument
        #RSI takes price and window
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)

    #goes through each candle, evaluates the criteria, decides whether to buy on the next candle        
    def next(self):
        if crossover(self.rsi, self.upper_bound):
            #sell everything
            self.position.close()

        elif crossover(self.rsi, self.lower_bound):
            self.buy()

#GOOG is pandas dataframe of google data in ohlcv format
bt = Backtest(GOOG, RsiOscillator, cash = 10000)

stats, heatmap = bt.optimize(
    upper_bound = range(55, 86, 5),
    lower_bound = range(10, 45, 5),
    rsi_window = range(10, 31, 2),
    maximize = optim_func,
    constraint = lambda param: param.upper_bound > param.lower_bound,
    max_tries = 100,
    return_heatmap = True
)

    

bt.plot()

print(stats)