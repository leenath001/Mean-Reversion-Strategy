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
        self.alo = alo
        self.position = 0
        self.api_key="PKYOJZNEMFQPBCSGY3MC"
        self.secret_key="cVPzOWmEz4bXrbUlm139qLQJwVaYnKuAYBdjDhcM"
        start = self.getsnap()
        self.maslog = {
            'Time' : [],
            'Strat' : [],
            'BH' : [],
            'Zsc' : [],
            'Action' : []      
            }
        self.logs(start,start,0,'NA')
        
    # logging method
    def logs(self,strat,bh,signal,action):
        
        self.maslog['Time'].append(datetime.now())
        self.maslog['Strat'].append(strat)
        self.maslog['BH'].append(bh)
        self.maslog['Zsc'].append(signal)
        self.maslog['Action'].append(action)

    # data collection
    def data_collection(self):

        client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
        )

        start = (datetime.now(timezone.utc) - timedelta(minutes=self.window + 1))
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
        data = bars.df.iloc[:,:4]
    
        # calculate rolling mean and stdev
        data['MA'] = data['close'].rolling(self.window).mean().shift(1).round(2)
        data['SDev'] = data['close'].rolling(self.window).std().shift(1).round(2)

        # storing rolling m/sd
        self.MA = data['MA'].iloc[-1]
        self.sd = data['SDev'].iloc[-1]

    def getsnap(self):
        BASE_URL = 'https://paper-api.alpaca.markets/v2' 
        api = tradeapi.REST(self.api_key, self.secret_key, BASE_URL, api_version='v2')
        quote = api.get_latest_quotes(self.ticker)
        return quote[self.ticker].ap
    
    # calc z score
    def z_score(self):
        self.xi = self.getsnap()
        self.zsc = (self.xi - self.MA) / self.sd
        return self.zsc

    # ID trading signal/execution
    def signal_exe(self):
        self.z = self.z_score()
        if self.z <= -1 and self.position == 0: #buy
            self.sig = 'BUY'
            self.BUY()
        
        elif self.z < 0 and self.position == 1: # hold
            self.sig = 'HOLD'
            self.HOLD()

        elif self.z >= 0 and self.position == 1: #sell 
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
        self.buyprice = self.xi
        self.logs(self.buyprice,self.buyprice,self.z,self.sig)
        print('Buying @ {}'.format(self.buyprice))
        print("Order Status:", self.trade.orderStatus.status)
        time.sleep(6)

    def SELL(self):
        self.executor()
        if self.maslog['Action'][-1] == 'BUY':
            sellprice = self.maslog['Strat'][-1] * self.xi/self.buyprice
        elif self.maslog['Action'][-1] == 'HOLD':
            sellprice = self.maslog['Strat'][-1] * self.xi/self.newhold
        self.logs(sellprice,self.xi,self.z,self.sig)
        print('Selling @ {}'.format(self.xi))
        print("Order Status:", self.trade.orderStatus.status)
        time.sleep(30)
        
    def HOLD(self):
        if self.maslog['Action'][-1] == 'BUY':
            holdprice = self.maslog['Strat'][-1] * self.xi/self.buyprice
            self.newhold = self.xi
        elif self.maslog['Action'][-1] == 'HOLD':
            holdprice = self.maslog['Strat'][-1] * self.xi/self.newhold
            self.newhold = self.xi
        self.logs(holdprice,self.xi,self.z,self.sig)
        print('Holding @ {}'.format(self.newhold))
        time.sleep(6)
        
    def NONE(self):
        self.logs(self.maslog['Strat'][-1],self.xi,self.z,self.sig)
        print('No Action')
        time.sleep(30)

    def CTRLC(self):
        if self.position == 1: 
            contract = Stock(self.ticker,'SMART','USD')
            order = MarketOrder('SELL',self.alo)
            trade = self.ib.placeOrder(contract,order)
            if self.maslog['Action'][-1] == 'BUY':
                sellprice = self.maslog['Strat'][-1] * self.xi/self.buyprice
            elif self.maslog['Action'][-1] == 'HOLD':
                sellprice = self.maslog['Strat'][-1] * self.xi/self.newhold
            self.logs(sellprice,self.xi,self.z,self.sig)
            print('Selling @ {}'.format(self.xi))
            print("Order Status:", trade.orderStatus.status)

    def plots(self):
        self.maslog = pd.DataFrame(self.maslog).set_index('Time')
        plt.figure()
        plt.plot(self.maslog.index,self.maslog.loc[:,'Strat'], label = 'Strategy', color = 'green')
        plt.plot(self.maslog.index,self.maslog.loc[:,'BH'], label = 'Buy & Hold', color = 'orange')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.xticks(rotation = 30)
        plt.legend()
        plt.title("Strategy vs Buy & Hold : {} ".format(self.ticker))
        plt.show()

    def stratstats(self):
        beta = np.cov(self.maslog.loc[:,'BH'],self.maslog.loc[:,'Strat'])/np.var(self.maslog.loc[:,'BH'])
        beta = beta[0,1]
        pctg = (self.maslog.iloc[-1,1] - self.maslog.iloc[0,1])/self.maslog.iloc[0,1]
        bhpct = (self.maslog.iloc[-1,2] - self.maslog.iloc[0,2])/self.maslog.iloc[0,2]
        risk_free = .042
        alpha = pctg - (risk_free + beta * (bhpct - risk_free))
        
        text = '\n'.join((
        '                  ',
        'Asset : {}, {}'.format(self.ticker),
        'Trading Periods : {}'.format(len(self.maslog)),
        'P&L : ${}'.format((self.maslog.iloc[-1,1] - self.maslog.iloc[0,1]).round(2)),
        'Growth : {}%'.format(pctg.round(2)),
        'Buy/Hold Growth : {}%'.format(bhpct.round(2)),
        'Beta (asset-relative) : {}'.format(beta.round(2)),
        'Alpha (asset-relative) : {}%'.format(alpha.round(2)),
        '                  '
        ))

        return text, self.maslog
    
    # TRADING LOGIC #
    def run(self):
        try:
            while True:
                self.data_collection()
                self.signal_exe()
        except KeyboardInterrupt:
            print("Exiting gracefully. Closing open positions...")
            self.CTRLC()
        finally:
            x = self.stratstats()
            print(x[0],x[1])
            self.plots()
