import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from hmmlearn.hmm import GaussianHMM
import warnings 
from ib_insync import *
import alpaca_trade_api as tradeapi
from alpaca.data.enums import DataFeed
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from datetime import timezone
import time

class MeanReversion:
    
    # initialization
    def __init__(self, ticker, window, alo):
        warnings.filterwarnings("ignore")
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        self.ticker = ticker
        self.window = window
        self.ib = IB()
        self.ib.connect('127.0.0.1', 4002, clientId=1)

        self.logs = pd.DataFrame(columns=['Time', 'Strat','BH', 'Signal', 'Action'])
        self.alo = alo
        self.position = 0
        new_row = {
            'Time': datetime.now(),
            'Strat': self.getsnap(),
            'BH': self.getsnap(),
            'Zsc': 0,
            'Action': 'NA'
        }       
        self.logs = pd.concat([self.logs, pd.DataFrame([new_row])], ignore_index=True)
        

    # data collection
    def data_collection(self):
        self.api_key="PKYOJZNEMFQPBCSGY3MC"
        self.secret_key="cVPzOWmEz4bXrbUlm139qLQJwVaYnKuAYBdjDhcM"

        client = StockHistoricalDataClient(
            api_key="PKYOJZNEMFQPBCSGY3MC",
            secret_key="cVPzOWmEz4bXrbUlm139qLQJwVaYnKuAYBdjDhcM",
        )

        start = (datetime.now(timezone.utc) - timedelta(minutes=11))
        end = datetime.now(timezone.utc)      

        request_params = StockBarsRequest(
            symbol_or_symbols=[self.ticker],
            timeframe=TimeFrame.Minute,
            start=start,
            end=end,
            feed=DataFeed.IEX
        )

        # historical data
        bars = client.get_stock_bars(request_params)
        self.data = bars.df.iloc[:,:4]
    
    # calculate rolling mean and stdev
    def mean_stdev(self):
        self.data['MA'] = self.data['close'].rolling(self.window).mean().shift(1).round(2)
        self.data['SDev'] = self.data['close'].rolling(self.window).std().shift(1).round(2)

        # storing rolling m/sd
        self.MA = self.data['MA'].iloc[-1]
        self.sd = self.data['SDev'].iloc[-1]

    def getsnap(self):
        BASE_URL = 'https://paper-api.alpaca.markets/v2' 
        api = tradeapi.REST(self.api_key, self.secret_key, BASE_URL, api_version='v2')
        quote = api.get_latest_quotes(self.ticker)
        return quote
    
    # calc z score
    def z_score(self):
        xi = self.getsnap()
        zsc = (xi - self.MA) / self.sd
        return zsc

    # ID trading signal/execution
    def signal_exe(self):
        if self.z_score() <= -1 and self.position == 0: #buy
            self.sig = 'BUY'
            self.BUY()
        
        elif self.z_score() < 0 and self.position == 1: # hold
            self.sig = 'HOLD'
            self.HOLD()

        elif self.z_score() >= 0 and self.position == 1: #sell 
            self.sig = 'SELL'
            self.SELL()

        else: 
            self.sig = 'NA'
            self.NONE()
            
        ''' Short stuff
        elif self.zsc >= 1 and self.position == 0: #sell short
            self.sig = 'SH'
        elif self.zsc <= 0 and self.position == 1: #close short
            self.sig = 'C'
        '''

    def executor(self):
        if self.sig == 'BUY':
            self.position = 1
        elif self.sig == 'SELL':
            self.position = 0
        contract = Stock(self.ticker,'SMART','USD')
        order = MarketOrder(self.sig,self.alo)
        self.trade = self.ib.placeOrder(contract,order)

    # trading functions that log actions, ACCOUNT FOR FEES
    def BUY(self):
        self.executor()
        self.buyprice = self.getsnap()
        new_row = {
            'Time': datetime.now(),
            'Strat': self.buyprice,
            'BH': self.getsnap(),
            'Zsc': self.z_score(),
            'Action': self.sig
        }       
        self.logs = pd.concat([self.logs, pd.DataFrame([new_row])], ignore_index=True)
        print('Buying @ {}'.format(self.buyprice))
        print("Order Status:", self.trade.orderStatus.status)
        time.sleep(5)

    def SELL(self):
        self.executor()
        if self.logs.iloc[-1,4] == 'BUY':
            sellprice = self.logs.iloc[-1,1] * self.getsnap()/self.buyprice
        elif self.logs.iloc[-1,4] == 'HOLD':
            sellprice = self.logs.iloc[-1,1] * self.getsnap()/self.newhold
        new_row = {
            'Time': datetime.now(),
            'Strat': sellprice,
            'BH': self.getsnap(),
            'Zsc': self.z_score(),
            'Action': self.sig
        }       
        self.logs = pd.concat([self.logs, pd.DataFrame([new_row])], ignore_index=True)
        print('Selling @ {}'.format(sellprice))
        print("Order Status:", self.trade.orderStatus.status)
        time.sleep(10)

    def HOLD(self):
        if self.logs.iloc[-1,4] == 'BUY':
            holdprice = self.logs.iloc[-1,1] * self.getsnap()/self.buyprice
            self.newhold = self.getsnap()
        elif self.logs.iloc[-1,4] == 'HOLD':
            holdprice = self.logs.iloc[-1,1] * self.getsnap()/self.newhold
            self.newhold = self.getsnap()
        new_row = {
            'Time': datetime.now(),
            'Strat': holdprice,
            'BH': self.getsnap(),
            'Zsc': self.z_score(),
            'Action': self.sig
        }       
        self.logs = pd.concat([self.logs, pd.DataFrame([new_row])], ignore_index=True)
        time.sleep(5)

    def NONE(self):
        new_row = {
            'Time': datetime.now(),
            'Strat': self.logs.iloc[-1,1],
            'BH': self.getsnap(),
            'Zsc': self.z_score(),
            'Action': self.sig
        }       
        self.logs = pd.concat([self.logs, pd.DataFrame([new_row])], ignore_index=True)
        time.sleep(10)

    def CTRLC(self):
        if self.position == 1: 
            pr = self.getsnap()
            contract = Stock(self.ticker,'SMART','USD')
            order = MarketOrder('SELL',self.alo)
            trade = self.ib.placeOrder(contract,order)
            if self.logs.iloc[-1,4] == 'BUY':
                sellprice = self.logs.iloc[-1,1] * pr/self.buyprice
            elif self.logs.iloc[-1,4] == 'HOLD':
                sellprice = self.logs.iloc[-1,1] * pr/self.newhold
            
            new_row = {
                'Time': datetime.now(),
                'Strat': sellprice,
                'BH': self.getsnap(),
                'Zsc': self.z_score(),
                'Action': self.sig
            }       
            self.logs = pd.concat([self.logs, pd.DataFrame([new_row])], ignore_index=True)
            print('Selling @ {}'.format(sellprice))
            print("Order Status:", trade.orderStatus.status)

    def plots(self):
        plt.figure()
        plt.plot(self.logs.index,self.logs.loc[:,'Strat'], label = 'Strategy', color = 'green')
        plt.plot(self.logs.index,self.logs.loc[:,'BH'], label = 'Buy & Hold', color = 'orange')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.xticks(rotation = 30)
        plt.legend()
        plt.title("Strategy vs Buy & Hold : {} ".format(self.ticker))
        plt.show()

    def stratstats(self):
        beta = np.cov(self.logs.loc[:,'BH'],self.logs.loc[:,'Strat'])/np.var(self.logs.loc[:,'BH'])
        beta = beta[0,1]
        pctg = (self.logs.iloc[-1,1] - self.logs.iloc[0,1])/self.logs.iloc[0,1]
        bhpct = (self.logs.iloc[-1,2] - self.logs.iloc[0,2])/self.logs.iloc[0,2]
        risk_free = .042
        alpha = pctg - (risk_free + beta * (bhpct - risk_free))
        
        text = '\n'.join((
        '                  ',
        'Asset : {}, {}'.format(self.ticker),
        'Trading Periods : {}'.format(len(self.logs)),
        'P&L : ${}'.format((self.logs.iloc[-1,1] - self.logs.iloc[0,1]).round(2)),
        'Growth : {}%'.format(pctg.round(2)),
        'Buy/Hold Growth : {}%'.format(bhpct.round(2)),
        'Beta (asset-relative) : {}'.format(beta.round(2)),
        'Alpha (asset-relative) : {}%'.format(alpha.round(2)),
        '                  '
        ))

        return text, self.logs
    
    def run(self):
        try:
            while True:
                self.data_collection()
                self.mean_stdev()
                self.signal_exe()
        except KeyboardInterrupt:
            print("Exiting gracefully. Closing open positions...")
            self.CTRLC()
        finally:
            x = self.stratstats
            print(x[0],x[1])
            self.plots()