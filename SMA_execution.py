import SMA_functions as SMA_functions
import yfinance as yf

# terminal func to run while in clamshell, ensure amphetaime is on

# macair
# caffeinate -i python3 "{filepath}"

# macmini
# caffeinate -i python3 ""{filepath}""

#x = SMA.SMA_backtest('TSLA',4,2025,'ov')
# (TSLA,9)

x = SMA_functions.SMA_tradingfunc('SPY',4,'mr')
print()
print(x[0]) # dataframe contains time-series data containing algorithmic actions, buy/hold quotes, and strategy values
print(x[1]) # trading stats  (alpha and beta are asset-relative, not marked to overall market)
