# Moving-Average-Strategy
Functions for employing and implementing Moving Average trading strategy. 

Goal : Strategy aims to profit from an asset reverting to it's mean. See type below for different implementations 
*  To run tradingfuncs, create an interactive brokers account and download IB Gateway (API must be simultaneously running alongside the function inside a terminal). 
*  To run autonomously, download 'Amphetamine' (mac) on app store. Also, employ caffeinate -i python3 '{filepath of execution files}' to run within terminal. Processes will run in the background while laptop/computer is inactive/closed. Trading functions run until Ctrl + C is used.

To change timeframe, see line 178 (tradingfunc) and line 42 (backtest). Allowed parameters for period and interval are included below. 

INVERVAL PARAMETERS ('period', interaval)
*  "1m" Max 7 days, only for recent data
*  "2m" Max 60 days
*  "5m" Max 60 days
*  "15m" Max 60 days
*  "30m" Max 60 days
*  "60m" Max 730 days (~2 years)
*  "90m" Max 60 days
*  "1d"

## SMA_funcs.SMA_backtest(ticker,window,year,type)
*  type :'mr' => mean reversion strat, aims to capture a securities movement back towards mean
*  type :'ov' => overvaluation capture strat, aims to capture valuation above mean. Works better with shorter dated window 
*  window gives period for rolling average to be calculated, year calls period of data wanted for backtest
*  Buy condition: Buy first instance of SMA < equity price. Hold for all other instances following.
*  Sell condition: Sell first instance of SMA > equity price. Do nothing for all other instances following.

## SMA_funcs.SMA_tradingfunc(ticker,window,type)
*  function for employing SMA strategy using interactive brokers (IB) gateway
*  'mr' => mean reversion strat, aims to capture a securities movement back towards mean
*  'ov' => overvaluation capture strat, aims to capture valuation above mean. Works better with shorter dated window 
*  window gives period for rolling average to be calculated
*  can change interval through which function operates (eg. 1min or 1day, see lines 31-40, 159)
*  function runs a while True loop. end with Ctrl + c
